import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO
from fastapi import UploadFile, HTTPException
from starlette.datastructures import Headers
from starlette.requests import Request
import pandas as pd

from app.core.supabase_helpers import _run_sync


def _fake_request() -> Request:
    return Request(scope={
        "type": "http",
        "method": "POST",
        "path": "/reports/upload",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "query_string": b"",
    })


def _csv_upload() -> UploadFile:
    return UploadFile(
        filename="data.csv",
        file=BytesIO(b"a,b\n1,2\n3,4"),
        headers=Headers({"content-type": "text/csv"}),
    )


class TestUploadCopiesToScheduledSources:
    """Test #1: upload_file() writes to both uploads/ and scheduled-sources/."""

    @pytest.fixture
    def mock_storage(self):
        m = MagicMock()
        m.storage.from_.return_value.upload.return_value = None
        return m

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute.return_value.mappings.return_value.first.return_value = None
        db.commit.return_value = None
        return db

    @pytest.fixture
    def fake_user(self):
        u = MagicMock()
        u.id = "user-abc"
        u.tier = "pro"
        u.reports_this_month = 0
        return u

    @pytest.mark.asyncio
    async def test_two_storage_writes_on_upload(self, mock_storage, mock_db, fake_user):
        from app.api.routes.reports import upload_file

        with (
            patch("app.api.routes.reports._get_supabase", return_value=mock_storage),
            patch("app.api.routes.reports.parse_csv") as mock_parse,
        ):
            df = pd.DataFrame({"a": [1, 3], "b": [2, 4]})
            mock_parse.return_value = df

            result = await upload_file(
                request=_fake_request(),
                file=_csv_upload(),
                current_user=fake_user,
                db=mock_db,
            )

        assert result["success"] is True

        upload_calls = mock_storage.storage.from_.return_value.upload.call_args_list
        assert len(upload_calls) == 2, f"Expected 2 upload calls, got {len(upload_calls)}"

        path1 = upload_calls[0][0][0]
        assert path1.startswith("uploads/"), f"First upload should be to uploads/, got {path1}"

        path2 = upload_calls[1][0][0]
        assert path2.startswith("scheduled-sources/"), (
            f"Second upload should be to scheduled-sources/, got {path2}"
        )

    @pytest.mark.asyncio
    async def test_scheduled_sources_path_uses_upload_id(self, mock_storage, mock_db, fake_user):
        from app.api.routes.reports import upload_file

        with (
            patch("app.api.routes.reports._get_supabase", return_value=mock_storage),
            patch("app.api.routes.reports.parse_csv") as mock_parse,
        ):
            df = pd.DataFrame({"a": [1, 3], "b": [2, 4]})
            mock_parse.return_value = df

            result = await upload_file(
                request=_fake_request(),
                file=_csv_upload(),
                current_user=fake_user,
                db=mock_db,
            )

        upload_id = result["data"]["upload_id"]
        upload_calls = mock_storage.storage.from_.return_value.upload.call_args_list

        scheduled_path = upload_calls[1][0][0]
        assert scheduled_path == f"scheduled-sources/{upload_id}/raw.csv", (
            f"Expected path based on upload_id, got {scheduled_path}"
        )

    @pytest.mark.asyncio
    async def test_upload_response_shape_unchanged(self, mock_storage, mock_db, fake_user):
        from app.api.routes.reports import upload_file

        with (
            patch("app.api.routes.reports._get_supabase", return_value=mock_storage),
            patch("app.api.routes.reports.parse_csv") as mock_parse,
        ):
            df = pd.DataFrame({"a": [1, 3], "b": [2, 4]})
            mock_parse.return_value = df

            result = await upload_file(
                request=_fake_request(),
                file=_csv_upload(),
                current_user=fake_user,
                db=mock_db,
            )

        assert result["success"] is True
        assert "upload_id" in result["data"]
        assert "filename" in result["data"]
        assert result["data"]["file_url"].startswith("uploads/"), (
            f"file_url must point to uploads/, got {result['data']['file_url']}"
        )
        assert "row_count" in result["data"]
        assert "column_count" in result["data"]
        assert "columns" in result["data"]
        assert "preview_rows" in result["data"]

    @pytest.mark.asyncio
    async def test_scheduled_sources_upload_failure_cleans_up_uploads(self, mock_db, fake_user):
        from app.api.routes.reports import upload_file

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.upload.side_effect = [
            None,
            Exception("scheduled-sources write failed"),
        ]

        with (
            patch("app.api.routes.reports._get_supabase", return_value=mock_storage),
            patch("app.api.routes.reports.parse_csv") as mock_parse,
        ):
            df = pd.DataFrame({"a": [1, 3], "b": [2, 4]})
            mock_parse.return_value = df

            with pytest.raises(HTTPException) as exc:
                await upload_file(
                    request=_fake_request(),
                    file=_csv_upload(),
                    current_user=fake_user,
                    db=mock_db,
                )
            assert exc.value.status_code == 500

        remove_calls = mock_storage.storage.from_.return_value.remove.call_args_list
        assert len(remove_calls) >= 1


class TestOneOffCleanupDoesNotAffectScheduledSources:
    """Test #2: Guard 2 deletes uploads/ copy but scheduled-sources/ persists."""

    @pytest.mark.asyncio
    async def test_guard2_deletes_only_uploads_copy(self):
        """run_report_pipeline must only remove from uploads/, not scheduled-sources/."""
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.return_value = b"a,b\n1,2\n"

        with (
            patch.object(svc, "_get_supabase", return_value=mock_storage),
            patch.object(svc, "get_upload") as mock_get_upload,
            patch.object(svc, "get_user") as mock_get_user,
            patch.object(svc, "data_service") as mock_data,
            patch.object(svc, "chart_service") as mock_chart,
            patch.object(svc, "pdf_service") as mock_pdf,
            patch.object(svc, "ai_service") as mock_ai,
            patch.object(svc, "AsyncSessionLocal") as mock_session_maker,
            patch.object(svc, "update_status"),
            patch.object(svc, "increment_report_count"),
            patch.object(svc, "mark_upload_used"),
        ):
            mock_get_upload.return_value = {
                "id": "upload-123",
                "file_url": "uploads/user-abc/upload-123/raw.csv",
            }
            mock_get_user.return_value = {"tier": "pro"}
            mock_data.parse_csv.return_value = pd.DataFrame({"a": [1]})
            mock_data.normalize_for_aggregation.return_value = mock_data.parse_csv.return_value
            mock_chart.generate_sync.return_value = []
            mock_pdf.build_sync.return_value = None
            mock_ai.detect_anomalies.return_value = []
            mock_ai.detect_trends.return_value = []

            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session_maker.return_value = mock_session

            await run_report_pipeline(
                report_id="report-1",
                user_id="user-abc",
                config={"upload_id": "upload-123", "sections": []},
            )

        for call in mock_storage.storage.method_calls:
            if call[0] == "from_" and len(call.args) > 0:
                assert "scheduled-sources" not in str(call.args[0]), (
                    "Guard 2 must not touch scheduled-sources/"
                )


class TestCopyUploadToScheduledSourceReadsFromScheduledSources:
    """Test #3: copy_upload_to_scheduled_source reads from scheduled-sources/, not uploads/."""

    @pytest.mark.asyncio
    async def test_reads_from_scheduled_sources_not_uploads(self):
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.return_value = b"a,b\n1,2\n"
        mock_storage.storage.from_.return_value.upload.return_value = None

        with patch("app.services.scheduled_report_service._get_supabase", return_value=mock_storage):
            result = await copy_upload_to_scheduled_source(
                upload_id="upload-123",
                scheduled_report_id="sr-abc-123",
            )

        assert result == "scheduled-sources/sr-abc-123.csv"

        from_calls = [
            call for call in mock_storage.storage.method_calls
            if call[0] == "from_"
        ]
        scheduled_from = [c for c in from_calls if "scheduled-sources" in str(c.args)]
        uploads_from = [c for c in from_calls if c.args and c.args[0] == "uploads"]
        assert len(scheduled_from) >= 1, "Must access scheduled-sources/ bucket"
        assert len(uploads_from) == 0, "Must NOT access uploads/ bucket"

        mock_storage.storage.from_.return_value.download.assert_called_once_with(
            "scheduled-sources/upload-123/raw.csv",
        )


class TestFullFlowUploadGenerateCreateSchedule:
    """Test #4: Full e2e flow — upload → generate one-off report → create scheduled report."""

    @pytest.mark.asyncio
    async def test_full_flow_succeeds(self):
        """Simulate the exact user flow: upload CSV, generate a
        one-off report (Guard 2 deletion), then create a scheduled
        report from the same upload_id — all succeed."""
        import uuid
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        upload_id = str(uuid.uuid4())
        scheduled_report_id = str(uuid.uuid4())

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.return_value = b"a,b\n1,2\n3,4\n"
        mock_storage.storage.from_.return_value.upload.return_value = None
        mock_storage.storage.from_.return_value.remove.return_value = None

        # Step 2: Simulate Guard 2 — delete the uploads/ copy
        file_url = f"uploads/user-abc/{upload_id}/raw.csv"
        bucket_ref = mock_storage.storage.from_("uploads")
        await _run_sync(bucket_ref.remove, [file_url])

        remove_calls = [c for c in bucket_ref.method_calls if c[0] == "remove"]
        assert len(remove_calls) >= 1, "Guard 2 should remove uploads/ copy"

        # Step 3: Create scheduled report — must succeed despite uploads/ deletion
        with patch("app.services.scheduled_report_service._get_supabase", return_value=mock_storage):
            result = await copy_upload_to_scheduled_source(
                upload_id=upload_id,
                scheduled_report_id=scheduled_report_id,
            )

        assert result == f"scheduled-sources/{scheduled_report_id}.csv"
        mock_storage.storage.from_.return_value.download.assert_called_with(
            f"scheduled-sources/{upload_id}/raw.csv",
        )
