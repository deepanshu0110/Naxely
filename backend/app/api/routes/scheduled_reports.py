import base64
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_agency
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_db
from app.models.user import User
from app.services.email_service import send_email
from app.services.report_service import run_report_pipeline, _get_supabase, _run_sync
from app.services.scheduled_report_service import copy_upload_to_scheduled_source

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scheduled_reports"])

ALLOWED_FREQUENCIES = {"daily", "weekly", "monthly"}


class ScheduledReportCreate(BaseModel):
    upload_id: str
    name: str
    frequency: str
    recipient_emails: list[str]
    template_id: str | None = None
    workspace_id: str | None = None
    config_json: str | None = None

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        if v not in ALLOWED_FREQUENCIES:
            raise ValueError(f"frequency must be one of: {', '.join(sorted(ALLOWED_FREQUENCIES))}")
        return v

    @field_validator("recipient_emails")
    @classmethod
    def validate_recipients(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("recipient_emails must not be empty")
        return v


class ScheduledReportUpdate(BaseModel):
    name: str | None = None
    frequency: str | None = None
    recipient_emails: list[str] | None = None
    is_active: bool | None = None
    template_id: str | None = None
    config_json: str | None = None

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str | None) -> str | None:
        if v is not None and v not in ALLOWED_FREQUENCIES:
            raise ValueError(f"frequency must be one of: {', '.join(sorted(ALLOWED_FREQUENCIES))}")
        return v


class ScheduledReportResponse(BaseModel):
    id: str
    name: str
    frequency: str
    next_run_at: datetime
    last_run_at: datetime | None
    recipient_emails: list[str]
    csv_storage_path: str | None
    config_json: str | None
    is_active: bool
    created_at: datetime
    template_id: str | None
    workspace_id: str | None


def _compute_next_run(frequency: str) -> datetime:
    now = datetime.now(timezone.utc)
    if frequency == "daily":
        return now + timedelta(days=1)
    elif frequency == "weekly":
        return now + timedelta(weeks=1)
    elif frequency == "monthly":
        return now + timedelta(days=30)
    return now + timedelta(days=1)


async def _get_scheduled_report_or_404(
    report_id: str, user_id: str, db: AsyncSession,
) -> dict:
    result = await db.execute(
        text("SELECT * FROM scheduled_reports WHERE id = :rid"),
        {"rid": report_id},
    )
    row = result.mappings().first()
    if not row or str(row["user_id"]) != user_id:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    return dict(row)


def _row_to_response(row: dict) -> ScheduledReportResponse:
    return ScheduledReportResponse(
        id=str(row["id"]),
        name=row["name"],
        frequency=row["frequency"],
        next_run_at=row["next_run_at"],
        last_run_at=row.get("last_run_at"),
        recipient_emails=list(row["recipient_emails"]),
        csv_storage_path=row.get("csv_storage_path"),
        config_json=row.get("config_json"),
        is_active=row["is_active"],
        created_at=row["created_at"],
        template_id=str(row["template_id"]) if row.get("template_id") else None,
        workspace_id=str(row["workspace_id"]) if row.get("workspace_id") else None,
    )


@router.post("/scheduled-reports", response_model=ScheduledReportResponse)
async def create_scheduled_report(
    body: ScheduledReportCreate,
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "SCHEDULED_REPORT_DIAGNOSTIC create attempt — upload_id=%s, user_id=%s (type=%s), user.id=%s",
        body.upload_id,
        str(current_user.id),
        type(current_user.id).__name__,
        current_user.id,
    )
    upload_result = await db.execute(
        text("SELECT id, user_id, source_type FROM uploads WHERE id = :uid"),
        {"uid": body.upload_id},
    )
    upload = upload_result.mappings().first()
    if upload:
        logger.info(
            "SCHEDULED_REPORT_DIAGNOSTIC upload found in DB — upload_id=%s, upload[user_id]=%s (type=%s), str(current_user.id)=%s",
            upload["id"],
            upload["user_id"],
            type(upload["user_id"]).__name__,
            str(current_user.id),
        )
    else:
        logger.warning(
            "SCHEDULED_REPORT_DIAGNOSTIC upload NOT FOUND in DB for upload_id=%s",
            body.upload_id,
        )
    if not upload or str(upload["user_id"]) != str(current_user.id):
        logger.error(
            "SCHEDULED_REPORT_DIAGNOSTIC rejecting — upload_found=%s, "
            "upload[user_id]=%r (type=%s), current_user.id=%r (type=%s), "
            "str(upload[user_id])=%r, str(current_user.id)=%r",
            upload is not None,
            upload["user_id"] if upload else None,
            type(upload["user_id"]).__name__ if upload else "N/A",
            current_user.id,
            type(current_user.id).__name__,
            str(upload["user_id"]) if upload else None,
            str(current_user.id),
        )
        raise HTTPException(status_code=404, detail="Upload not found")

    next_run_at = _compute_next_run(body.frequency)

    result = await db.execute(
        text("""
            INSERT INTO scheduled_reports
                (user_id, template_id, workspace_id, name, frequency,
                 next_run_at, recipient_emails, config_json, is_active)
            VALUES (:user_id, :template_id, :workspace_id, :name, :frequency,
                    :next_run_at, :recipient_emails, :config_json, TRUE)
            RETURNING *
        """),
        {
            "user_id": str(current_user.id),
            "template_id": body.template_id,
            "workspace_id": body.workspace_id,
            "name": body.name,
            "frequency": body.frequency,
            "next_run_at": next_run_at,
            "recipient_emails": body.recipient_emails,
            "config_json": body.config_json,
        },
    )
    await db.commit()

    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create scheduled report")

    scheduled_report_id = str(row["id"])

    file_ext = "csv" if upload.get("source_type", "csv") == "csv" else "xlsx"

    try:
        storage_path = await copy_upload_to_scheduled_source(
            upload_id=body.upload_id,
            scheduled_report_id=scheduled_report_id,
            user_id=str(current_user.id),
            file_ext=file_ext,
        )
        await db.execute(
            text("UPDATE scheduled_reports SET csv_storage_path = :path WHERE id = :rid"),
            {"path": storage_path, "rid": scheduled_report_id},
        )
        await db.commit()
        row = dict(row)
        row["csv_storage_path"] = storage_path
    except Exception as e:
        logger.error("Failed to copy CSV for scheduled report %s: %s", scheduled_report_id, e)
        raise HTTPException(status_code=500, detail="Failed to copy CSV source")

    return _row_to_response(row)


@router.get("/scheduled-reports", response_model=list[ScheduledReportResponse])
async def list_scheduled_reports(
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT * FROM scheduled_reports
            WHERE user_id = :uid
            ORDER BY created_at DESC
        """),
        {"uid": str(current_user.id)},
    )
    rows = result.mappings().all()
    return [_row_to_response(dict(r)) for r in rows]


@router.patch("/scheduled-reports/{report_id}", response_model=ScheduledReportResponse)
async def update_scheduled_report(
    report_id: str,
    body: ScheduledReportUpdate,
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    existing = await _get_scheduled_report_or_404(report_id, str(current_user.id), db)

    updates: dict[str, object] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.frequency is not None:
        updates["frequency"] = body.frequency
        updates["next_run_at"] = _compute_next_run(body.frequency)
    if body.recipient_emails is not None:
        updates["recipient_emails"] = body.recipient_emails
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if body.template_id is not None:
        updates["template_id"] = body.template_id
    if body.config_json is not None:
        updates["config_json"] = body.config_json

    if not updates:
        return _row_to_response(existing)

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["rid"] = report_id

    result = await db.execute(
        text(f"UPDATE scheduled_reports SET {set_clause} WHERE id = :rid RETURNING *"),
        updates,
    )
    await db.commit()

    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to update scheduled report")

    return _row_to_response(dict(row))


@router.delete("/scheduled-reports/{report_id}")
async def delete_scheduled_report(
    report_id: str,
    current_user: User = Depends(require_agency),
    db: AsyncSession = Depends(get_db),
):
    await _get_scheduled_report_or_404(report_id, str(current_user.id), db)

    await db.execute(
        text("DELETE FROM scheduled_reports WHERE id = :rid"),
        {"rid": report_id},
    )
    await db.commit()

    return {"success": True, "message": "Scheduled report deleted"}


# ── Internal: cron-triggered execution ──────────────────────────────


async def _run_all_scheduled_reports() -> None:
    """Runs all due scheduled reports. Called in background from the cron endpoint."""
    logger.info("[scheduler] _run_all_scheduled_reports started")
    try:
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                text("""
                    SELECT * FROM scheduled_reports
                    WHERE next_run_at <= :now AND is_active = TRUE
                    ORDER BY next_run_at ASC
                """),
                {"now": now},
            )
            rows = result.mappings().all()
            logger.info("[scheduler] found %s due reports", len(rows))

            for row in rows:
                sched = dict(row)
                sched_id = str(sched["id"])
                user_id = str(sched["user_id"])
                sched_name = sched["name"]

                try:
                    # 1. Download CSV from storage (permanent path or legacy scheduled-sources)
                    csv_storage_path = sched.get("csv_storage_path")
                    if not csv_storage_path:
                        logger.error("Scheduled report %s has no csv_storage_path — skipping", sched_id)
                        continue
                    if csv_storage_path.startswith("permanent/"):
                        csv_bytes = await _run_sync(
                            _get_supabase().storage.from_("uploads").download,
                            csv_storage_path,
                        )
                    else:
                        filename = csv_storage_path.split("/")[-1]
                        csv_bytes = await _run_sync(
                            _get_supabase().storage.from_("scheduled-sources").download,
                            filename,
                        )

                    # 2. Create a new report record
                    report_id = str(uuid.uuid4())

                    config_raw = sched.get("config_json") or "{}"
                    if isinstance(config_raw, str):
                        try:
                            config = json.loads(config_raw)
                        except (json.JSONDecodeError, TypeError):
                            config = {}
                    else:
                        config = config_raw

                    config.setdefault("template_type", "professional")
                    config.setdefault("sections", [
                        "kpi_overview",
                        "charts",
                        "executive_summary",
                        "insights",
                        "anomalies",
                        "trends",
                        "recommendations",
                        "data_table",
                    ])

                    await db.execute(
                        text("""
                            INSERT INTO reports
                                (id, user_id, title, template_type, status, source_type,
                                 source_filename, config, created_at, updated_at)
                            VALUES (:id, :uid, :title, :template, 'pending', 'csv',
                                    :filename, :config, NOW(), NOW())
                        """),
                        {
                            "id": report_id,
                            "uid": user_id,
                            "title": sched_name,
                            "template": config.get("template_type", "professional"),
                            "filename": f"scheduled/{sched_id}.csv",
                            "config": json.dumps(config),
                        },
                    )
                    await db.commit()

                    # 3. Run the report pipeline
                    await run_report_pipeline(
                        report_id=report_id,
                        user_id=user_id,
                        config=config,
                        csv_bytes=csv_bytes,
                    )

                    # 4. Fetch the completed report to get PDF storage path
                    report_row = await db.execute(
                        text("SELECT pdf_url FROM reports WHERE id = :rid"),
                        {"rid": report_id},
                    )
                    report_data = report_row.mappings().first()

                    if report_data and report_data["pdf_url"]:
                        pdf_bytes = await _run_sync(
                            _get_supabase().storage.from_("reports").download,
                            report_data["pdf_url"],
                        )

                        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

                        # 5. Email PDF to all recipients
                        recipients = list(sched.get("recipient_emails", []))
                        if recipients:
                            send_email(
                                to=recipients,
                                subject=f"{sched_name} — {config.get('brand', {}).get('company_name') or config.get('title') or 'Report'} | {datetime.now().strftime('%d %b %Y')}",
                                html=(
                                    f"<p>Your scheduled report <strong>{sched_name}</strong> "
                                    f"is ready.</p><p>The report PDF is attached.</p>"
                                ),
                                attachments=[{
                                    "filename": f"{sched_name}.pdf",
                                    "content": pdf_b64,
                                }],
                            )

                    # 6. Update next_run_at
                    next_run = _compute_next_run(sched["frequency"])
                    await db.execute(
                        text("""
                            UPDATE scheduled_reports
                            SET last_run_at = :now, next_run_at = :next
                            WHERE id = :rid
                        """),
                        {"now": now, "next": next_run, "rid": sched_id},
                    )
                    await db.commit()

                except Exception as e:
                    logger.error("Failed to process scheduled report %s: %s", sched_id, e)
    except Exception as e:
        logger.error("[scheduler] FATAL ERROR in _run_all_scheduled_reports: %s", e, exc_info=True)


@router.post("/internal/scheduled-reports/run", status_code=202)
async def run_scheduled_reports(
    background_tasks: BackgroundTasks,
    x_cron_secret: str = Header(...),
):
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    background_tasks.add_task(_run_all_scheduled_reports)
    return {"status": "accepted", "message": "Scheduled reports queued"}
