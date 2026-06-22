import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, check_pro_tier
from app.core.database import get_db
from app.models.user import User
from app.utils.encryption import get_master_key, encrypt_api_key

logger = logging.getLogger(__name__)

from app.core.supabase_helpers import _get_supabase, _run_sync
from app.core.limiter import limiter
from fastapi import Request as FastAPIRequest
from gotrue.errors import AuthApiError

router = APIRouter()


VALID_KEY_PATTERNS = {
    "openai": r"^sk-[a-zA-Z0-9\-_]{20,}$",
    "claude": r"^sk-ant-[a-zA-Z0-9\-_]{20,}$",
    "gemini": r"^(AIza|AQ\.)[a-zA-Z0-9\-_]{30,}$",
}

ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "svg"}
MAX_LOGO_SIZE = 2 * 1024 * 1024

MONTHLY_LIMITS = {"free": 3, "pro": None, "agency": None}

HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., max_length=255)


class ApiKeyRequest(BaseModel):
    provider: str
    api_key: str = Field(..., max_length=200)


class BrandingUpdateRequest(BaseModel):
    brand_color: Optional[str] = None
    company_name: Optional[str] = None


class ThemeUpdateRequest(BaseModel):
    theme: str = Field(..., pattern=r"^(light|dark)$")


class DeleteAccountRequest(BaseModel):
    email: str


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM users WHERE id = :uid AND deleted_at IS NULL"),
        {"uid": str(current_user.id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    api_key_preview = None
    if row.get("encrypted_api_key"):
        preview_stored = row.get("api_key_preview")
        if preview_stored:
            api_key_preview = preview_stored
        else:
            prov = row.get("ai_provider")
            if prov == "openai":
                provider_prefix = "sk-"
            elif prov == "claude":
                provider_prefix = "sk-ant-"
            else:
                provider_prefix = "AIza... or AQ...."
            api_key_preview = f"{provider_prefix}...xxxx"

    monthly_limit = MONTHLY_LIMITS.get(row.get("tier", "free"), 3)

    return {
        "success": True,
        "data": {
            "email": row["email"],
            "full_name": row.get("full_name"),
            "tier": row.get("tier", "free"),
            "ai_provider": row.get("ai_provider"),
            "has_api_key": row.get("encrypted_api_key") is not None,
            "api_key_preview": api_key_preview,
            "logo_url": row.get("logo_url"),
            "brand_color": row.get("brand_color", "#6366F1"),
            "reports_this_month": row.get("reports_this_month", 0),
            "monthly_limit": monthly_limit,
        },
    }


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    full_name = body.full_name.strip()[:255]
    if not full_name:
        raise HTTPException(status_code=400, detail="full_name cannot be empty")

    await db.execute(
        text("UPDATE users SET full_name = :name, updated_at = NOW() WHERE id = :uid"),
        {"name": full_name, "uid": str(current_user.id)},
    )
    await db.commit()

    result = await db.execute(
        text("SELECT full_name, updated_at FROM users WHERE id = :uid"),
        {"uid": str(current_user.id)},
    )
    row = result.mappings().first()

    updated_at = row["updated_at"].isoformat() + "Z" if row and row.get("updated_at") else datetime.now(timezone.utc).isoformat() + "Z"

    return {
        "success": True,
        "data": {
            "full_name": row["full_name"] if row else full_name,
            "updated_at": updated_at,
        },
    }


@router.post("/api-key")
@limiter.limit("5/minute")
async def save_api_key(
    request: FastAPIRequest,
    body: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await check_pro_tier(current_user)

    if body.provider not in VALID_KEY_PATTERNS:
        raise HTTPException(
            status_code=400,
            detail="Provider must be 'openai', 'claude', or 'gemini'",
        )

    pattern = VALID_KEY_PATTERNS[body.provider]
    if not re.match(pattern, body.api_key):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid API key format for {body.provider}",
        )

    master_key = get_master_key()
    encrypted, iv = encrypt_api_key(body.api_key, master_key)

    key_preview = f"...{body.api_key[-4:]}"

    await db.execute(
        text("""
            UPDATE users SET
                encrypted_api_key = :encrypted,
                api_key_iv = :iv,
                ai_provider = :provider,
                api_key_preview = :preview,
                updated_at = NOW()
            WHERE id = :uid
        """),
        {
            "encrypted": encrypted,
            "iv": iv,
            "provider": body.provider,
            "preview": key_preview,
            "uid": str(current_user.id),
        },
    )
    await db.commit()

    return {
        "success": True,
        "data": {
            "provider": body.provider,
            "key_preview": key_preview,
            "saved_at": datetime.now(timezone.utc).isoformat() + "Z",
        },
    }


@router.delete("/api-key")
async def delete_api_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await check_pro_tier(current_user)

    await db.execute(
        text("""
            UPDATE users SET
                encrypted_api_key = NULL,
                api_key_iv = NULL,
                ai_provider = NULL,
                api_key_preview = NULL,
                updated_at = NOW()
            WHERE id = :uid
        """),
        {"uid": str(current_user.id)},
    )
    await db.commit()

    return {"success": True, "data": {"deleted": True}}


@router.post("/branding")
async def update_branding(
    brand_color: str = Form(None),
    company_name: str = Form(None),
    logo: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await check_pro_tier(current_user)

    logo_url = None

    if logo and logo.filename:
        ext = logo.filename.rsplit(".", 1)[-1].lower() if "." in logo.filename else ""
        if ext not in ALLOWED_LOGO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Logo must be .png, .jpg, or .svg. Received: .{ext}",
            )

        content = await logo.read()
        if len(content) > MAX_LOGO_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Logo file too large. Maximum size is 2MB.",
            )

        storage_path = f"logos/{str(current_user.id)}/logo.{ext}"
        try:
            await _run_sync(
                _get_supabase().storage.from_("logos").upload,
                storage_path,
                content,
                {"content-type": logo.content_type, "upsert": "true"},
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload logo: {str(e)}",
            )

        logo_url = storage_path

    if brand_color and not HEX_COLOR_PATTERN.match(brand_color):
        raise HTTPException(
            status_code=400,
            detail="brand_color must be a valid hex color (#RRGGBB)",
        )

    update_parts = ["updated_at = NOW()"]
    params: Dict[str, Any] = {"uid": str(current_user.id)}

    if logo_url is not None:
        update_parts.append("logo_url = :logo_url")
        params["logo_url"] = logo_url

    if brand_color is not None:
        update_parts.append("brand_color = :brand_color")
        params["brand_color"] = brand_color

    if company_name is not None:
        update_parts.append("company_name = :company_name")
        params["company_name"] = company_name.strip()[:255] if company_name else None

    if len(update_parts) == 1:
        raise HTTPException(status_code=400, detail="No fields to update")

    await db.execute(
        text(f"UPDATE users SET {', '.join(update_parts)} WHERE id = :uid"),
        params,
    )
    await db.commit()

    result = await db.execute(
        text("SELECT logo_url, brand_color, company_name FROM users WHERE id = :uid"),
        {"uid": str(current_user.id)},
    )
    row = result.mappings().first()

    return {
        "success": True,
        "data": {
            "logo_url": row["logo_url"] if row else logo_url,
            "brand_color": row["brand_color"] if row else brand_color,
            "company_name": row["company_name"] if row else company_name,
        },
    }


@router.post("/theme")
async def update_theme(
    body: ThemeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await db.execute(
        text("UPDATE users SET theme_preference = :theme, updated_at = NOW() WHERE id = :uid"),
        {"theme": body.theme, "uid": str(current_user.id)},
    )
    await db.commit()
    return {"success": True, "data": {"theme": body.theme}}


@router.delete("/account")
async def delete_account(
    body: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if body.email.strip().lower() != current_user.email.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="Email confirmation does not match your account email.",
        )

    uid = str(current_user.id)

    upload_result = await db.execute(
        text("SELECT file_url FROM uploads WHERE user_id = :uid"),
        {"uid": uid},
    )
    upload_paths = [r["file_url"] for r in upload_result.mappings().all() if r.get("file_url")]

    report_result = await db.execute(
        text("SELECT pdf_url, ppt_url FROM reports WHERE user_id = :uid"),
        {"uid": uid},
    )
    report_paths = []
    for r in report_result.mappings().all():
        if r.get("pdf_url"):
            report_paths.append(r["pdf_url"])
        if r.get("ppt_url"):
            report_paths.append(r["ppt_url"])

    if current_user.logo_url:
        logo_paths = [current_user.logo_url]
    else:
        logo_paths = []

    all_paths = {p for p in upload_paths + report_paths + logo_paths if p}

    try:
        for bucket, paths in [("uploads", upload_paths), ("reports", report_paths), ("logos", logo_paths)]:
            if paths:
                await _run_sync(
                    _get_supabase().storage.from_(bucket).remove,
                    paths,
                )
    except Exception as e:
        logger.warning("Storage cleanup during account deletion (non-fatal): %s", e)

    try:
        _get_supabase().auth.admin.delete_user(uid)
    except AuthApiError as e:
        if e.status != 404:
            logger.error("Supabase Auth user deletion failed (status %s): %s", e.status, e)
            raise HTTPException(
                status_code=502,
                detail="Account deletion failed at Auth provider, please try again.",
            )
        logger.info("Auth user %s already gone — proceeding with DB cleanup", uid)

    await db.execute(
        text("DELETE FROM users WHERE id = :uid"),
        {"uid": uid},
    )
    await db.commit()

    return {"success": True, "data": {"deleted": True}}
