import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_user, get_db
from app.core.supabase_helpers import _run_sync, _get_supabase
from app.services import data_service
from app.services.report_service import run_report_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["public-api"])


@router.post("/reports", status_code=202)
async def api_create_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV or XLSX file"),
    title: str = Form(...),
    sections: Optional[str] = Form('["kpi","charts","ai_insights","anomalies"]'),
    tone: Optional[str] = Form("professional"),
    current_user=Depends(get_api_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sections_list = json.loads(sections) if isinstance(sections, str) else sections
    except json.JSONDecodeError:
        sections_list = ["kpi", "charts", "ai_insights", "anomalies"]

    content = await file.read()
    try:
        df = data_service.parse_csv(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    if df.empty or len(df.columns) < 2:
        raise HTTPException(
            status_code=422,
            detail="File must have at least 2 columns and 1 data row.",
        )

    from app.api.routes.reports import _store_csv_upload
    upload_record = await _store_csv_upload(
        db=db,
        user_id=str(current_user.id),
        csv_bytes=content,
        source_type="api",
        filename=file.filename or "upload.csv",
        df=df,
    )

    report_id = str(uuid.uuid4())
    config = {
        "upload_id": upload_record["id"],
        "title": title,
        "sections": {s: True for s in sections_list},
        "tone": tone,
        "template_type": "general",
        "column_config": [],
        "chart_specs": None,
    }

    await db.execute(
        text("""
            INSERT INTO reports (id, user_id, title, template_type, status, source_type,
                source_filename, config, created_at, updated_at)
            VALUES (:id, :uid, :title, 'general', 'pending', 'api', :filename, :config, NOW(), NOW())
        """),
        {
            "id": report_id,
            "uid": str(current_user.id),
            "title": title,
            "filename": file.filename or "upload.csv",
            "config": json.dumps(config),
        },
    )
    await db.commit()

    background_tasks.add_task(
        run_report_pipeline,
        report_id=report_id,
        user_id=str(current_user.id),
        config=config,
    )

    return JSONResponse(
        status_code=202,
        content={
            "report_id": report_id,
            "status": "processing",
            "status_url": f"/v1/reports/{report_id}",
            "message": "Report generation started. Poll status_url for completion.",
        },
    )


@router.get("/reports/{report_id}")
async def api_get_report_status(
    report_id: str,
    current_user=Depends(get_api_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM reports WHERE id = :id AND user_id = :uid AND deleted_at IS NULL"),
        {"id": report_id, "uid": str(current_user.id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    response_data = {"report_id": report_id, "status": row["status"]}

    if row["status"] == "completed" and row.get("pdf_url"):
        from app.api.routes.reports import _generate_signed_url
        signed_url = await _generate_signed_url(row["pdf_url"])
        response_data["pdf_url"] = signed_url
        response_data["download_url"] = f"/v1/reports/{report_id}/download"

    if row["status"] == "failed":
        response_data["error"] = row.get("error_message") or "Report generation failed"

    return response_data


@router.get("/reports/{report_id}/download")
async def api_download_report(
    report_id: str,
    current_user=Depends(get_api_user),
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
