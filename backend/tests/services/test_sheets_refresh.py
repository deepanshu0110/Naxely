"""Tests for Google Sheets live refresh (Phase 2).

Covers all 4 insertion points:
1. _store_csv_upload persists sheets_url
2. upload_sheets passes sheets_url through
3. run_report_pipeline: fresh fetch + fallback + data_source_stale flag
4. create_scheduled_report persists sheets_url from upload
5. _run_all_scheduled_reports: fresh fetch + fallback
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_CSV = b"col_a,col_b\n1,2\n3,4\n"
SAMPLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/abc123/edit"


class FakeSync:
    @staticmethod
    def generate_sync(*a, **kw):
        return []

    @staticmethod
    def build_sync(*a, **kw):
        import tempfile
        f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        f.write(b"%PDF-1.4...")
        f.close()
        return f.name

    @staticmethod
    def _compute_kpi_data(*a, **kw):
        return {}

    @staticmethod
    def cleanup_charts(*a, **kw):
        pass


fake_chart = type("FakeChart", (), {
    "generate_sync": FakeSync.generate_sync,
    "cleanup_charts": FakeSync.cleanup_charts,
})
fake_pdf = type("FakePdf", (), {
    "build_sync": FakeSync.build_sync,
    "_compute_kpi_data": FakeSync._compute_kpi_data,
})


# ── Insertion Point 1: _store_csv_upload persists sheets_url ─────────────────

class TestStoreCsvUploadSheetsUrl:
    """Verify sheets_url is written into the DB and returned."""

    @pytest.mark.asyncio
    async def test_persists_sheets_url(self):
        import app.api.routes.reports as routes
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": "test-uuid",
            "file_url": "uploads/test.csv",
            "columns_meta": None,
        }
        mock_db.execute.return_value = mock_result

        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        with (
            patch.object(routes, "_run_sync", new_callable=AsyncMock),
            patch.object(routes, "_get_supabase"),
        ):
            result = await routes._store_csv_upload(
                db=mock_db,
                user_id="user-1",
                csv_bytes=SAMPLE_CSV,
                source_type="sheets",
                filename="test",
                df=df,
                sheets_url=SAMPLE_SHEETS_URL,
            )

        assert result["sheets_url"] == SAMPLE_SHEETS_URL

        call_params = mock_db.execute.call_args[0][1]
        assert call_params["sheets_url"] == SAMPLE_SHEETS_URL

    @pytest.mark.asyncio
    async def test_defaults_to_none_when_omitted(self):
        import app.api.routes.reports as routes
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": "test-uuid-2",
            "file_url": "uploads/test.csv",
            "columns_meta": None,
        }
        mock_db.execute.return_value = mock_result

        df = pd.DataFrame({"a": [1]})

        with (
            patch.object(routes, "_run_sync", new_callable=AsyncMock),
            patch.object(routes, "_get_supabase"),
        ):
            result = await routes._store_csv_upload(
                db=mock_db,
                user_id="user-2",
                csv_bytes=SAMPLE_CSV,
                source_type="csv",
                filename="test.csv",
                df=df,
            )

        call_params = mock_db.execute.call_args[0][1]
        assert call_params["sheets_url"] is None


# ── Insertion Point 2: upload_sheets passes sheets_url through ───────────────

class TestUploadSheetsSheetsUrl:
    """Verify the /upload-sheets endpoint propagates sheets_url."""

    @pytest.mark.asyncio
    async def test_upload_sheets_returns_sheets_url(self):
        from app.api.routes import reports as routes

        mock_db = MagicMock()
        fake_df = pd.DataFrame({"greeting": ["hello"]})

        with (
            patch.object(routes, "_store_csv_upload", new_callable=AsyncMock) as mock_store,
            patch.object(routes.sheets_service, "fetch_sheet_as_df", return_value=fake_df),
            patch.object(routes.sheets_service, "extract_sheet_id", return_value="abc123"),
            patch.object(routes.sheets_service, "build_credentials", return_value=MagicMock()),
            patch.object(routes, "settings") as mock_settings,
            patch.object(routes, "validate_csv"),
            patch.object(routes, "validate_for_injection"),
        ):
            mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = '{"fake": "creds"}'
            mock_store.return_value = {
                "id": "upload-sheets-test-1",
                "file_url": "uploads/sheets_test.csv",
                "columns": [],
            }

            from app.models.user import User
            user = User()
            user.id = "user-sheets-1"
            user.tier = "agency"

            result = await routes.upload_sheets(
                sheets_data={"sheets_url": SAMPLE_SHEETS_URL},
                current_user=user,
                db=mock_db,
            )

            assert result["success"] is True
            assert result["data"]["sheets_url"] == SAMPLE_SHEETS_URL
            mock_store.assert_awaited_once()
            kw = mock_store.call_args[1]
            assert kw["sheets_url"] == SAMPLE_SHEETS_URL


# ── Insertion Point 3: run_report_pipeline — live fetch / fallback ────────────

class TestRunReportPipelineSheetsUrl:
    """run_report_pipeline with upload having sheets_url."""

    @pytest.mark.asyncio
    async def test_sheets_url_triggers_live_fetch(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        mock_db = AsyncMock()
        mock_db.__aenter__.return_value = mock_db

        fresh_df = pd.DataFrame({"metric": [100, 200], "date": ["2026-01", "2026-02"]})

        with (
            patch.object(svc, "get_upload", new_callable=AsyncMock) as mock_get_upload,
            patch.object(svc, "_get_supabase"),
            patch.object(svc, "mark_upload_used", new_callable=AsyncMock),
            patch.object(svc, "update_status"),
            patch.object(svc, "AsyncSessionLocal", return_value=mock_db),
            patch.object(svc, "data_service") as mock_data,
            patch.object(svc, "chart_service", fake_chart),
            patch.object(svc, "pdf_service", fake_pdf),
            patch.object(svc, "ai_service"),
            patch.object(svc, "get_user", return_value=None),
            patch.object(svc, "sheets_service") as mock_sheets,
            patch.object(svc, "settings") as mock_settings,
            patch("builtins.open"),
        ):
            mock_get_upload.return_value = {
                "file_url": "uploads/stale.csv",
                "sheets_url": SAMPLE_SHEETS_URL,
            }
            mock_sheets.extract_sheet_id.return_value = "abc123"
            mock_sheets.build_credentials.return_value = MagicMock()
            mock_sheets.fetch_sheet_as_df.return_value = fresh_df
            mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = "{}"

            mock_data.parse_csv.return_value = fresh_df
            mock_data.normalize_for_aggregation.return_value = fresh_df

            await run_report_pipeline(
                report_id="report-sheets-1",
                user_id="user-1",
                config={"upload_id": "upl-sheets-1", "sections": ["charts"]},
                csv_bytes=None,
            )

            mock_sheets.fetch_sheet_as_df.assert_called_once_with(
                "abc123", mock_sheets.build_credentials.return_value
            )
            update_params = mock_db.execute.call_args_list[-2][0][1]
            assert update_params["stale"] is False

    @pytest.mark.asyncio
    async def test_sheets_fetch_failure_falls_back(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        mock_db = AsyncMock()
        mock_db.__aenter__.return_value = mock_db

        with (
            patch.object(svc, "get_upload", new_callable=AsyncMock) as mock_get_upload,
            patch.object(svc, "_get_supabase"),
            patch.object(svc, "_run_sync", return_value=b"stale,a\n1\n") as mock_run_sync,
            patch.object(svc, "mark_upload_used", new_callable=AsyncMock),
            patch.object(svc, "update_status"),
            patch.object(svc, "AsyncSessionLocal", return_value=mock_db),
            patch.object(svc, "data_service") as mock_data,
            patch.object(svc, "chart_service", fake_chart),
            patch.object(svc, "pdf_service", fake_pdf),
            patch.object(svc, "ai_service"),
            patch.object(svc, "get_user", return_value=None),
            patch.object(svc, "sheets_service") as mock_sheets,
            patch.object(svc, "settings") as mock_settings,
            patch("builtins.open"),
        ):
            mock_get_upload.return_value = {
                "file_url": "uploads/stale.csv",
                "sheets_url": SAMPLE_SHEETS_URL,
            }
            mock_sheets.extract_sheet_id.return_value = "abc123"
            mock_sheets.build_credentials.return_value = MagicMock()
            mock_sheets.fetch_sheet_as_df.side_effect = RuntimeError("API down")
            mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = "{}"

            stale_df = pd.DataFrame({"a": [1]})
            mock_data.parse_csv.return_value = stale_df
            mock_data.normalize_for_aggregation.return_value = stale_df

            await run_report_pipeline(
                report_id="report-fallback-1",
                user_id="user-1",
                config={"upload_id": "upl-sheets-2", "sections": ["charts"]},
                csv_bytes=None,
            )

            mock_run_sync.assert_called()
            update_params = mock_db.execute.call_args_list[-2][0][1]
            assert update_params["stale"] is True

    @pytest.mark.asyncio
    async def test_no_sheets_url_skips_live_fetch(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        mock_db = AsyncMock()
        mock_db.__aenter__.return_value = mock_db

        with (
            patch.object(svc, "get_upload", new_callable=AsyncMock) as mock_get_upload,
            patch.object(svc, "_get_supabase"),
            patch.object(svc, "_run_sync", return_value=b"a,b\n1,2\n"),
            patch.object(svc, "mark_upload_used", new_callable=AsyncMock),
            patch.object(svc, "update_status"),
            patch.object(svc, "AsyncSessionLocal", return_value=mock_db),
            patch.object(svc, "data_service") as mock_data,
            patch.object(svc, "chart_service", fake_chart),
            patch.object(svc, "pdf_service", fake_pdf),
            patch.object(svc, "ai_service"),
            patch.object(svc, "get_user", return_value=None),
            patch.object(svc, "sheets_service") as mock_sheets,
            patch("builtins.open"),
        ):
            mock_get_upload.return_value = {
                "file_url": "uploads/normal.csv",
                "sheets_url": None,
            }

            df = pd.DataFrame({"a": [1]})
            mock_data.parse_csv.return_value = df
            mock_data.normalize_for_aggregation.return_value = df

            await run_report_pipeline(
                report_id="report-no-sheets",
                user_id="user-1",
                config={"upload_id": "upl-normal", "sections": ["charts"]},
                csv_bytes=None,
            )

            mock_sheets.fetch_sheet_as_df.assert_not_called()


# ── Insertion Point 4: create_scheduled_report persists sheets_url ───────────

class TestCreateScheduledReportSheetsUrl:
    """Verify scheduled report creation persists sheets_url from source upload."""

    @pytest.mark.asyncio
    async def test_persists_sheets_url_from_upload(self):
        from app.api.routes.scheduled_reports import create_scheduled_report
        from app.api.routes.scheduled_reports import ScheduledReportCreate
        from app.core.database import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": "sched-insert-1",
            "name": "Weekly Sheets Report",
            "frequency": "weekly",
            "next_run_at": datetime.now(timezone.utc),
            "recipient_emails": ["a@b.com"],
            "csv_storage_path": "permanent/user-1/test.csv",
            "config_json": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "template_id": None,
            "workspace_id": None,
            "user_id": "user-1",
            "sheets_url": SAMPLE_SHEETS_URL,
        }

        mock_second = MagicMock()
        mock_second.mappings.return_value.first.return_value = {
            "id": "sched-insert-2",
            "name": "Weekly Sheets Report",
        }

        mock_db.execute.side_effect = [
            mock_result,   # SELECT upload lookup
            mock_result,   # INSERT scheduled_reports
            mock_second,   # UPDATE csv_storage_path
        ]

        from app.models.user import User
        user = User()
        user.id = "user-1"
        user.tier = "agency"

        body = ScheduledReportCreate(
            upload_id="upl-1",
            name="Weekly Sheets Report",
            frequency="weekly",
            recipient_emails=["a@b.com"],
        )

        with (
            patch("app.api.routes.scheduled_reports.copy_upload_to_scheduled_source",
                  new_callable=AsyncMock, return_value="permanent/user-1/test.csv"),
        ):
            result = await create_scheduled_report(
                body=body,
                current_user=user,
                db=mock_db,
            )

            assert result.sheets_url == SAMPLE_SHEETS_URL


# ── Insertion Point 5: _run_all_scheduled_reports — live fetch / fallback ────

class TestRunAllScheduledReportsSheetsUrl:
    """_run_all_scheduled_reports with sheets_url on scheduled report."""

    @pytest.mark.asyncio
    async def test_sheets_url_triggers_live_fetch(self):
        from app.api.routes.scheduled_reports import _run_all_scheduled_reports
        import app.api.routes.scheduled_reports as sched_mod

        fresh_df = pd.DataFrame({"val": [10, 20]})

        with (
            patch.object(sched_mod, "AsyncSessionLocal") as mock_session_cls,
            patch.object(sched_mod, "run_report_pipeline", new_callable=AsyncMock) as mock_pipeline,
            patch.object(sched_mod, "_get_supabase"),
            patch.object(sched_mod, "send_email", new_callable=AsyncMock),
            patch.object(sched_mod.sheets_service, "extract_sheet_id", return_value="abc123"),
            patch.object(sched_mod.sheets_service, "build_credentials", return_value=MagicMock()),
            patch.object(sched_mod.sheets_service, "fetch_sheet_as_df", return_value=fresh_df),
            patch.object(sched_mod, "settings") as mock_settings,
        ):
            mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = "{}"

            mock_db = AsyncMock()
            mock_db.__aenter__.return_value = mock_db
            mock_session_cls.return_value = mock_db

            due_row = {
                "id": "sched-1",
                "user_id": "user-1",
                "name": "Auto Sheet Report",
                "csv_storage_path": "permanent/user-1/old.csv",
                "sheets_url": SAMPLE_SHEETS_URL,
                "config_json": json.dumps({"template_type": "professional", "sections": ["charts"]}),
                "is_active": True,
            }

            mock_fetch = MagicMock()
            mock_fetch.mappings.return_value.all.return_value = [due_row]
            mock_fetch.mappings.return_value.first.return_value = None
            mock_db.execute.return_value = mock_fetch

            await _run_all_scheduled_reports()

            mock_pipeline.assert_awaited_once()
            args, kwargs = mock_pipeline.call_args
            assert kwargs["csv_bytes"] == fresh_df.to_csv(index=False).encode("utf-8")

    @pytest.mark.asyncio
    async def test_sheets_fetch_failure_falls_back_to_storage(self):
        from app.api.routes.scheduled_reports import _run_all_scheduled_reports
        import app.api.routes.scheduled_reports as sched_mod

        with (
            patch.object(sched_mod, "AsyncSessionLocal") as mock_session_cls,
            patch.object(sched_mod, "run_report_pipeline", new_callable=AsyncMock) as mock_pipeline,
            patch.object(sched_mod, "_get_supabase"),
            patch.object(sched_mod, "send_email", new_callable=AsyncMock),
            patch.object(sched_mod.sheets_service, "extract_sheet_id", return_value="abc123"),
            patch.object(sched_mod.sheets_service, "build_credentials", return_value=MagicMock()),
            patch.object(sched_mod.sheets_service, "fetch_sheet_as_df",
                         side_effect=RuntimeError("quota exceeded")),
            patch.object(sched_mod, "settings") as mock_settings,
            patch.object(sched_mod, "_run_sync", return_value=b"stale,data\n1,2\n") as mock_run_sync,
        ):
            mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = "{}"

            mock_db = AsyncMock()
            mock_db.__aenter__.return_value = mock_db
            mock_session_cls.return_value = mock_db

            due_row = {
                "id": "sched-fallback-1",
                "user_id": "user-1",
                "name": "Fallback Sheet",
                "csv_storage_path": "permanent/user-1/old.csv",
                "sheets_url": SAMPLE_SHEETS_URL,
                "config_json": json.dumps({"template_type": "professional", "sections": ["charts"]}),
                "is_active": True,
            }

            mock_fetch = MagicMock()
            mock_fetch.mappings.return_value.all.return_value = [due_row]
            mock_fetch.mappings.return_value.first.return_value = None
            mock_db.execute.return_value = mock_fetch

            await _run_all_scheduled_reports()

            mock_run_sync.assert_called()
            mock_pipeline.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_sheets_url_skips_live_fetch(self):
        from app.api.routes.scheduled_reports import _run_all_scheduled_reports
        import app.api.routes.scheduled_reports as sched_mod

        with (
            patch.object(sched_mod, "AsyncSessionLocal") as mock_session_cls,
            patch.object(sched_mod, "run_report_pipeline", new_callable=AsyncMock) as mock_pipeline,
            patch.object(sched_mod, "_get_supabase"),
            patch.object(sched_mod, "send_email", new_callable=AsyncMock),
            patch.object(sched_mod, "_run_sync", return_value=b"normal,csv\n1,2\n") as mock_run_sync,
        ):
            mock_db = AsyncMock()
            mock_db.__aenter__.return_value = mock_db
            mock_session_cls.return_value = mock_db

            due_row = {
                "id": "sched-no-sheets",
                "user_id": "user-1",
                "name": "Normal CSV",
                "csv_storage_path": "permanent/user-1/data.csv",
                "sheets_url": None,
                "config_json": json.dumps({"template_type": "professional", "sections": ["charts"]}),
                "is_active": True,
            }

            mock_fetch = MagicMock()
            mock_fetch.mappings.return_value.all.return_value = [due_row]
            mock_fetch.mappings.return_value.first.return_value = None
            mock_db.execute.return_value = mock_fetch

            await _run_all_scheduled_reports()

            mock_run_sync.assert_called()
            mock_pipeline.assert_awaited_once()
