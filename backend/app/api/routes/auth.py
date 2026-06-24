from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

MONTHLY_LIMITS = {"free": 3, "pro": None, "agency": None}


@router.get("/verify")
async def verify_auth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM users WHERE id = :uid AND deleted_at IS NULL"),
        {"uid": str(current_user.id)},
    )
    row = result.mappings().first()
    if not row:
        return {"id": str(current_user.id), "email": "", "full_name": "", "avatar_url": None, "tier": "free", "tier_expires_at": None, "has_api_key": False, "ai_provider": None, "logo_url": None, "brand_color": "#6366F1", "company_name": None, "reports_this_month": 0, "monthly_limit": 3, "theme_preference": "light", "has_completed_onboarding": False}

    monthly_limit = MONTHLY_LIMITS.get(row.get("tier", "free"), 3)

    return {
        "id": str(row["id"]),
        "email": row["email"],
        "full_name": row.get("full_name"),
        "avatar_url": row.get("avatar_url"),
        "tier": row.get("tier", "free"),
        "tier_expires_at": row["tier_expires_at"].isoformat().replace("+00:00", "Z") if row.get("tier_expires_at") else None,
        "has_api_key": row.get("encrypted_api_key") is not None,
        "ai_provider": row.get("ai_provider"),
        "logo_url": row.get("logo_url"),
        "brand_color": row.get("brand_color", "#6366F1"),
        "company_name": row.get("company_name"),
        "reports_this_month": row.get("reports_this_month", 0),
        "monthly_limit": monthly_limit,
        "theme_preference": row.get("theme_preference", "light"),
        "has_completed_onboarding": row.get("has_completed_onboarding", False),
    }


@router.post("/complete-onboarding")
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await db.execute(
        text("UPDATE users SET has_completed_onboarding = TRUE WHERE id = :uid"),
        {"uid": str(current_user.id)},
    )
    await db.commit()
    return {"success": True}


@router.post("/skip-onboarding")
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await db.execute(
        text("UPDATE users SET has_completed_onboarding = TRUE WHERE id = :uid"),
        {"uid": str(current_user.id)},
    )
    await db.commit()
    return {"success": True}
