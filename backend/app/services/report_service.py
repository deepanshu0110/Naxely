import asyncio
import concurrent.futures
import json
import os
import time
import logging

import pandas as pd
import sentry_sdk
from fastapi import HTTPException
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.core.supabase_helpers import _get_supabase, _run_sync
from app.services import data_service, chart_service, ai_service, pdf_service
from app.api.deps import increment_report_count, mark_upload_used

logger = logging.getLogger(__name__)

_PDF_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="pdf_worker",
)
_CHART_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="chart_worker",
)

STEP_LABELS = {
    'data': 'Parsing data...',
    'charts': 'Generating charts...',
    'ai': 'Generating AI insights...',
    'pdf': 'Building PDF...',
}


async def update_status(report_id: str, status: str, step: str | None = None, error_message: str | None = None) -> None:
    async with AsyncSessionLocal() as db:
        if step:
            await db.execute(
                text("UPDATE reports SET status = :status, current_step = :step WHERE id = :rid"),
                {"status": status, "step": step, "rid": report_id},
            )
        if error_message is not None:
            await db.execute(
                text("UPDATE reports SET status = :status, error_message = :err WHERE id = :rid"),
                {"status": status, "err": error_message, "rid": report_id},
            )
        await db.commit()


async def get_upload(upload_id: str) -> dict | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT * FROM uploads WHERE id = :uid"),
            {"uid": upload_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None


async def get_user(user_id: str) -> dict | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT * FROM users WHERE id = :uid AND deleted_at IS NULL"),
            {"uid": user_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None


def _has_ai_sections(config: dict) -> bool:
    ai_sections = {"executive_summary", "insights", "anomalies", "trends"}
    sections = set(config.get("sections", []))
    return bool(sections & ai_sections)


async def run_report_pipeline(report_id: str, user_id: str, config: dict, csv_bytes: bytes | None = None) -> None:
    start_time = time.monotonic()

    chart_paths = []
    pdf_path = None
    _use_default_path = csv_bytes is None

    try:
        await update_status(report_id, 'processing', step='data')

        if _use_default_path:
            upload = await get_upload(config["upload_id"])
            if not upload:
                raise ValueError(f"Upload {config['upload_id']} not found")
            file_url = upload["file_url"]

            csv_bytes = await _run_sync(
                _get_supabase().storage.from_("uploads").download, file_url,
            )

        df = data_service.parse_csv(csv_bytes)

        column_config = config.get("column_config", [])
        if column_config:
            df = data_service.apply_column_config(df, column_config)

        column_types = {}
        for cc in column_config:
            if cc.get("include", True):
                col_name = cc.get("display_name") or cc.get("original_name")
                col_type = cc.get("type", "dimension")
                if col_type:
                    column_types[col_name] = col_type

        df_norm = data_service.normalize_for_aggregation(df, column_types)

        config["_raw_null_counts"] = {
            col: int(df[col].isna().sum())
            for col in df.columns
            if column_types.get(col) in ("dimension", "text")
        }

        date_column = next(
            (col for col in df.columns if col.lower() in ['date', 'datetime', 'timestamp', 'time', 'week', 'month', 'year']),
            None
        )
        if not date_column:
            stats = data_service.compute_column_stats(df)
            date_column = stats.get("date_column")
        config["date_column"] = date_column
        logger.info(f"[report_service] detected date_column={date_column!r} all_cols={list(df.columns)}")

        await update_status(report_id, 'processing', step='charts')

        brand_color = (config.get("brand") or {}).get("color") or "#6366F1"
        user_data_row = await get_user(user_id)
        if user_data_row and user_data_row.get("brand_color"):
            brand_color = user_data_row["brand_color"]

        loop = asyncio.get_event_loop()
        chart_paths = await loop.run_in_executor(
            _CHART_EXECUTOR,
            chart_service.generate_sync,
            df_norm, report_id, config, brand_color,
        )

        if _use_default_path:
            try:
                await _run_sync(
                    _get_supabase().storage.from_("uploads").remove, [file_url],
                )
            except Exception:
                logger.warning("Failed to delete CSV from storage: %s", file_url)

        ai_content: dict = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        ai_error: str | None = None
        ai_skipped = False

        if _has_ai_sections(config):
            user_obj = _make_user_proxy(user_data_row or {})
            has_key = bool(user_data_row and user_data_row.get("encrypted_api_key"))

            if has_key:
                await update_status(report_id, 'processing', step='ai')

                try:
                    summary = await ai_service.generate_summary(df_norm, config, user_obj)
                    ai_content["summary"] = summary
                except HTTPException as e:
                    ai_error = str(e.detail) if isinstance(e.detail, str) else str(e.detail)
                    logger.warning("AI summary skipped for %s: %s", report_id, ai_error)
                    ai_skipped = True

                try:
                    insights = await ai_service.generate_nra_insights(df_norm, config, user_obj)
                    ai_content["insights"] = insights
                except HTTPException as e:
                    msg = str(e.detail) if isinstance(e.detail, str) else str(e.detail)
                    ai_error = ai_error or msg
                    logger.warning("AI insights skipped for %s: %s", report_id, msg)
                    ai_skipped = True

                anomalies = ai_service.detect_anomalies(df_norm)
                ai_content["anomalies"] = anomalies

                trends = ai_service.detect_trends(df_norm)
                ai_content["trends"] = trends

        await update_status(report_id, 'processing', step='pdf')

        logo_url = None
        if user_data_row and user_data_row.get("logo_url"):
            try:
                raw_path = user_data_row["logo_url"]
                logo_path_clean = raw_path.removeprefix("logos/")
                logger.info("_get_logo_signed_url: raw_path=%s clean_path=%s", raw_path, logo_path_clean)
                def _sync_signed():
                    return _get_supabase().storage.from_("logos").create_signed_url(logo_path_clean, 3600)
                signed = await _run_sync(_sync_signed)
                logo_url = signed.get("signedURL", signed.get("signedUrl", ""))
                logger.info(f"[report_service] logo signed URL result: raw={raw_path!r} clean={logo_path_clean!r} url={logo_url!r}")
            except Exception:
                logo_url = None

        user_data_dict = {
            "brand_color": brand_color,
            "tier": user_data_row.get("tier", "free") if user_data_row else "free",
            "logo_url": logo_url,
            "company_name": (user_data_row.get("company_name") if user_data_row else None),
        }

        kpis = await loop.run_in_executor(
            None,
            pdf_service._compute_kpi_data,
            df_norm, config, ai_content, brand_color,
        )

        pdf_config = dict(config)
        pdf_config["report_id"] = report_id
        pdf_config["_precomputed_kpis"] = kpis
        pdf_config["_ai_skipped"] = ai_skipped

        pdf_path = await loop.run_in_executor(
            _PDF_EXECUTOR,
            pdf_service.build_sync,
            df, chart_paths, ai_content, pdf_config, user_data_dict,
        )

        storage_path = f"reports/{user_id}/{report_id}/report.pdf"
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        await _run_sync(
            _get_supabase().storage.from_("reports").upload, storage_path, pdf_bytes,
            {"content-type": "application/pdf"},
        )

        if _use_default_path:
            async with AsyncSessionLocal() as db:
                await mark_upload_used(config["upload_id"], db)

        async with AsyncSessionLocal() as db:
            await increment_report_count(user_id, db)

        elapsed = round(time.monotonic() - start_time, 1)

        metric_cols = config.get('metric_columns') or [
            c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
        ]
        trend_pct = 0.0
        if metric_cols:
            metric = metric_cols[0]
            series = pd.to_numeric(df[metric], errors='coerce').dropna()
            if len(series) >= 2:
                first = series.iloc[0]
                last = series.iloc[-1]
                if first != 0:
                    trend_pct = round(((last - first) / abs(first)) * 100, 2)

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    UPDATE reports SET
                        status = 'completed',
                        pdf_url = :pdf_url,
                        ai_summary = :ai_summary,
                        ai_insights = :ai_insights,
                        ai_anomalies = :ai_anomalies,
                        generation_time_seconds = :gen_time,
                        row_count = :row_count,
                        column_count = :col_count,
                        trend_pct = :trend_pct,
                        ai_skipped = :ai_skipped,
                        error_message = :ai_err
                    WHERE id = :rid
                """),
                {
                    "pdf_url": storage_path,
                    "ai_summary": ai_content.get("summary"),
                    "ai_insights": json.dumps(ai_content.get("insights") or []),
                    "ai_anomalies": json.dumps(ai_content.get("anomalies") or []),
                    "gen_time": elapsed,
                    "row_count": len(df),
                    "col_count": len(df.columns),
                    "trend_pct": trend_pct,
                    "ai_skipped": ai_skipped,
                    "ai_err": ai_error,
                    "rid": report_id,
                },
            )
            await db.commit()

    except Exception as e:
        elapsed = round(time.monotonic() - start_time, 1)
        error_msg = str(e)

        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    text("UPDATE reports SET status = 'failed', error_message = :err WHERE id = :rid"),
                    {"err": error_msg, "rid": report_id},
                )
                await db.commit()
        except Exception:
            logger.error("Failed to update report status to failed for %s", report_id)

        sentry_sdk.capture_exception(e)
        logger.error("Report pipeline failed for %s", report_id, exc_info=True)

    finally:
        try:
            if chart_paths:
                chart_service.cleanup_charts(report_id)
        except Exception:
            logger.warning("Failed to clean up chart temp files for %s", report_id)

        try:
            if pdf_path and os.path.isfile(pdf_path):
                os.unlink(pdf_path)
        except Exception:
            logger.warning("Failed to clean up PDF temp file for %s", report_id)


def _make_user_proxy(user_data: dict):
    from app.models.user import User
    user = User()
    for key, value in user_data.items():
        try:
            setattr(user, key, value)
        except Exception:
            pass
    return user
