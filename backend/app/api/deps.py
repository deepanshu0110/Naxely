import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Header
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_supabase_jwt
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User

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

    user = User()
    for key, value in row.items():
        setattr(user, key, value)
    return user


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
    user_tier = (getattr(current_user, 'tier', None) or 'free').lower()
    has_key = bool(
        getattr(current_user, 'encrypted_api_key', None) and
        getattr(current_user, 'api_key_iv', None)
    )
    if user_tier == 'free' and has_key:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "UPGRADE_REQUIRED",
                "message": "BYOK API keys require a Pro or Agency plan.",
                "current_tier": user_tier,
            }
        )
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
