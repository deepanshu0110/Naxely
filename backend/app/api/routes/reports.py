import uuid
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, File, UploadFile, Request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, check_pro_tier, check_report_limit
from app.core.database import get_db
from app.models.user import User
from app.services.report_service import run_report_pipeline
from app.services.data_service import (
    parse_csv, validate_csv, validate_for_injection,
    detect_column_types,
)

from app.core.supabase_helpers import _get_supabase, _run_sync
from app.core.limiter import limiter

router = APIRouter()

ALLOWED_MIME_TYPES = ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
MAX_FILE_SIZE = 10 * 1024 * 1024


class ColumnConfigItem(BaseModel):
    original_name: str
    display_name: Optional[str] = None
    type: Optional[str] = None
    include: bool = True


class DateRange(BaseModel):
    from_: str = Field(alias="from")
    to: str


class BrandConfig(BaseModel):
    company_name: Optional[str] = None
    prepared_by: Optional[str] = None
    color: Optional[str] = None
    logo_url: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    upload_id: str
    title: str
    template_type: str = "marketing"
    tone: str = "professional"
    sections: List[str] = []
    date_range: Optional[DateRange] = None
    column_config: List[ColumnConfigItem] = []
    brand: Optional[BrandConfig] = None
    workspace_id: Optional[str] = None

    model_config = {"populate_by_name": True}


class ShareRequest(BaseModel):
    expires_days: int = 30
    password: Optional[str] = None


async def _generate_signed_url(storage_path: str) -> str:
    def _sync():
        return _get_supabase().storage.from_("reports").create_signed_url(storage_path, 3600)
    signed = await _run_sync(_sync)
    return signed.get("signedURL", signed.get("signedUrl", ""))


AI_SECTIONS = {"executive_summary", "insights", "anomalies", "trends"}


def _has_ai_sections(sections: list) -> bool:
    return bool(set(sections) & AI_SECTIONS)


@router.post("/reports/upload")
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if current_user.tier == "free":
        if current_user.reports_this_month >= 3:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "MONTHLY_LIMIT_REACHED",
                    "message": "You've used all 3 free reports this month.",
                    "upgrade_url": "https://databrief.io/pricing",
                },
            )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Only CSV and XLSX files are allowed. Received: {file.content_type}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    try:
        df = parse_csv(content)
        validate_csv(df)
        validate_for_injection(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    columns_meta = detect_column_types(df)

    upload_id = str(uuid.uuid4())

    if file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        file_ext = "xlsx"
    else:
        file_ext = "csv"

    storage_path = f"uploads/{current_user.id}/{upload_id}/raw.{file_ext}"

    try:
        await _run_sync(
            _get_supabase().storage.from_("uploads").upload,
            storage_path,
            content,
            {"content-type": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {str(e)}")

    columns_meta_json = json.dumps(columns_meta)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    try:
        await db.execute(
            text("""
                INSERT INTO uploads (
                    id, user_id, filename, file_url, file_size_bytes, source_type,
                    row_count, column_count, columns_meta, expires_at, used, created_at
                ) VALUES (
                    :id, :user_id, :filename, :file_url, :file_size_bytes, :source_type,
                    :row_count, :column_count, :columns_meta, :expires_at, FALSE, NOW()
                )
            """),
            {
                "id": upload_id,
                "user_id": str(current_user.id),
                "filename": file.filename,
                "file_url": storage_path,
                "file_size_bytes": len(content),
                "source_type": "csv" if file_ext == "csv" else "xlsx",
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns_meta": columns_meta_json,
                "expires_at": expires_at,
            },
        )
        await db.commit()
    except Exception as e:
        try:
            await _run_sync(
                _get_supabase().storage.from_("uploads").remove, [storage_path],
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to save upload metadata: {str(e)}")

    preview_rows = []
    for _, row in df.head(5).iterrows():
        preview_row: Dict[str, Optional[str]] = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                preview_row[str(col)] = None
            else:
                preview_row[str(col)] = str(val)
        preview_rows.append(preview_row)

    return {
        "success": True,
        "data": {
            "upload_id": upload_id,
            "filename": file.filename,
            "file_url": storage_path,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns_meta,
            "preview_rows": preview_rows,
        },
    }


@router.post("/reports/upload-sheets")
async def upload_sheets(
    sheets_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if current_user.tier not in ("pro", "agency"):
        raise HTTPException(
            status_code=402,
            detail={
                "code": "PRO_REQUIRED",
                "message": "This feature requires a Pro subscription.",
                "upgrade_url": "https://databrief.io/pricing",
            },
        )

    sheets_url = sheets_data.get("sheets_url")
    if not sheets_url:
        raise HTTPException(status_code=400, detail="sheets_url is required")
    if not sheets_url.startswith("https://docs.google.com/spreadsheets/"):
        raise HTTPException(status_code=400, detail="Invalid URL. Must be a Google Sheets URL.")

    raise HTTPException(status_code=501, detail="Google Sheets integration coming soon")


@router.post("/reports/generate")
@limiter.limit("10/minute")
async def generate_report(
    request: Request,
    body: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await check_report_limit(current_user)

    result = await db.execute(
        text("SELECT * FROM uploads WHERE id = :uid AND user_id = :owner"),
        {"uid": body.upload_id, "owner": str(current_user.id)},
    )
    upload = result.mappings().first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if _has_ai_sections(body.sections):
        await check_pro_tier(current_user)

    existing = await db.execute(
        text("""
            SELECT id FROM reports
            WHERE user_id = :uid
              AND status IN ('pending', 'processing')
              AND config::jsonb->>'upload_id' = :upload_id
              AND deleted_at IS NULL
            LIMIT 1
        """),
        {"uid": str(current_user.id), "upload_id": body.upload_id},
    )
    existing_row = existing.mappings().first()
    if existing_row:
        return {
            "success": True,
            "data": {
                "report_id": str(existing_row["id"]),
                "status": "processing",
                "estimated_seconds": 45,
                "poll_url": f"/reports/{existing_row['id']}/status",
            },
        }

    report_id = str(uuid.uuid4())

    config_json = body.model_dump(by_alias=True)
    config_json["upload_id"] = body.upload_id

    try:
        await db.execute(
            text("""
                INSERT INTO reports (id, user_id, title, template_type, status, source_type,
                    source_filename, config, created_at, updated_at)
                VALUES (:id, :uid, :title, :template, 'pending', 'csv', :filename, :config, NOW(), NOW())
            """),
            {
                "id": report_id,
                "uid": str(current_user.id),
                "title": body.title,
                "template": body.template_type,
                "filename": upload.get("filename"),
                "config": json.dumps(config_json),
            },
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        winner = await db.execute(
            text("""
                SELECT id FROM reports
                WHERE user_id = :uid
                  AND config::jsonb->>'upload_id' = :upload_id
                  AND status IN ('pending', 'processing')
                  AND deleted_at IS NULL
                LIMIT 1
            """),
            {"uid": str(current_user.id), "upload_id": body.upload_id},
        )
        winner_row = winner.mappings().first()
        if winner_row:
            return {
                "success": True,
                "data": {
                    "report_id": str(winner_row["id"]),
                    "status": "processing",
                    "estimated_seconds": 45,
                    "poll_url": f"/reports/{winner_row['id']}/status",
                },
            }
        raise

    background_tasks.add_task(
        run_report_pipeline,
        report_id=report_id,
        user_id=str(current_user.id),
        config=config_json,
    )

    return {
        "success": True,
        "data": {
            "report_id": report_id,
            "status": "processing",
            "estimated_seconds": 45,
            "poll_url": f"/reports/{report_id}/status",
        },
    }


@router.get("/reports/{report_id}/status")
async def get_report_status(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    status_val = report["status"]

    if status_val == "completed":
        pdf_url = ""
        if report["pdf_url"]:
            pdf_url = await _generate_signed_url(report["pdf_url"])
        return {
            "success": True,
            "data": {
                "report_id": report_id,
                "status": "completed",
                "progress_percent": 100,
                "pdf_url": pdf_url,
                "generation_time_seconds": report.get("generation_time_seconds"),
                "error_message": report.get("error_message"),
            },
        }

    if status_val == "failed":
        return {
            "success": False,
            "data": {
                "report_id": report_id,
                "status": "failed",
                "error_message": report.get("error_message"),
            },
        }

    config_raw = report.get("config", {})
    if isinstance(config_raw, str):
        try:
            config_raw = json.loads(config_raw)
        except Exception:
            config_raw = {}
    sections = config_raw.get("sections", [])
    has_ai = _has_ai_sections(sections)

    step_map = {
        "data": (20, "Parsing data...", ["parsing"], ["charts", "ai_insights", "pdf_build"] if has_ai else ["charts", "pdf_build"]),
        "charts": (45, "Generating charts...", ["parsing", "charts"], ["ai_insights", "pdf_build"] if has_ai else ["pdf_build"]),
        "ai": (65, "Generating AI insights...", ["parsing", "charts", "ai_insights"], ["pdf_build"]),
        "pdf": (85, "Building PDF...", ["parsing", "charts", "ai_insights", "pdf_build"] if has_ai else ["parsing", "charts", "pdf_build"], []),
    }

    progress_percent = 10
    current_step_label = "Initializing..."
    steps_completed: list[str] = []
    steps_remaining: list[str] = ["parsing", "charts", "ai_insights", "pdf_build"] if has_ai else ["parsing", "charts", "pdf_build"]

    for _step_key, (_pct, _label, _completed, _remaining) in step_map.items():
        progress_percent = _pct  # type: ignore[assignment]
        current_step_label = _label  # type: ignore[assignment]
        steps_completed = _completed  # type: ignore[assignment]
        steps_remaining = _remaining  # type: ignore[assignment]

    return {
        "success": True,
        "data": {
            "report_id": report_id,
            "status": "processing",
            "progress_percent": progress_percent,
            "current_step": current_step_label,
            "steps_completed": steps_completed,
            "steps_remaining": steps_remaining,
        },
    }


@router.get("/reports")
async def list_reports(
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    workspace_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"uid": str(current_user.id), "lim": limit, "off": offset}

    where_clause = "user_id = :uid AND deleted_at IS NULL"
    if workspace_id:
        where_clause += " AND workspace_id = :wid"
        params["wid"] = workspace_id

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM reports WHERE {where_clause}"),
        params,
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        text(f"SELECT * FROM reports WHERE {where_clause} ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
        params,
    )
    rows = result.mappings().all()

    reports = []
    for row in rows:
        item = {
            "id": str(row["id"]),
            "title": row["title"],
            "template_type": row["template_type"],
            "status": row["status"],
            "row_count": row.get("row_count"),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "generation_time_seconds": row.get("generation_time_seconds"),
        }
        if row["status"] == "completed" and row.get("pdf_url"):
            item["pdf_url"] = await _generate_signed_url(row["pdf_url"])
        else:
            item["pdf_url"] = None
        reports.append(item)

    return {
        "success": True,
        "data": {
            "reports": reports,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    ai_insights_raw = report.get("ai_insights")
    if isinstance(ai_insights_raw, str):
        try:
            ai_insights = json.loads(ai_insights_raw)
        except Exception:
            ai_insights = []
    elif isinstance(ai_insights_raw, list):
        ai_insights = ai_insights_raw
    else:
        ai_insights = []

    ai_anomalies_raw = report.get("ai_anomalies")
    if isinstance(ai_anomalies_raw, str):
        try:
            ai_anomalies = json.loads(ai_anomalies_raw)
        except Exception:
            ai_anomalies = []
    elif isinstance(ai_anomalies_raw, list):
        ai_anomalies = ai_anomalies_raw
    else:
        ai_anomalies = []

    data: Dict[str, Any] = {
        "id": str(report["id"]),
        "title": report["title"],
        "status": report["status"],
        "ai_summary": report.get("ai_summary"),
        "ai_insights": ai_insights,
        "ai_anomalies": ai_anomalies,
        "pdf_url": await _generate_signed_url(report["pdf_url"]) if report["status"] == "completed" and report.get("pdf_url") else None,
        "share_token": report.get("share_token"),
        "share_view_count": report.get("share_view_count", 0),
        "created_at": report["created_at"].isoformat() if report.get("created_at") else None,
        "error_message": report.get("error_message"),
    }

    return {"success": True, "data": data}


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.execute(
        text("UPDATE reports SET deleted_at = NOW() WHERE id = :rid"),
        {"rid": report_id},
    )
    await db.commit()

    return {"success": True, "data": {"deleted": True}}


@router.post("/reports/{report_id}/share")
async def share_report(
    report_id: str,
    body: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await check_pro_tier(current_user)

    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(days=body.expires_days)

    await db.execute(
        text("""
            UPDATE reports SET share_token = :token, share_expires_at = :expires_at
            WHERE id = :rid
        """),
        {"token": token, "expires_at": expires_at, "rid": report_id},
    )
    await db.commit()

    return {
        "success": True,
        "data": {
            "share_url": f"https://databrief.io/share/{token}",
            "share_token": token,
            "expires_at": expires_at.isoformat() + "Z",
        },
    }


@router.delete("/reports/{report_id}/share")
async def revoke_share(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.execute(
        text("UPDATE reports SET share_token = NULL, share_expires_at = NULL WHERE id = :rid"),
        {"rid": report_id},
    )
    await db.commit()

    return {"success": True, "data": {"revoked": True}}


@router.get("/share/{share_token}")
async def get_shared_report(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM reports WHERE share_token = :token AND deleted_at IS NULL"),
        {"token": share_token},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Shared report not found")

    if report.get("share_expires_at") and report["share_expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link has expired")

    await db.execute(
        text("UPDATE reports SET share_view_count = share_view_count + 1 WHERE id = :rid"),
        {"rid": str(report["id"])},
    )
    await db.commit()

    pdf_url = None
    if report.get("pdf_url"):
        pdf_url = await _generate_signed_url(report["pdf_url"])

    ai_insights_raw = report.get("ai_insights")
    if isinstance(ai_insights_raw, str):
        try:
            ai_insights = json.loads(ai_insights_raw)
        except Exception:
            ai_insights = []
    elif isinstance(ai_insights_raw, list):
        ai_insights = ai_insights_raw
    else:
        ai_insights = []

    ai_anomalies_raw = report.get("ai_anomalies")
    if isinstance(ai_anomalies_raw, str):
        try:
            ai_anomalies = json.loads(ai_anomalies_raw)
        except Exception:
            ai_anomalies = []
    elif isinstance(ai_anomalies_raw, list):
        ai_anomalies = ai_anomalies_raw
    else:
        ai_anomalies = []

    return {
        "success": True,
        "data": {
            "id": str(report["id"]),
            "title": report["title"],
            "status": report["status"],
            "template_type": report["template_type"],
            "ai_summary": report.get("ai_summary"),
            "ai_insights": ai_insights,
            "ai_anomalies": ai_anomalies,
            "pdf_url": pdf_url,
            "created_at": report["created_at"].isoformat() if report.get("created_at") else None,
        },
    }
