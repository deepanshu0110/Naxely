import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

# Resend uses Svix/Standard Webhooks: headers svix-id, svix-timestamp, svix-signature
# (also sent as webhook-id etc for compatibility). We verify via standardwebhooks.
# Live-fetch verified: Resend docs reference Svix webhook verification; standardwebhooks
# library implements the same HMAC-SHA256 verification as Svix.

BOUNCE_TYPES = {"email.bounced", "email.complained"}


def _verify_resend_signature(body: bytes, request: Request) -> None:
    if not settings.RESEND_WEBHOOK_SECRET:
        logger.warning("RESEND_WEBHOOK_SECRET not set — skipping signature verification")
        return
    # Resend sends svix-* headers; standardwebhooks expects webhook-*.
    # The library actually checks for both prefixes; we pass both to be safe.
    headers = {
        "webhook-id": request.headers.get("svix-id") or request.headers.get("webhook-id", ""),
        "webhook-timestamp": request.headers.get("svix-timestamp") or request.headers.get("webhook-timestamp", ""),
        "webhook-signature": request.headers.get("svix-signature") or request.headers.get("webhook-signature", ""),
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }
    # standardwebhooks expects exactly webhook-* keys
    verify_headers = {
        "webhook-id": headers["webhook-id"],
        "webhook-timestamp": headers["webhook-timestamp"],
        "webhook-signature": headers["webhook-signature"],
    }
    if not verify_headers["webhook-id"] or not verify_headers["webhook-signature"]:
        raise HTTPException(status_code=400, detail="Missing webhook signature headers")
    try:
        from standardwebhooks import Webhook as _Webhook
        _Webhook(settings.RESEND_WEBHOOK_SECRET).verify(body, verify_headers)
    except Exception as e:
        logger.warning("Resend webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


@router.post("/internal/webhooks/resend")
@limiter.limit("20/minute")
async def resend_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    body = await request.body()
    _verify_resend_signature(body, request)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("type", "")
    data = payload.get("data") or {}
    # Resend event examples: type=email.bounced, data.email_id=uuid, data.to=[email]
    resend_id = data.get("email_id") or data.get("id") or payload.get("email_id")

    logger.info("Resend webhook received type=%s resend_id=%s", event_type, resend_id)

    if event_type in BOUNCE_TYPES:
        # For email.bounced, distinguish hard (Permanent) vs soft (Temporary) — only hard bounces
        # indicate a permanently invalid address and should suppress future sends. Soft bounces
        # (Temporary, e.g. mailbox full, transient DNS) may recover, so we log but do not suppress.
        # If bounce object is missing (as in some tests), treat as hard to be safe and preserve
        # backward compatibility with existing tests that send minimal bounced payloads.
        if event_type == "email.bounced":
            bounce = data.get("bounce") or {}
            bounce_type = str(bounce.get("type", "")).lower()
            # Only Temporary is explicitly soft; missing/empty or Permanent is treated as hard
            if bounce_type == "temporary":
                logger.info("Ignoring soft bounce for resend_id=%s type=%s subType=%s — not suppressing", resend_id, bounce.get("type"), bounce.get("subType"))
                # Still update email_log to bounced for tracking, but do not set email_suppressed
                if resend_id:
                    await db.execute(
                        text("UPDATE email_log SET status = :status WHERE resend_id = :rid"),
                        {"status": "bounced", "rid": str(resend_id)},
                    )
                    await db.commit()
                return {"success": True, "data": {"status": "soft_bounced_ignored"}}
        status = "bounced" if event_type == "email.bounced" else "complained"
        if not resend_id:
            # Fallback: try to find user by recipient email and suppress
            to_list = data.get("to") or []
            to_email = to_list[0] if isinstance(to_list, list) and to_list else data.get("email")
            if to_email:
                await db.execute(
                    text("UPDATE users SET email_suppressed = TRUE, updated_at = NOW() WHERE email = :email"),
                    {"email": to_email},
                )
                await db.commit()
                logger.info("Suppressed user by email fallback %s due to %s", to_email, event_type)
            return {"success": True, "data": {"status": "suppressed_by_email_fallback"}}

        # Update email_log status
        result = await db.execute(
            text("SELECT user_id FROM email_log WHERE resend_id = :rid LIMIT 1"),
            {"rid": str(resend_id)},
        )
        row = result.mappings().first()
        if row:
            user_id = str(row["user_id"])
            await db.execute(
                text("UPDATE email_log SET status = :status WHERE resend_id = :rid"),
                {"status": status, "rid": str(resend_id)},
            )
            await db.execute(
                text("UPDATE users SET email_suppressed = TRUE, updated_at = NOW() WHERE id = :uid"),
                {"uid": user_id},
            )
            await db.commit()
            logger.info("Marked %s for resend_id %s, suppressed user %s", status, resend_id, user_id)
            return {"success": True, "data": {"status": status, "user_id": user_id}}
        else:
            # No email_log match — try recipient email fallback
            to_list = data.get("to") or []
            to_email = to_list[0] if isinstance(to_list, list) and to_list else None
            if to_email:
                await db.execute(
                    text("UPDATE users SET email_suppressed = TRUE, updated_at = NOW() WHERE email = :email"),
                    {"email": to_email},
                )
                await db.commit()
                logger.info("Suppressed by email fallback (no email_log) %s due to %s", to_email, event_type)
            return {"success": True, "data": {"status": "suppressed_by_email_fallback_no_log"}}

    # For other events (delivered, opened, etc.) just acknowledge
    return {"success": True, "data": {"status": "ignored", "type": event_type}}
