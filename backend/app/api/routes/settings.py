import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_pro_or_above, require_byok, require_agency
from app.services.api_key_service import generate_api_key as _generate_api_key
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
    "groq": r"^gsk_[a-zA-Z0-9\-_]{20,}$",
    "deepseek": r"^[a-zA-Z0-9\-_]{20,}$",
    "mistral": r"^[a-zA-Z0-9\-_]{20,}$",
    "together": r"^[a-zA-Z0-9\-_]{20,}$",
}

ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "svg"}
MAX_LOGO_SIZE = 2 * 1024 * 1024

MONTHLY_LIMITS = {"free": 3, "pro": None, "agency": None}

HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


async def _get_logo_signed_url(db_path: str | None) -> str | None:
    if not db_path:
        return None
    try:
        clean = db_path.removeprefix("logos/")
        def _sync():
            return _get_supabase().storage.from_("logos").create_signed_url(clean, 3600)
        signed = await _run_sync(_sync)
        return signed.get("signedURL", signed.get("signedUrl", ""))
    except Exception:
        return None


def extract_brand_colors(image_bytes: bytes, n: int = 3) -> list[str]:
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((150, 150), Image.Resampling.LANCZOS)
    quantized = img.quantize(colors=n, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette()
    colors: list[str] = []
    for i in range(n):
        r, g, b = palette[i*3], palette[i*3+1], palette[i*3+2]
        brightness = (r + g + b) / 3
        if brightness < 20 or brightness > 235:
            continue
        colors.append(f"#{r:02X}{g:02X}{b:02X}")
    return colors[:n]


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., max_length=255)


class ApiKeyRequest(BaseModel):
    provider: str
    api_key: Optional[str] = Field(None, max_length=200)


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
    logo_signed_url = await _get_logo_signed_url(row.get("logo_url"))

    return {
        "success": True,
        "data": {
            "email": row["email"],
            "full_name": row.get("full_name"),
            "tier": row.get("tier", "free"),
            "ai_provider": row.get("ai_provider"),
            "has_api_key": row.get("encrypted_api_key") is not None,
            "api_key_preview": api_key_preview,
            "logo_url": logo_signed_url,
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
    current_user: User = Depends(require_byok),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    if body.provider not in VALID_KEY_PATTERNS:
        raise HTTPException(
            status_code=400,
            detail="Provider must be one of: openai, claude, gemini, groq, deepseek, mistral, together",
        )

    # Gemini uses a server-side key — skip key validation, clear stored key
    if body.provider == "gemini":
        await db.execute(
            text("""
                UPDATE users SET
                    encrypted_api_key = NULL,
                    api_key_iv = NULL,
                    ai_provider = 'gemini',
                    api_key_preview = NULL,
                    updated_at = NOW()
                WHERE id = :uid
            """),
            {"uid": str(current_user.id)},
        )
        await db.commit()
        return {
            "success": True,
            "data": {
                "provider": "gemini",
                "key_preview": None,
                "saved_at": datetime.now(timezone.utc).isoformat() + "Z",
            },
        }

    if not body.api_key:
        raise HTTPException(
            status_code=400,
            detail="API key required for this provider",
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
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

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
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    logo_url = None
    suggested_colors = []

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

        suggested_colors = extract_brand_colors(content)

        storage_path = f"{str(current_user.id)}/logo.{ext}"
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
    logo_signed_url = await _get_logo_signed_url(row["logo_url"] if row else logo_url)

    return {
        "success": True,
        "data": {
            "logo_url": logo_signed_url,
            "brand_color": row["brand_color"] if row else brand_color,
            "company_name": row["company_name"] if row else company_name,
            "suggested_colors": suggested_colors,
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


@router.post("/api-keys", status_code=201)
async def create_api_key(
    body: dict,
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Key name is required")
    if len(name) > 100:
        raise HTTPException(status_code=400, detail="Key name must be under 100 characters")

    raw_key, key_prefix, key_suffix, key_hash = _generate_api_key()

    count_result = await db.execute(
        text("SELECT COUNT(*) FROM api_keys WHERE user_id = :uid AND revoked_at IS NULL"),
        {"uid": current_user.id},
    )
    count = count_result.scalar()
    if count >= 10:
        raise HTTPException(status_code=400, detail="Maximum of 10 active API keys allowed")

    result = await db.execute(
        text("""
            INSERT INTO api_keys (user_id, name, key_hash, key_prefix, key_suffix)
            VALUES (:uid, :name, :hash, :prefix, :suffix)
            RETURNING id, created_at
        """),
        {
            "uid": current_user.id,
            "name": name,
            "hash": key_hash,
            "prefix": key_prefix,
            "suffix": key_suffix,
        },
    )
    row = result.mappings().first()

    created_at = row["created_at"].isoformat() + "Z" if row.get("created_at") else datetime.now(timezone.utc).isoformat() + "Z"

    return {
        "id": row["id"],
        "name": name,
        "key": raw_key,
        "key_prefix": key_prefix,
        "key_suffix": key_suffix,
        "created_at": created_at,
        "message": "Save this key now. It will not be shown again.",
    }


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT id, name, key_prefix, key_suffix, created_at, last_used_at, revoked_at
            FROM api_keys
            WHERE user_id = :uid
            ORDER BY created_at DESC
        """),
        {"uid": current_user.id},
    )
    rows = result.mappings().all()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "key_display": f"{r['key_prefix']}...{r['key_suffix']}",
            "created_at": r["created_at"].isoformat() + "Z" if r.get("created_at") else None,
            "last_used_at": r["last_used_at"].isoformat() + "Z" if r.get("last_used_at") else None,
            "revoked": r["revoked_at"] is not None,
        }
        for r in rows
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            UPDATE api_keys
            SET revoked_at = NOW()
            WHERE id = CAST(:id AS uuid) AND user_id = CAST(:uid AS uuid) AND revoked_at IS NULL
        """),
        {"id": key_id, "uid": str(current_user.id)},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="API key not found or already revoked")
    await db.commit()
    return {"success": True, "message": "API key revoked"}
