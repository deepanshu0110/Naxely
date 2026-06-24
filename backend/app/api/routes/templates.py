import json
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import require_pro_or_above
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    template_type: str = "marketing"
    config: dict = Field(default_factory=dict)


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None


@router.get("/templates")
async def list_templates(
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    result = await db.execute(
        text("SELECT * FROM templates WHERE user_id = :uid ORDER BY created_at DESC"),
        {"uid": str(current_user.id)},
    )
    rows = result.mappings().all()

    templates = []
    for row in rows:
        templates.append({
            "id": str(row["id"]),
            "name": row["name"],
            "template_type": row.get("template_type", "marketing"),
            "is_default": row.get("is_default", False),
            "created_at": row["created_at"].isoformat() + "Z" if row.get("created_at") else None,
        })

    return {"success": True, "data": templates}


@router.post("/templates")
async def create_template(
    body: TemplateCreateRequest,
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    name = body.name.strip()[:255]
    if not name:
        raise HTTPException(status_code=400, detail="Template name cannot be empty")

    result = await db.execute(
        text("""
            INSERT INTO templates (user_id, name, template_type, config, is_default, created_at, updated_at)
            VALUES (:uid, :name, :template_type, :config, FALSE, NOW(), NOW())
            RETURNING id, name, template_type, is_default, created_at
        """),
        {
            "uid": str(current_user.id),
            "name": name,
            "template_type": body.template_type,
            "config": json.dumps(body.config),
        },
    )
    row = result.mappings().first()
    if not row:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create template")
    await db.commit()

    return {
        "success": True,
        "data": {
            "id": str(row["id"]),
            "name": row["name"],
            "template_type": row.get("template_type", "marketing"),
            "is_default": row.get("is_default", False),
            "created_at": row["created_at"].isoformat() + "Z" if row.get("created_at") else None,
        },
    }


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: str,
    body: TemplateUpdateRequest,
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    result = await db.execute(
        text("SELECT * FROM templates WHERE id = :tid AND user_id = :uid"),
        {"tid": template_id, "uid": str(current_user.id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    update_parts = ["updated_at = NOW()"]
    params: Dict[str, Any] = {"tid": template_id}

    if body.name is not None:
        name = body.name.strip()[:255]
        if not name:
            raise HTTPException(status_code=400, detail="Template name cannot be empty")
        update_parts.append("name = :name")
        params["name"] = name

    if body.is_default is not None:
        if body.is_default:
            await db.execute(
                text("UPDATE templates SET is_default = FALSE, updated_at = NOW() WHERE user_id = :uid AND is_default = TRUE"),
                {"uid": str(current_user.id)},
            )
        update_parts.append("is_default = :is_default")
        params["is_default"] = body.is_default

    await db.execute(
        text(f"UPDATE templates SET {', '.join(update_parts)} WHERE id = :tid"),
        params,
    )
    await db.commit()

    result = await db.execute(
        text("SELECT * FROM templates WHERE id = :tid"),
        {"tid": template_id},
    )
    updated = result.mappings().first()
    if not updated:
        raise HTTPException(status_code=404, detail="Template not found after update")

    return {
        "success": True,
        "data": {
            "id": str(updated["id"]),
            "name": updated["name"],
            "template_type": updated.get("template_type", "marketing"),
            "is_default": updated.get("is_default", False),
            "created_at": updated["created_at"].isoformat() + "Z" if updated.get("created_at") else None,
        },
    }


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    result = await db.execute(
        text("SELECT * FROM templates WHERE id = :tid AND user_id = :uid"),
        {"tid": template_id, "uid": str(current_user.id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.execute(
        text("DELETE FROM templates WHERE id = :tid"),
        {"tid": template_id},
    )
    await db.commit()

    return {"success": True, "data": {"deleted": True}}
