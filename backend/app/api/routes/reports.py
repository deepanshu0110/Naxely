import uuid
import asyncio
import base64
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, File, UploadFile, Request, Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, EmailStr

from app.api.deps import get_current_user, require_pro_or_above, require_byok, require_agency, check_report_limit
from app.api.routes.settings import _get_logo_signed_url
from app.core.database import get_db
from app.services import sheets_service
from app.core.config import settings
from app.models.user import User
from app.services.report_service import run_report_pipeline
from app.services import data_service
from app.services import ai_service as ai_service_mod
from app.services import chart_service as chart_service_mod
from app.services.report_service import _make_user_proxy, _process_csv

from app.services.data_service import (
    parse_csv, validate_csv, validate_for_injection,
    detect_column_types,
)

from app.core.supabase_helpers import _get_supabase, _run_sync
from app.services.email_service import send_email
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MIME_TYPES = ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
MAX_FILE_SIZE = 10 * 1024 * 1024


class ColumnConfigItem(BaseModel):
    original_name: str
    display_name: Optional[str] = None
    type: Optional[Literal["date", "metric", "dimension", "text"]] = None
    include: bool = True


class DateRange(BaseModel):
    from_: str = Field(alias="from")
    to: str


class BrandConfig(BaseModel):
    company_name: Optional[str] = None
    prepared_by: Optional[str] = None
    color: Optional[str] = None
    logo_url: Optional[str] = None


class PreviewChartsRequest(BaseModel):
    upload_id: str
    column_config: Optional[List[ColumnConfigItem]] = None


class ChartSpecOverride(BaseModel):
    x: str
    y: str
    type: str
    title: str


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
    chart_specs: Optional[List[ChartSpecOverride]] = None

    model_config = {"populate_by_name": True}


class ShareRequest(BaseModel):
    expires_days: int = 30
    password: Optional[str] = None


class SendReportRequest(BaseModel):
    recipients: List[EmailStr] = Field(min_length=1)
    message: Optional[str] = None


async def _generate_signed_url(storage_path: str) -> str | None:
    def _sync():
        try:
            result = _get_supabase().storage.from_("reports").create_signed_url(
                storage_path, 3600
            )
            return result
        except UnboundLocalError as e:
            logger.warning(f"[reports] Supabase SDK UnboundLocalError for {storage_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"[reports] create_signed_url failed for {storage_path}: {e}")
            return None

    try:
        signed = await _run_sync(_sync)
        return signed.get("signedURL") if signed else None
    except Exception as e:
        logger.warning(f"[reports] _generate_signed_url outer error: {e}")
        return None


async def _store_csv_upload(
    db: AsyncSession,
    user_id: str,
    csv_bytes: bytes,
    source_type: str,
    filename: str,
    df: pd.DataFrame,
    upload_id: str | None = None,
    file_ext: str = "csv",
    content_type: str = "text/csv",
    extra_meta: dict | None = None,
) -> dict:
    """Store CSV bytes to Supabase Storage and insert into uploads table.

    Mirrors the exact storage paths used by upload_file():
    - uploads/{user_id}/{upload_id}/raw.{ext}
    - scheduled-sources/{upload_id}/raw.{ext}
    - uploads/permanent/{user_id}/{upload_id}.{ext}

    Returns dict with keys: id, file_url, columns
    """
    if upload_id is None:
        upload_id = str(uuid.uuid4())

    storage_path = f"{user_id}/{upload_id}/raw.{file_ext}"

    try:
        await _run_sync(
            _get_supabase().storage.from_("uploads").upload,
            storage_path,
            csv_bytes,
            {"content-type": content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {str(e)}")

    scheduled_source_path = f"{upload_id}/raw.{file_ext}"
    try:
        await _run_sync(
            _get_supabase().storage.from_("scheduled-sources").upload,
            scheduled_source_path,
            csv_bytes,
            {"content-type": content_type},
        )
    except Exception as e:
        try:
            await _run_sync(
                _get_supabase().storage.from_("uploads").remove, [storage_path],
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save scheduled-source copy: {str(e)}",
        )

    permanent_path = f"permanent/{user_id}/{upload_id}.{file_ext}"
    try:
        await _run_sync(
            _get_supabase().storage.from_("uploads").upload,
            permanent_path,
            csv_bytes,
            {"content-type": content_type},
        )
    except Exception as e:
        try:
            await _run_sync(
                _get_supabase().storage.from_("uploads").remove, [storage_path],
            )
        except Exception:
            pass
        try:
            await _run_sync(
                _get_supabase().storage.from_("scheduled-sources").remove, [scheduled_source_path],
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save permanent copy: {str(e)}",
        )

    columns_meta = detect_column_types(df)
    columns_meta_json = json.dumps(columns_meta)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

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
                "user_id": user_id,
                "filename": filename,
                "file_url": storage_path,
                "file_size_bytes": len(csv_bytes),
                "source_type": source_type,
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
        try:
            await _run_sync(
                _get_supabase().storage.from_("scheduled-sources").remove, [scheduled_source_path],
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to save upload metadata: {str(e)}")

    return {
        "id": upload_id,
        "file_url": storage_path,
        "columns": columns_meta,
    }


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
                    "upgrade_url": f"{settings.FRONTEND_BASE_URL}/pricing",
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

    if file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        file_ext = "xlsx"
        content_type = file.content_type
    else:
        file_ext = "csv"
        content_type = "text/csv"

    source_type = "csv" if file_ext == "csv" else "xlsx"

    upload_record = await _store_csv_upload(
        db=db,
        user_id=str(current_user.id),
        csv_bytes=content,
        source_type=source_type,
        filename=file.filename,
        df=df,
        file_ext=file_ext,
        content_type=content_type,
    )
    upload_id = upload_record["id"]
    storage_path = upload_record["file_url"]
    columns_meta = upload_record["columns"]

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
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Ingest a Google Sheet as a report data source.
    Returns an upload_id identical to POST /reports/upload.
    The report generation pipeline is then identical for both sources.

    The user must share their sheet with the Naxely service account email
    (shown in the frontend). Viewer access is sufficient.
    """
    sheets_url = sheets_data.get("sheets_url")
    if not sheets_url:
        raise HTTPException(status_code=400, detail="sheets_url is required")
    if not sheets_url.startswith("https://docs.google.com/spreadsheets/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must be a Google Sheets URL "
                   "(https://docs.google.com/spreadsheets/d/...)"
        )

    try:
        sheet_id = sheets_service.extract_sheet_id(sheets_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        creds = sheets_service.build_credentials(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail="Google Sheets integration is not configured on this server.",
        )

    try:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, lambda: sheets_service.fetch_sheet_as_df(sheet_id, creds)
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    import io as _io
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    filename = f"Google Sheet - {sheet_id}.csv"

    upload_record = await _store_csv_upload(
        db=db,
        user_id=str(current_user.id),
        csv_bytes=csv_bytes,
        source_type="sheets",
        filename=filename,
        df=df,
    )

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
            "upload_id": upload_record["id"],
            "filename": filename,
            "file_url": upload_record["file_url"],
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": upload_record["columns"],
            "preview_rows": preview_rows,
            "source_type": "sheets",
            "sheets_url": sheets_url,
        },
    }


@router.get("/reports/sheets-config")
async def get_sheets_config(
    current_user: User = Depends(require_pro_or_above),
) -> Dict[str, Any]:
    """Return the service account email users must share their sheet with."""
    email = sheets_service.get_service_account_email(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON
    )
    return {
        "configured": bool(email),
        "service_account_email": email or None,
    }


SAMPLE_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "static" / "samples" / "agency_billable_hours.csv"


@router.post("/reports/sample-upload")
async def sample_upload(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if not SAMPLE_CSV_PATH.exists():
        raise HTTPException(status_code=500, detail="Sample data file not found")

    with open(SAMPLE_CSV_PATH, "rb") as f:
        content = f.read()

    try:
        df = parse_csv(content)
        validate_csv(df)
        validate_for_injection(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    columns_meta = detect_column_types(df)
    upload_id = str(uuid.uuid4())
    filename = "agency_billable_hours.csv"
    file_ext = "csv"

    storage_path = f"{current_user.id}/{upload_id}/raw.{file_ext}"

    try:
        await _run_sync(
            _get_supabase().storage.from_("uploads").upload,
            storage_path,
            content,
            {"content-type": "text/csv"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload sample to storage: {str(e)}")

    scheduled_source_path = f"{upload_id}/raw.{file_ext}"
    try:
        await _run_sync(
            _get_supabase().storage.from_("scheduled-sources").upload,
            scheduled_source_path,
            content,
            {"content-type": "text/csv"},
        )
    except Exception as e:
        try:
            await _run_sync(
                _get_supabase().storage.from_("uploads").remove, [storage_path],
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to save scheduled-source copy: {str(e)}")

    permanent_path = f"permanent/{current_user.id}/{upload_id}.{file_ext}"
    try:
        await _run_sync(
            _get_supabase().storage.from_("uploads").upload,
            permanent_path,
            content,
            {"content-type": "text/csv"},
        )
    except Exception as e:
        try:
            await _run_sync(
                _get_supabase().storage.from_("uploads").remove, [storage_path],
            )
        except Exception:
            pass
        try:
            await _run_sync(
                _get_supabase().storage.from_("scheduled-sources").remove, [scheduled_source_path],
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to save permanent copy: {str(e)}")

    columns_meta_json = json.dumps(columns_meta)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

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
                "filename": filename,
                "file_url": storage_path,
                "file_size_bytes": len(content),
                "source_type": "csv",
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
            "filename": filename,
            "file_url": storage_path,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns_meta,
            "preview_rows": preview_rows,
        },
    }


@router.get("/uploads")
async def list_uploads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        text("""
            SELECT id, filename, row_count, column_count, created_at
            FROM uploads
            WHERE user_id = :user_id AND used = FALSE
            ORDER BY created_at DESC
            LIMIT 50
        """),
        {"user_id": str(current_user.id)},
    )
    rows = result.mappings().all()
    return {
        "success": True,
        "data": [
            {
                "upload_id": str(r["id"]),
                "filename": r["filename"],
                "row_count": r["row_count"],
                "column_count": r["column_count"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ],
    }


@router.post("/reports/preview-charts")
async def preview_charts(
    body: PreviewChartsRequest,
    current_user: User = Depends(require_byok),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM uploads WHERE id = :uid AND user_id = :owner"),
        {"uid": body.upload_id, "owner": str(current_user.id)},
    )
    upload = result.mappings().first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    csv_bytes = await _run_sync(
        _get_supabase().storage.from_("uploads").download, upload["file_url"],
    )
    df = parse_csv(csv_bytes)
    config = {"column_config": [c.model_dump() for c in body.column_config] if body.column_config else []}
    df, df_norm = _process_csv(df, config)

    chart_specs = None
    try:
        user_result = await db.execute(
            text("SELECT * FROM users WHERE id = :uid"), {"uid": str(current_user.id)}
        )
        user_obj = _make_user_proxy(
            dict(user_result.mappings().first() or {})
        )
        provider, api_key = ai_service_mod.get_user_api_key(user_obj)
        chart_specs = chart_service_mod.select_charts_with_ai(
            df=df_norm, config=config, provider=provider, api_key=api_key, max_charts=3,
        )
    except Exception:
        logger.warning("[preview_charts] AI chart selection failed, using rule-based fallback")

    if not chart_specs:
        metric_columns = [c for c in df_norm.columns if pd.api.types.is_numeric_dtype(df_norm[c])]
        date_column = config.get("date_column")
        dimension_columns = [
            c for c in df_norm.columns
            if c != date_column and not pd.api.types.is_numeric_dtype(df_norm[c]) and df_norm[c].nunique() <= 10
        ]
        pairs = chart_service_mod._select_chart_pairs(df_norm, date_column, metric_columns, dimension_columns, 3)
        chart_specs = [
            {"x": x, "y": y, "type": chart_service_mod.select_chart_type(x, y, df_norm), "title": f"{y} by {x}"}
            for x, y in pairs
        ]

    return {"chart_specs": chart_specs}


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
        require_pro_or_above(current_user)

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

    if body.chart_specs:
        config_json["chart_specs_override"] = [s.model_dump() for s in body.chart_specs]

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

    real_step = report.get("current_step") or ""
    defaults = (10, "Initializing...", [],
                ["parsing", "charts", "ai_insights", "pdf_build"] if has_ai else ["parsing", "charts", "pdf_build"])
    progress_percent, current_step_label, steps_completed, steps_remaining = step_map.get(real_step, defaults)  # type: ignore[misc]

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


@router.get("/reports/{report_id}/export/pptx")
async def export_report_pptx(
    report_id: str,
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    import asyncio
    import io as _io
    from fastapi.responses import Response
    from app.services.pptx_service import generate_pptx
    from app.services.chart_service import generate_sync as generate_charts
    from app.services.pdf_service import _compute_kpi_data
    from app.services.report_service import get_upload

    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report = dict(report)

    user_row = await db.execute(
        text("SELECT brand_color, company_name, logo_url, tier FROM users WHERE id = :uid"),
        {"uid": str(current_user.id)},
    )
    user_row_data = user_row.mappings().first()
    raw_logo_path = (user_row_data.get("logo_url") if user_row_data else None)
    logo_signed_url = await _get_logo_signed_url(raw_logo_path) if raw_logo_path else None
    user_data = {
        "brand_color": (user_row_data.get("brand_color") if user_row_data else None) or "#0E9F6E",
        "company_name": (user_row_data.get("company_name") if user_row_data else None),
        "logo_url": logo_signed_url,
        "tier": "agency",
    }

    config = report.get("config") or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except Exception:
            config = {}
    upload_id = config.get("upload_id")
    if not upload_id:
        raise HTTPException(status_code=422, detail="Report has no associated CSV upload")

    upload = await get_upload(upload_id)
    if not upload:
        raise HTTPException(status_code=422, detail="Original CSV not found in storage")
    file_ext = "csv" if upload.get("source_type") != "xlsx" else "xlsx"
    permanent_path = f"permanent/{current_user.id}/{upload_id}.{file_ext}"

    csv_bytes = await _run_sync(
        _get_supabase().storage.from_("uploads").download, permanent_path,
    )

    import pandas as pd
    df = pd.read_csv(_io.BytesIO(csv_bytes))

    df_norm = df.copy()
    for col in df_norm.select_dtypes(include=["object"]).columns:
        df_norm[col] = pd.to_numeric(df_norm[col], errors="ignore")

    brand_color = user_data["brand_color"]
    ai_content = {
        "summary": report.get("ai_summary"),
        "insights": report.get("ai_insights") or [],
        "anomalies": report.get("ai_anomalies") or [],
        "trends": [],
    }

    try:
        kpis = _compute_kpi_data(df_norm, config, ai_content, brand_color)
    except Exception:
        kpis = []
    logger.info(f"pptx export kpis: {kpis}  metric_columns={config.get('metric_columns')}  _precomputed_kpis={config.get('_precomputed_kpis')}")
    config["_precomputed_kpis"] = kpis
    config["_ai_skipped"] = report.get("ai_skipped", False)
    config["report_id"] = report_id

    loop = asyncio.get_event_loop()
    try:
        chart_paths = await loop.run_in_executor(
            None,
            lambda: generate_charts(df_norm, report_id + "_pptx", config, brand_color),
        )
    except Exception:
        logger.warning(f"[pptx_export] chart regeneration failed, continuing without charts")
        chart_paths = []

    seen = set()
    chart_paths = [
        p for p in chart_paths
        if (key := p[1] if isinstance(p, tuple) else p) not in seen
        and not seen.add(key)
    ]

    pptx_bytes = await loop.run_in_executor(
        None,
        lambda: generate_pptx(df, chart_paths, ai_content, config, user_data),
    )

    try:
        storage_path = f"pptx/{current_user.id}/{report_id}.pptx"
        await _run_sync(
            _get_supabase().storage.from_("reports").upload,
            storage_path,
            pptx_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
        )
        await db.execute(
            text("UPDATE reports SET ppt_url = :url WHERE id = :rid"),
            {"url": storage_path, "rid": report_id},
        )
        await db.commit()
    except Exception as e:
        logger.warning(f"[pptx_export] failed to store ppt_url: {e}")

    filename = f"naxely_report_{report_id[:8]}.pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :id AND user_id = :uid AND deleted_at IS NULL"),
        {"id": report_id, "uid": str(current_user.id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    if row["status"] != "completed":
        raise HTTPException(status_code=409, detail="Report is not yet completed")

    import httpx
    signed_url = await _generate_signed_url(row["pdf_url"])
    if not signed_url:
        raise HTTPException(status_code=502, detail="Could not generate signed URL for PDF")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(signed_url, follow_redirects=True)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not retrieve PDF: {e}")

    filename = f"naxely_report_{report_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
            "trend_pct": row.get("trend_pct"),
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
        "row_count": report.get("row_count"),
        "column_count": report.get("column_count"),
        "trend_pct": report.get("trend_pct"),
        "generation_time_seconds": report.get("generation_time_seconds"),
        "pdf_url": await _generate_signed_url(report["pdf_url"]) if report["status"] == "completed" and report.get("pdf_url") else None,
        "share_token": report.get("share_token"),
        "share_view_count": report.get("share_view_count", 0),
        "created_at": report["created_at"].isoformat() if report.get("created_at") else None,
        "error_message": report.get("error_message"),
        "ai_skipped": report.get("ai_skipped", False),
    }

    return {"success": True, "data": data}


@router.post("/reports/{report_id}/retry")
async def retry_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_byok),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["status"] != "failed":
        raise HTTPException(status_code=400, detail="Only failed reports can be retried")

    config_raw = report.get("config", {})
    if isinstance(config_raw, str):
        config_raw = json.loads(config_raw)

    await db.execute(
        text("""
            UPDATE reports SET
                status = 'pending',
                error_message = NULL,
                generation_time_seconds = NULL,
                updated_at = NOW()
            WHERE id = :rid
        """),
        {"rid": report_id},
    )
    await db.commit()

    background_tasks.add_task(
        run_report_pipeline,
        report_id=report_id,
        user_id=str(current_user.id),
        config=config_raw,
    )

    return {
        "success": True,
        "data": {
            "report_id": report_id,
            "status": "processing",
            "poll_url": f"/reports/{report_id}/status",
        },
    }


class BulkDeleteRequest(BaseModel):
    report_ids: List[str]


@router.post("/reports/bulk-delete")
async def bulk_delete_reports(
    body: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if not body.report_ids:
        return {"deleted": 0}

    if len(body.report_ids) > 50:
        raise HTTPException(status_code=400, detail="Max 50 reports per bulk delete")

    result = await db.execute(
        text("""
            SELECT id, pdf_url FROM reports
            WHERE id = ANY(:ids) AND user_id = :uid
        """),
        {"ids": body.report_ids, "uid": str(current_user.id)},
    )
    rows = result.mappings().all()

    if not rows:
        return {"deleted": 0}

    for row in rows:
        if row.get("pdf_url"):
            try:
                await _run_sync(
                    _get_supabase().storage.from_("reports").remove,
                    [row["pdf_url"]],
                )
            except Exception:
                pass

    deleted_ids = [str(row["id"]) for row in rows]
    await db.execute(
        text("DELETE FROM reports WHERE id = ANY(:ids) AND user_id = :uid"),
        {"ids": deleted_ids, "uid": str(current_user.id)},
    )
    await db.commit()

    logger.info(f"[bulk_delete] user={current_user.id} deleted {len(deleted_ids)} reports")
    return {"deleted": len(deleted_ids), "ids": deleted_ids}


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
    current_user: User = Depends(require_pro_or_above),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:

    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :rid AND deleted_at IS NULL AND user_id = :uid"),
        {"rid": report_id, "uid": str(current_user.id)},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_days)

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
            "share_url": f"{settings.FRONTEND_BASE_URL}/share/{token}",
            "share_token": token,
            "expires_at": expires_at.isoformat() + "Z",
        },
    }


@router.delete("/reports/{report_id}/share")
async def revoke_share(
    report_id: str,
    current_user: User = Depends(require_pro_or_above),
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


@router.post("/reports/{report_id}/send", dependencies=[Depends(require_pro_or_above)])
async def send_report_to_client(
    report_id: str,
    payload: SendReportRequest,
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

    if not report.get("pdf_url"):
        raise HTTPException(status_code=409, detail="Report has no PDF to send")

    pdf_bytes = await _run_sync(
        _get_supabase().storage.from_("reports").download,
        report["pdf_url"],
    )
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    subject = f"{report['title']} — from {current_user.company_name or current_user.email}"

    html_parts = [f"<p>Your report <strong>{report['title']}</strong> is ready.</p>"]
    if payload.message:
        html_parts.append(f"<blockquote style='border-left:3px solid #d97706;padding-left:12px;margin:16px 0;color:#555;'><p>{payload.message}</p></blockquote>")
    html_parts.append("<p>The report PDF is attached.</p>")

    ok = send_email(
        to=payload.recipients,
        subject=subject,
        html="".join(html_parts),
        attachments=[{
            "filename": f"{report['title']}.pdf",
            "content": pdf_b64,
        }],
    )
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to send email")

    return {"success": True, "data": {"sent": True, "recipients": len(payload.recipients)}}


@router.get("/share/{share_token}")
async def get_shared_report(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await db.execute(
        text("""
            SELECT r.*, u.tier AS user_tier
            FROM reports r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.share_token = :token AND r.deleted_at IS NULL
        """),
        {"token": share_token},
    )
    report = result.mappings().first()
    if not report:
        raise HTTPException(status_code=404, detail="Shared report not found")

    if report.get("share_expires_at") and report["share_expires_at"] < datetime.now(timezone.utc):
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
            "is_white_label": report.get("user_tier") == "agency",
        },
    }
