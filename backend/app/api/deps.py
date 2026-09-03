import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_supabase_jwt
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.services.api_key_service import hash_key

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Missing or invalid authorization header.",
            },
        )
    token = authorization.split(" ", 1)[1]
    payload = verify_supabase_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Token missing user identity."},
        )
    result = await db.execute(
        text("SELECT * FROM users WHERE id = :uid AND deleted_at IS NULL"),
        {"uid": user_id},
    )
    row = result.mappings().first()
    if not row:
        logger.warning(
            "get_current_user: user %s not found in DB — inserting fallback row. "
            "This indicates the Supabase auth trigger may not be firing.",
            user_id,
        )
        email = payload.get("email", "")
        full_name = (
            payload.get("user_metadata", {}).get("full_name")
            or payload.get("user_metadata", {}).get("name")
        )
        avatar_url = (
            payload.get("user_metadata", {}).get("avatar_url")
            or payload.get("user_metadata", {}).get("picture")
        )
        auth_provider = "google" if payload.get("app_metadata", {}).get("provider") == "google" else "email"

        await db.execute(
            text("""
                INSERT INTO users (id, email, full_name, avatar_url, auth_provider, tier)
                VALUES (:uid, :email, :full_name, :avatar_url, :auth_provider, 'free')
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "uid": user_id,
                "email": email,
                "full_name": full_name,
                "avatar_url": avatar_url,
                "auth_provider": auth_provider,
            },
        )
        await db.commit()

        result = await db.execute(
            text("SELECT * FROM users WHERE id = :uid AND deleted_at IS NULL"),
            {"uid": user_id},
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(
                status_code=401,
                detail={"code": "USER_NOT_FOUND", "message": "User not found."},
            )

    # Self-healing tier expiry: if pro/agency tier has passed its tier_expires_at,
    # downgrade to free immediately (safety net if downgrade webhook was delayed/dropped
    # or used US spelling). This is Option A from Phase 2 P0 — enforcement-layer, per-request,
    # not a cron sweep. Writes the correction to DB so future requests need no re-check.
    tier_val = (row.get("tier") or "free").lower()
    expires_at_val = row.get("tier_expires_at")
    if tier_val in ("pro", "agency") and expires_at_val is not None:
        try:
            now_utc = datetime.now(timezone.utc)
            exp = expires_at_val
            if getattr(exp, "tzinfo", None) is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now_utc:
                logger.info(
                    "get_current_user: auto-downgrading expired tier for user %s from %s (expired %s, now %s)",
                    user_id,
                    tier_val,
                    exp.isoformat(),
                    now_utc.isoformat(),
                )
                await db.execute(
                    text(
                        "UPDATE users SET tier = 'free', tier_expires_at = NULL, dodo_subscription_id = NULL, updated_at = NOW() WHERE id = :uid"
                    ),
                    {"uid": user_id},
                )
                await db.commit()
                # Reflect downgrade in the in-memory row so the returned User is already 'free'
                # RowMapping is immutable — build a mutable copy
                row = dict(row)
                row["tier"] = "free"
                row["tier_expires_at"] = None
                row["dodo_subscription_id"] = None
        except Exception as e:
            logger.warning("get_current_user: expiry self-heal failed for %s: %s", user_id, e)

    user = User()
    for key, value in row.items():
        setattr(user, key, value)
    return user


async def get_api_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    raw_key = request.headers.get("X-API-Key")
    if not raw_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Pass X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    if not raw_key.startswith("nax_") or len(raw_key) != 36:
        raise HTTPException(status_code=401, detail="Invalid API key format.")

    key_hash_val = hash_key(raw_key)

    result = await db.execute(
        text("""
            SELECT ak.id, ak.user_id, ak.revoked_at, u.tier
            FROM api_keys ak
            JOIN users u ON u.id = ak.user_id
            WHERE ak.key_hash = :hash
        """),
        {"hash": key_hash_val},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    if row["revoked_at"] is not None:
        raise HTTPException(status_code=401, detail="API key has been revoked.")

    # Defer tier check until after self-heal — tier_expires_at lives on users, not api_keys
    # (row["tier"] from the join may be stale if expired).
    try:
        await db.execute(
            text("UPDATE api_keys SET last_used_at = NOW() WHERE id = :id"),
            {"id": row["id"]},
        )
        await db.commit()
    except Exception:
        pass

    user_result = await db.execute(
        text("SELECT * FROM users WHERE id = :uid AND deleted_at IS NULL"),
        {"uid": row["user_id"]},
    )
    user_row = user_result.mappings().first()
    if not user_row:
        raise HTTPException(status_code=401, detail="User not found.")

    # Self-healing expiry for API path (mirrors get_current_user Option A)
    user_tier = (user_row.get("tier") or "free").lower()
    exp_val = user_row.get("tier_expires_at")
    if user_tier in ("pro", "agency") and exp_val is not None:
        try:
            now_utc = datetime.now(timezone.utc)
            exp2 = exp_val
            if getattr(exp2, "tzinfo", None) is None:
                exp2 = exp2.replace(tzinfo=timezone.utc)
            if exp2 < now_utc:
                logger.info(
                    "get_api_user: auto-downgrading expired tier for user %s from %s (expired %s)",
                    row["user_id"],
                    user_tier,
                    exp2.isoformat(),
                )
                await db.execute(
                    text("UPDATE users SET tier = 'free', tier_expires_at = NULL, dodo_subscription_id = NULL, updated_at = NOW() WHERE id = :uid"),
                    {"uid": row["user_id"]},
                )
                await db.commit()
                user_row = dict(user_row)
                user_row["tier"] = "free"
                user_row["tier_expires_at"] = None
                user_row["dodo_subscription_id"] = None
                user_tier = "free"
        except Exception as e:
            logger.warning("get_api_user: expiry self-heal failed for %s: %s", row["user_id"], e)
            user_tier = (user_row.get("tier") or "free").lower()

    if user_tier != "agency":
        raise HTTPException(status_code=403, detail="API access requires Agency plan.")

    from app.services.report_service import _make_user_proxy
    return _make_user_proxy(dict(user_row))


async def check_report_limit(current_user: User = Depends(get_current_user)) -> None:
    if current_user.tier == "free":
        if current_user.reports_this_month >= 3:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "MONTHLY_LIMIT_REACHED",
                    "message": "You've used all 3 free reports this month.",
                    "upgrade_url": f"{settings.FRONTEND_BASE_URL}/pricing",
                },
            )


def _check_tier(user: User, allowed_tiers: set, required: str) -> User:
    user_tier = (getattr(user, 'tier', None) or 'free').lower()
    if user_tier not in allowed_tiers:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "UPGRADE_REQUIRED",
                "message": f"This feature requires a {required.title()} plan.",
                "current_tier": user_tier,
                "required_tier": required,
            }
        )
    return user


def require_pro_or_above(current_user: User = Depends(get_current_user)) -> User:
    return _check_tier(current_user, {'pro', 'agency'}, 'pro')


def require_agency(current_user: User = Depends(get_current_user)) -> User:
    return _check_tier(current_user, {'agency'}, 'agency')


def require_byok(current_user: User = Depends(get_current_user)) -> User:
    return current_user


async def increment_report_count(user_id: str, db: AsyncSession) -> None:
    await db.execute(
        text("UPDATE users SET reports_this_month = reports_this_month + 1 WHERE id = :uid"),
        {"uid": user_id},
    )
    await db.commit()


async def mark_upload_used(upload_id: str, db: AsyncSession) -> None:
    await db.execute(
        text("UPDATE uploads SET used = TRUE WHERE id = :uid"),
        {"uid": upload_id},
    )
    await db.commit()


async def reset_monthly_usage(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        text(
            "UPDATE users SET reports_this_month = 0, "
            "usage_reset_at = date_trunc('month', NOW() + interval '1 month') "
            "WHERE usage_reset_at <= :now"
        ),
        {"now": now},
    )
    await db.commit()
