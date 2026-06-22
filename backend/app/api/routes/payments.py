import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from standardwebhooks import Webhook as _Webhook
from dodopayments import AsyncDodoPayments, APIStatusError

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.services.email_service import send_email
from app.models.user import User
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

dodo = AsyncDodoPayments(
    bearer_token=settings.DODO_API_KEY,
    environment=settings.DODO_ENVIRONMENT,
)


PLANS_DATA = [
    {
        "id": "free",
        "name": "Free",
        "price_monthly": 0,
        "features": ["3 reports/month", "CSV upload", "Basic charts", "PDF with watermark"],
    },
    {
        "id": "pro",
        "name": "Pro",
        "price_monthly": 29,
        "dodo_product_id": settings.DODO_PRO_PRODUCT_ID,
        "features": ["Unlimited reports", "AI insights", "Custom branding", "Google Sheets", "No watermark"],
    },
    {
        "id": "agency",
        "name": "Agency",
        "price_monthly": 79,
        "dodo_product_id": settings.DODO_AGENCY_PRODUCT_ID,
        "features": ["Everything in Pro", "White-label", "Dedicated support"],
    },
]


_DOWNGRADE_EVENTS = frozenset({
    "subscription.cancelled",
    "subscription.failed",
    "subscription.expired",
    "refund.succeeded",
    "dispute.opened",
    "dispute.lost",
    "dispute.accepted",
    "dispute.expired",
})



class CheckoutRequest(BaseModel):
    plan: Literal["pro", "agency"]


class DowngradeRequest(BaseModel):
    plan: Literal["pro", "free"]


def _dodo_error_to_http(e: APIStatusError) -> HTTPException:
    body = e.body if isinstance(e.body, dict) else {}
    code = body.get("code")
    message = body.get("message", "") or e.message
    http_status = {400: 400, 401: 401, 403: 403, 404: 404,
                   409: 400, 422: 400, 429: 429, 500: 502}.get(e.status_code, 502)
    detail: Dict[str, Any] = {"message": message or "Dodo Payments API error"}
    if code:
        detail["code"] = code
    return HTTPException(status_code=http_status, detail=detail)


@router.get("/plans")
async def get_plans() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "plans": PLANS_DATA,
        },
    }


@router.post("/checkout")
@limiter.limit("10/minute")
async def create_checkout_session(
    request: Request,
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    if body.plan == "pro":
        product_id = settings.DODO_PRO_PRODUCT_ID
        new_tier = "pro"
    elif body.plan == "agency":
        product_id = settings.DODO_AGENCY_PRODUCT_ID
        new_tier = "agency"
    else:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if not product_id:
        raise HTTPException(status_code=500, detail="Product not configured")

    # Existing subscriber — change plan in-place instead of creating a new checkout
    if current_user.dodo_subscription_id:
        # Subscription on hold (tier='free' but sub_id survived the hold)
        if current_user.tier == "free":
            # Route to Customer Portal if we have a customer reference
            if current_user.dodo_customer_id:
                try:
                    session = await dodo.customers.customer_portal.create(
                        customer_id=current_user.dodo_customer_id,
                        return_url=f"{settings.FRONTEND_BASE_URL}/settings?tab=billing",
                    )
                except Exception as e:
                    logger.error("Dodo customer portal error: %s", e)
                    raise HTTPException(status_code=502, detail="Failed to create customer portal session")
                return {"checkout_url": session.link}
            # No customer reference — log and fall through to new checkout below
            logger.warning(
                "On-hold user %s has no dodo_customer_id; creating new checkout session",
                current_user.id,
            )
        else:
            if current_user.tier == new_tier:
                raise HTTPException(status_code=400, detail="Already subscribed to this plan")

            try:
                await dodo.subscriptions.change_plan(
                    subscription_id=current_user.dodo_subscription_id,
                    product_id=product_id,
                    proration_billing_mode="prorated_immediately",
                    quantity=1,
                )
            except Exception as e:
                logger.error("Dodo change plan error: %s", e)
                raise HTTPException(status_code=502, detail="Failed to change plan")

            return {"checkout_url": ""}

    try:
        session = await dodo.checkout_sessions.create(
            product_cart=[{"product_id": product_id, "quantity": 1}],
            customer={"email": current_user.email, "name": current_user.full_name},
            metadata={"user_id": str(current_user.id)},
            return_url=f"{settings.FRONTEND_BASE_URL}/settings?tab=billing&checkout=complete",
        )
    except Exception as e:
        logger.error("Dodo checkout error: %s", e)
        raise HTTPException(status_code=502, detail="Failed to create checkout session")

    return {"checkout_url": session.checkout_url}


@router.post("/webhook")
@limiter.limit("20/minute")
async def dodo_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    body = await request.body()

    try:
        _Webhook(settings.DODO_WEBHOOK_SECRET).verify(
            body,
            {
                "webhook-id": request.headers.get("webhook-id", ""),
                "webhook-signature": request.headers.get("webhook-signature", ""),
                "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
            },
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = request.headers.get("webhook-id", "")
    if not event_id:
        raise HTTPException(status_code=400, detail="Missing webhook-id header")

    existing = await db.execute(
        text("SELECT id FROM payment_events WHERE dodo_event_id = :eid"),
        {"eid": str(event_id)},
    )
    if existing.mappings().first():
        return {"success": True, "data": {"status": "already_processed"}}

    event_type = payload.get("type", payload.get("event_type", ""))

    # Primary: metadata.user_id from our own checkout creation (may be under data or top-level)
    user_id = (
        ((payload.get("data") or {}).get("metadata") or {}).get("user_id")
        or (payload.get("metadata") or {}).get("user_id")
    )
    # Fallback: lookup by dodo_customer_id for dashboard-originated events
    if not user_id:
        dodo_customer_id = payload.get("customer_id") or (payload.get("data") or {}).get("customer_id")
        if dodo_customer_id:
            result = await db.execute(
                text("SELECT id FROM users WHERE dodo_customer_id = :dci"),
                {"dci": dodo_customer_id},
            )
            row = result.mappings().first()
            if row:
                user_id = str(row["id"])
    subscription_id = payload.get("subscription_id", (payload.get("data") or {}).get("subscription_id"))
    expires_at_raw = (
        payload.get("expires_at")
        or (payload.get("data") or {}).get("next_billing_date")
        or (payload.get("data") or {}).get("expires_at")
        or payload.get("current_period_end")
    )
    expires_at: datetime | None = None
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            expires_at = None

    product_id = payload.get("product_id") or (payload.get("data") or {}).get("product_id", "")
    if product_id == settings.DODO_PRO_PRODUCT_ID:
        new_tier = "pro"
    elif product_id == settings.DODO_AGENCY_PRODUCT_ID:
        new_tier = "agency"
    else:
        new_tier = (
            (payload.get("data") or {}).get("metadata", {}).get("tier")
            or (payload.get("metadata") or {}).get("tier", "pro")
        )

    try:
        await db.execute(
            text("""
                INSERT INTO payment_events (id, user_id, event_type, dodo_event_id, payload, processed, created_at)
                VALUES (gen_random_uuid(), :user_id, :event_type, :dodo_event_id, :payload, TRUE, NOW())
            """),
            {
                "user_id": user_id,
                "event_type": event_type,
                "dodo_event_id": str(event_id),
                "payload": json.dumps(payload),
            },
        )
    except IntegrityError:
        await db.rollback()
        logger.warning("Duplicate dodo_event_id %s — returning already_processed", event_id)
        return {"success": True, "data": {"status": "already_processed"}}

    if event_type in ("subscription.created", "subscription.renewed", "subscription.active", "subscription.plan_changed", "dunning.recovered"):
        if not user_id:
            await db.commit()
            return {"success": True, "data": {"status": "processed"}}

        updates = ["tier = :tier", "updated_at = NOW()"]
        params: Dict[str, Any] = {"uid": user_id, "tier": new_tier}

        if expires_at:
            updates.append("tier_expires_at = :expires_at")
            params["expires_at"] = expires_at
        if subscription_id:
            updates.append("dodo_subscription_id = :sub_id")
            params["sub_id"] = str(subscription_id)

        await db.execute(
            text(f"UPDATE users SET {', '.join(updates)} WHERE id = :uid"),
            params,
        )

        # Capture Dodo's customer_id for future fallback lookups
        dodo_customer_id = payload.get("customer_id") or (payload.get("data") or {}).get("customer_id")
        if dodo_customer_id:
            await db.execute(
                text("UPDATE users SET dodo_customer_id = :dci, updated_at = NOW() WHERE id = :uid AND dodo_customer_id IS NULL"),
                {"dci": dodo_customer_id, "uid": user_id},
            )

    elif event_type == "subscription.on_hold":
        if user_id:
            await db.execute(
                text("UPDATE users SET tier = 'free', tier_expires_at = NULL, updated_at = NOW() WHERE id = :uid"),
                {"uid": user_id},
            )

    elif event_type in _DOWNGRADE_EVENTS:
        if user_id:
            await db.execute(
                text("UPDATE users SET tier = 'free', tier_expires_at = NULL, dodo_subscription_id = NULL, updated_at = NOW() WHERE id = :uid"),
                {"uid": user_id},
            )

    elif event_type == "payment.failed":
        if user_id:
            result = await db.execute(
                text("SELECT email FROM users WHERE id = :uid"),
                {"uid": user_id},
            )
            row = result.mappings().first()
            if row and settings.RESEND_API_KEY:
                send_email(
                    to=row["email"],
                    subject="Payment failed — Naxely",
                    html=(
                        "<p>Your most recent payment for Naxely failed.</p>"
                        "<p>Please update your billing information at "
                        f"<a href='{settings.FRONTEND_BASE_URL}/settings/billing'>"
                        f"{settings.FRONTEND_BASE_URL}/settings/billing</a> "
                        "to avoid any disruption to your subscription.</p>"
                    ),
                )

    await db.commit()
    return {"success": True, "data": {"status": "processed"}}


@router.post("/downgrade")
@limiter.limit("10/minute")
async def downgrade_subscription(
    request: Request,
    body: DowngradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if not current_user.dodo_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    if current_user.tier == "free":
        raise HTTPException(status_code=400, detail="No active paid subscription to downgrade")

    # Pre-check: fetch current subscription state for pending changes
    try:
        sub = await dodo.subscriptions.retrieve(
            subscription_id=current_user.dodo_subscription_id,
        )
    except APIStatusError as e:
        raise _dodo_error_to_http(e)
    except Exception as e:
        logger.error("Failed to retrieve subscription: %s", e)
        raise HTTPException(status_code=502, detail="Failed to verify subscription state")

    if sub.scheduled_change:
        effective = sub.scheduled_change.effective_at
        date_str = f"{effective.strftime('%B')} {effective.day}, {effective.year}" if hasattr(effective, 'strftime') else str(effective)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "PENDING_SCHEDULED_CHANGE",
                "message": f"You already have a pending plan change scheduled for {date_str}. Cancel that first before requesting a new change.",
            },
        )

    if sub.cancel_at_next_billing_date:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "PENDING_CANCELLATION",
                "message": "Your subscription is already scheduled for cancellation at the next billing date. Cancel that first before requesting a new change.",
            },
        )

    if body.plan == "free":
        try:
            await dodo.subscriptions.update(
                subscription_id=current_user.dodo_subscription_id,
                cancel_at_next_billing_date=True,
            )
        except APIStatusError as e:
            raise _dodo_error_to_http(e)
        except Exception as e:
            logger.error("Failed to schedule downgrade to free: %s", e)
            raise HTTPException(status_code=502, detail="Failed to schedule downgrade")

        result = await db.execute(
            text("SELECT tier_expires_at FROM users WHERE id = :uid"),
            {"uid": str(current_user.id)},
        )
        row = result.mappings().first()
        effective_date = row["tier_expires_at"] if row and row.get("tier_expires_at") else datetime.now(timezone.utc)
        month_name = f"{effective_date.strftime('%B')} {effective_date.day}, {effective_date.year}" if hasattr(effective_date, "strftime") else str(effective_date)

        return {
            "success": True,
            "data": {
                "planned_tier": "free",
                "effective_date": effective_date.isoformat() + "Z",
                "message": f"Your {current_user.tier.capitalize()} access continues until {month_name}. After that, you'll move to the Free plan.",
            },
        }

    if body.plan == "pro":
        if current_user.tier != "agency":
            raise HTTPException(status_code=400, detail="You are not subscribed to the Agency plan")

        product_id = settings.DODO_PRO_PRODUCT_ID
        if not product_id:
            raise HTTPException(status_code=500, detail="Pro product not configured")

        try:
            await dodo.subscriptions.change_plan(
                subscription_id=current_user.dodo_subscription_id,
                product_id=product_id,
                quantity=1,
                proration_billing_mode="full_immediately",
                effective_at="next_billing_date",
            )
        except APIStatusError as e:
            raise _dodo_error_to_http(e)
        except Exception as e:
            logger.error("Dodo downgrade error: %s", e)
            raise HTTPException(status_code=502, detail="Failed to schedule downgrade")

        try:
            sub = await dodo.subscriptions.retrieve(
                subscription_id=current_user.dodo_subscription_id,
            )
        except Exception as e:
            logger.error("Failed to retrieve subscription after downgrade: %s", e)
            raise HTTPException(status_code=502, detail="Downgrade scheduled but failed to confirm date")

        effective_date = sub.next_billing_date
        scheduled_change_id = sub.scheduled_change.id if sub.scheduled_change else None
        month_name = f"{effective_date.strftime('%B')} {effective_date.day}, {effective_date.year}" if hasattr(effective_date, "strftime") else str(effective_date)

        return {
            "success": True,
            "data": {
                "planned_tier": "pro",
                "effective_date": effective_date.isoformat() + "Z",
                "scheduled_change_id": scheduled_change_id,
                "message": f"You'll move to Pro starting {month_name}",
            },
        }

    raise HTTPException(status_code=400, detail="Invalid plan")


@router.get("/subscription")
async def get_subscription_state(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    if not current_user.dodo_subscription_id:
        return {"success": True, "data": {"has_subscription": False}}

    try:
        sub = await dodo.subscriptions.retrieve(
            subscription_id=current_user.dodo_subscription_id,
        )
    except Exception as e:
        logger.error("Failed to retrieve subscription: %s", e)
        raise HTTPException(status_code=502, detail="Failed to retrieve subscription state")

    scheduled = None
    if sub.scheduled_change:
        target_tier = "pro" if sub.scheduled_change.product_id == settings.DODO_PRO_PRODUCT_ID else "agency"
        scheduled = {
            "id": sub.scheduled_change.id,
            "product_id": sub.scheduled_change.product_id,
            "planned_tier": target_tier,
            "effective_at": sub.scheduled_change.effective_at.isoformat() + "Z",
        }

    return {
        "success": True,
        "data": {
            "has_subscription": True,
            "subscription_id": sub.subscription_id,
            "status": sub.status,
            "next_billing_date": sub.next_billing_date.isoformat() + "Z" if sub.next_billing_date else None,
            "cancel_at_next_billing_date": sub.cancel_at_next_billing_date,
            "scheduled_change": scheduled,
        },
    }


@router.post("/cancel-scheduled-change")
async def cancel_scheduled_change(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    if not current_user.dodo_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    try:
        sub = await dodo.subscriptions.retrieve(
            subscription_id=current_user.dodo_subscription_id,
        )
    except Exception as e:
        logger.error("Failed to retrieve subscription: %s", e)
        raise HTTPException(status_code=502, detail="Failed to check subscription state")

    if sub.scheduled_change:
        try:
            await dodo.subscriptions.cancel_change_plan(
                subscription_id=current_user.dodo_subscription_id,
            )
        except Exception as e:
            logger.error("Failed to cancel scheduled change: %s", e)
            raise HTTPException(status_code=502, detail="Failed to cancel scheduled downgrade")

        return {"success": True, "data": {"cancelled": True, "type": "plan_change"}}

    if sub.cancel_at_next_billing_date:
        try:
            await dodo.subscriptions.update(
                subscription_id=current_user.dodo_subscription_id,
                cancel_at_next_billing_date=False,
            )
        except Exception as e:
            logger.error("Failed to unschedule cancellation: %s", e)
            raise HTTPException(status_code=502, detail="Failed to cancel scheduled downgrade")

        return {"success": True, "data": {"cancelled": True, "type": "cancellation"}}

    raise HTTPException(status_code=400, detail="No scheduled change found")


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if not current_user.dodo_subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found",
        )

    try:
        await dodo.subscriptions.update(
            subscription_id=current_user.dodo_subscription_id,
            cancel_at_next_billing_date=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to cancel subscription with Dodo: {str(e)}",
        )

    result = await db.execute(
        text("SELECT tier_expires_at FROM users WHERE id = :uid"),
        {"uid": str(current_user.id)},
    )
    row = result.mappings().first()
    access_until = row["tier_expires_at"] if row and row.get("tier_expires_at") else datetime.now(timezone.utc)

    access_until_str = access_until.isoformat() + "Z"
    month_name = f"{access_until.strftime('%B')} {access_until.day}, {access_until.year}" if hasattr(access_until, "strftime") else str(access_until)

    return {
        "success": True,
        "data": {
            "cancelled": True,
            "access_until": access_until_str,
            "message": f"Your {current_user.tier.capitalize()} access continues until {month_name}",
        },
    }
