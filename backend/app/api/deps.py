import logging
from datetime import datetime

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


async def check_pro_tier(current_user: User = Depends(get_current_user)) -> None:
    if current_user.tier not in ("pro", "agency"):
        raise HTTPException(
            status_code=402,
            detail={
                "code": "PRO_REQUIRED",
                "message": "This feature requires a Pro subscription.",
                "upgrade_url": f"{settings.FRONTEND_BASE_URL}/pricing",
            },
        )


async def check_agency_tier(current_user: User = Depends(get_current_user)) -> None:
    if current_user.tier != "agency":
        raise HTTPException(
            status_code=402,
            detail={
                "code": "AGENCY_REQUIRED",
                "message": "This feature requires an Agency subscription.",
                "upgrade_url": f"{settings.FRONTEND_BASE_URL}/pricing",
            },
        )


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
    now = datetime.utcnow()
    await db.execute(
        text(
            "UPDATE users SET reports_this_month = 0, "
            "usage_reset_at = date_trunc('month', NOW() + interval '1 month') "
            "WHERE usage_reset_at <= :now"
        ),
        {"now": now},
    )
    await db.commit()
