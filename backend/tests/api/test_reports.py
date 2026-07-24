import pytest
from app.api.routes.reports import (
    _has_ai_sections,
    ReportGenerateRequest,
    ShareRequest,
    ColumnConfigItem,
    DateRange,
    BrandConfig,
    ChartSpecOverride,
    PreviewChartsRequest,
    BulkDeleteRequest,
)


class TestReportRouteHelpers:
    def test_has_ai_sections_with_exec_summary(self):
        assert _has_ai_sections(["executive_summary"]) is True

    def test_has_ai_sections_with_insights(self):
        assert _has_ai_sections(["insights", "charts"]) is True

    def test_has_ai_sections_without_ai(self):
        assert _has_ai_sections(["charts", "data_table"]) is False

    def test_has_ai_sections_empty(self):
        assert _has_ai_sections([]) is False


class TestDoubleSubmissionGuard:
    @pytest.mark.asyncio
    async def test_duplicate_upload_returns_existing_report(self):
        import json
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks

        from app.api.routes.reports import generate_report
        from app.models.user import User

        user = User()
        user.id = "user-dedup-123"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="upload-duplicate-test",
            title="Dedup Test",
            sections=["charts"],
        )

        existing_report_id = "existing-report-uuid"

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _FoundUpload:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test-filename.csv"
                row.__getitem__.return_value = "test-filename.csv"
                return row

        class _FoundExisting:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.__getitem__.return_value = existing_report_id
                row.get.return_value = existing_report_id
                return row

        class _AsyncDB:
            def __init__(self, results):
                self.results = results
                self.call_count = 0
                self.executed_queries = []

            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                idx = self.call_count
                self.call_count += 1
                if idx < len(self.results):
                    return self.results[idx]
                return MagicMock()

            async def commit(self):
                pass
            async def rollback(self):
                pass

        class _MockBackgroundTasks:
            def add_task(self, *args, **kwargs):
                pass

        scope = {
            "type": "http", "method": "POST", "path": "/reports/generate",
            "headers": [], "query_string": b"",
            "client": ("127.0.0.1", 8000), "scheme": "http",
            "server": ("test", 80), "root_path": "",
        }
        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        request = Request(scope, receive=receive)

        results = [_FoundUpload(), _FoundExisting()]
        db = _AsyncDB(results)

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            resp = await generate_report(
                request=request, body=body,
                background_tasks=_MockBackgroundTasks(),
                current_user=user, db=db,
            )

        assert resp["success"] is True
        assert resp["data"]["report_id"] == existing_report_id
        assert resp["data"]["status"] == "processing"

        dedup_queries = [q for q in db.executed_queries if "upload_id" in q.lower()]
        assert len(dedup_queries) >= 1

    @pytest.mark.asyncio
    async def test_fresh_upload_inserts_new_report(self):
        import uuid
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks

        from app.api.routes.reports import generate_report
        from app.models.user import User

        user = User()
        user.id = "user-fresh-456"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="upload-fresh-test",
            title="Fresh Test",
            sections=["charts"],
        )

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _InsertResult:
            pass

        class _AsyncDB:
            def __init__(self):
                self.call_count = 0
                self.executed_queries = []

            async def execute(self, query, params=None):
                qs = str(query)
                self.executed_queries.append(qs)
                idx = self.call_count
                self.call_count += 1
                if idx == 0:
                    from unittest.mock import MagicMock
                    row = MagicMock()
                    row.get.return_value = "test-filename.csv"
                    row.__getitem__.return_value = "test-filename.csv"
                    result = MagicMock()
                    result.mappings.return_value = result
                    result.first.return_value = row
                    return result
                return _NotFound()

            async def commit(self):
                pass
            async def rollback(self):
                pass

        db = _AsyncDB()

        scope = {
            "type": "http", "method": "POST", "path": "/reports/generate",
            "headers": [], "query_string": b"",
            "client": ("127.0.0.1", 8000), "scheme": "http",
            "server": ("test", 80), "root_path": "",
        }
        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        request = Request(scope, receive=receive)

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            resp = await generate_report(
                request=request, body=body,
                background_tasks=BackgroundTasks(),
                current_user=user, db=db,
            )

        assert resp["success"] is True
        assert resp["data"]["status"] == "processing"
        assert uuid.UUID(resp["data"]["report_id"]) is not None

        inserts = [q for q in db.executed_queries if "INSERT INTO reports" in q]
        assert len(inserts) == 1

    @pytest.mark.asyncio
    async def test_race_concurrent_requests_same_report_id(self):
        import asyncio
        import uuid as uuid_mod
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks
        from sqlalchemy.exc import IntegrityError

        from app.api.routes.reports import generate_report
        from app.models.user import User

        user = User()
        user.id = "user-race-789"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="upload-race-test",
            title="Race Test",
            sections=["charts"],
        )

        known_winner_id = "11111111-2222-3333-4444-555555555555"

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _FoundUpload:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test-filename.csv"
                row.__getitem__.return_value = "test-filename.csv"
                return row

        class _WinnerDB:
            def __init__(self):
                self.call_count = 0
                self.executed_queries = []
                self.committed = False
                self.rolled_back = False

            async def execute(self, query, params=None):
                qs = str(query)
                self.executed_queries.append(qs)
                idx = self.call_count
                self.call_count += 1
                if idx == 0:
                    return _FoundUpload()
                return _NotFound()

            async def commit(self):
                self.committed = True

            async def rollback(self):
                self.rolled_back = True

        class _LoserDB:
            def __init__(self):
                self.call_count = 0
                self.executed_queries = []
                self.committed = False
                self.rolled_back = False

            async def execute(self, query, params=None):
                qs = str(query)
                self.executed_queries.append(qs)
                idx = self.call_count
                self.call_count += 1
                if idx == 0:
                    return _FoundUpload()
                if idx == 1:
                    return _NotFound()
                if "INSERT INTO reports" in qs:
                    raise IntegrityError("duplicate key", {}, None)
                # Winner query - return the known winning report
                row = MagicMock()
                row.__getitem__.return_value = known_winner_id
                row.get.return_value = known_winner_id
                result = MagicMock()
                result.mappings.return_value = result
                result.first.return_value = row
                return result

            async def commit(self):
                self.committed = True

            async def rollback(self):
                self.rolled_back = True

        def make_scope():
            return {
                "type": "http", "method": "POST", "path": "/reports/generate",
                "headers": [], "query_string": b"",
                "client": ("127.0.0.1", 8000), "scheme": "http",
                "server": ("test", 80), "root_path": "",
            }

        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        winner_db = _WinnerDB()
        loser_db = _LoserDB()

        async def call_winner():
            request = Request(make_scope(), receive=receive)
            with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
                with patch("app.api.routes.reports.uuid.uuid4", return_value=uuid_mod.UUID(known_winner_id)):
                    return await generate_report(
                        request=request, body=body,
                        background_tasks=BackgroundTasks(),
                        current_user=user, db=winner_db,
                    )

        async def call_loser():
            request = Request(make_scope(), receive=receive)
            with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
                return await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=loser_db,
                )

        resp_winner, resp_loser = await asyncio.gather(call_winner(), call_loser())

        assert resp_winner["success"] is True
        assert resp_loser["success"] is True
        assert resp_winner["data"]["report_id"] == known_winner_id
        assert resp_loser["data"]["report_id"] == known_winner_id
        assert loser_db.rolled_back

        winner_inserts = [q for q in winner_db.executed_queries if "INSERT INTO reports" in q]
        assert len(winner_inserts) == 1

        loser_inserts = [q for q in loser_db.executed_queries if "INSERT INTO reports" in q]
        assert len(loser_inserts) == 1


class TestPydanticModels:
    def test_report_generate_request_defaults(self):
        req = ReportGenerateRequest(
            upload_id="test-uuid",
            title="Q1 Report",
        )
        assert req.template_type == "marketing"
        assert req.tone == "professional"
        assert req.sections == []
        assert req.column_config == []
        assert req.workspace_id is None

    def test_report_generate_request_with_all_fields(self):
        req = ReportGenerateRequest(
            upload_id="test-uuid",
            title="Q1 Report",
            template_type="financial",
            tone="casual",
            sections=["executive_summary", "charts", "insights"],
            column_config=[
                ColumnConfigItem(original_name="col_1", display_name="Date", type="date", include=True),
                ColumnConfigItem(original_name="col_2", display_name="Revenue", type="metric", include=False),
            ],
            brand=BrandConfig(company_name="Acme", prepared_by="Sarah", color="#1F3864"),
            workspace_id="ws-uuid",
        )
        assert req.template_type == "financial"
        assert len(req.sections) == 3
        assert len(req.column_config) == 2
        assert req.brand.company_name == "Acme"
        assert req.workspace_id == "ws-uuid"

    def test_date_range_by_alias(self):
        dr = DateRange(**{"from": "2024-01-01", "to": "2024-03-31"})
        assert dr.from_ == "2024-01-01"
        assert dr.to == "2024-03-31"

    def test_share_request_defaults(self):
        req = ShareRequest()
        assert req.expires_days == 30
        assert req.password is None

    def test_column_config_item_defaults(self):
        item = ColumnConfigItem(original_name="col_1")
        assert item.include is True
        assert item.display_name is None
        assert item.type is None


class TestSharedReportIsWhiteLabel:
    """GET /share/{token} must return is_white_label matching the report owner's tier."""

    @pytest.fixture
    def row_cls(self):
        class _Row:
            def __init__(self, **kw):
                self._kw = kw
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
        return _Row

    @pytest.fixture
    def not_found(self):
        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None
        return _NotFound()

    @pytest.fixture
    def asyncdb(self, not_found):
        class _AsyncDB:
            def __init__(self, results):
                self.results = results
                self.call_count = 0
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                idx = self.call_count
                self.call_count += 1
                if idx < len(self.results):
                    return self.results[idx]
                return not_found
            async def commit(self):
                pass
            async def rollback(self):
                pass
        return _AsyncDB

    @pytest.mark.asyncio
    async def test_agency_user_share_returns_is_white_label_true(self, row_cls, asyncdb):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_shared_report

        row = row_cls(
            id="rep-agency-001",
            title="Agency Q3 Report",
            status="completed",
            template_type="marketing",
            user_tier="agency",
            pdf_url="reports/agency/report.pdf",
            share_expires_at=None,
            ai_summary=None,
            ai_insights=None,
            ai_anomalies=None,
            created_at=datetime(2026, 7, 1, 12, 0, 0),
        )

        db = asyncdb([row, MagicMock()])

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"):
            result = await get_shared_report(share_token="agency-token", db=db)

        assert result["success"] is True
        assert result["data"]["is_white_label"] is True

    @pytest.mark.asyncio
    async def test_pro_user_share_returns_is_white_label_false(self, row_cls, asyncdb):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_shared_report

        row = row_cls(
            id="rep-pro-002",
            title="Pro Marketing Report",
            status="completed",
            template_type="financial",
            user_tier="pro",
            pdf_url="reports/pro/report.pdf",
            share_expires_at=None,
            ai_summary=None,
            ai_insights=None,
            ai_anomalies=None,
            created_at=datetime(2026, 6, 15, 12, 0, 0),
        )

        db = asyncdb([row, MagicMock()])

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"):
            result = await get_shared_report(share_token="pro-token", db=db)

        assert result["success"] is True
        assert result["data"]["is_white_label"] is False

    @pytest.mark.asyncio
    async def test_free_user_share_returns_is_white_label_false(self, row_cls, asyncdb):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_shared_report

        row = row_cls(
            id="rep-free-003",
            title="Free Report",
            status="completed",
            template_type="marketing",
            user_tier="free",
            pdf_url="reports/free/report.pdf",
            share_expires_at=None,
            ai_summary=None,
            ai_insights=None,
            ai_anomalies=None,
            created_at=datetime(2026, 5, 1, 12, 0, 0),
        )

        db = asyncdb([row, MagicMock()])

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"):
            result = await get_shared_report(share_token="free-token", db=db)

        assert result["success"] is True
        assert result["data"]["is_white_label"] is False

    @pytest.mark.asyncio
    async def test_future_share_expiry_returns_report(self, row_cls, asyncdb):
        """tz-aware future share_expires_at does NOT raise 410 — report renders."""
        from unittest.mock import MagicMock, patch
        from datetime import datetime, timedelta, timezone
        from app.api.routes.reports import get_shared_report

        row = row_cls(
            id="rep-future-004",
            title="Future Expiry Report",
            status="completed",
            template_type="marketing",
            user_tier="pro",
            pdf_url="reports/future/report.pdf",
            share_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            ai_summary=None,
            ai_insights=None,
            ai_anomalies=None,
            created_at=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        db = asyncdb([row, MagicMock()])

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"):
            result = await get_shared_report(share_token="future-token", db=db)

        assert result["success"] is True
        assert result["data"]["id"] == "rep-future-004"
        assert result["data"]["is_white_label"] is False

    @pytest.mark.asyncio
    async def test_past_share_expiry_returns_410(self, row_cls, asyncdb):
        """tz-aware past share_expires_at returns 410 (not TypeError 500)."""
        from unittest.mock import MagicMock
        from datetime import datetime, timedelta, timezone
        from fastapi import HTTPException
        import pytest
        from app.api.routes.reports import get_shared_report

        row = row_cls(
            id="rep-past-005",
            title="Past Expiry Report",
            status="completed",
            template_type="marketing",
            user_tier="pro",
            pdf_url="reports/past/report.pdf",
            share_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            ai_summary=None,
            ai_insights=None,
            ai_anomalies=None,
            created_at=datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        db = asyncdb([row])

        with pytest.raises(HTTPException) as exc:
            await get_shared_report(share_token="past-token", db=db)

        assert exc.value.status_code == 410
        assert "expired" in exc.value.detail.lower()


class TestChartSpecOverride:
    def test_chart_spec_override_fields(self):
        spec = ChartSpecOverride(x="Date", y="Revenue", type="area", title="Revenue Area")
        assert spec.x == "Date"
        assert spec.y == "Revenue"
        assert spec.type == "area"
        assert spec.title == "Revenue Area"

    def test_report_generate_request_with_chart_specs(self):
        req = ReportGenerateRequest(
            upload_id="test-uuid",
            title="Chart Spec Test",
            sections=["charts"],
            chart_specs=[
                ChartSpecOverride(x="Date", y="Revenue", type="bar", title="Rev by Date"),
                ChartSpecOverride(x="Month", y="Users", type="line", title="Users over Time"),
            ],
        )
        assert len(req.chart_specs) == 2
        assert req.chart_specs[0].type == "bar"
        assert req.chart_specs[1].x == "Month"

    def test_chart_specs_defaults_to_none(self):
        req = ReportGenerateRequest(upload_id="u", title="No Specs")
        assert req.chart_specs is None

    def test_preview_charts_request_model(self):
        req = PreviewChartsRequest(
            upload_id="upload-123",
            column_config=[
                ColumnConfigItem(original_name="col_a", type="date", include=True),
            ],
        )
        assert req.upload_id == "upload-123"
        assert len(req.column_config) == 1
        assert req.column_config[0].original_name == "col_a"

    def test_preview_charts_request_column_config_defaults(self):
        req = PreviewChartsRequest(upload_id="upload-123")
        assert req.column_config is None


class TestBulkDelete:
    def test_bulk_delete_request_model(self):
        req = BulkDeleteRequest(report_ids=["id-1", "id-2"])
        assert len(req.report_ids) == 2
        assert req.report_ids == ["id-1", "id-2"]

    def test_bulk_delete_request_empty_list(self):
        req = BulkDeleteRequest(report_ids=[])
        assert req.report_ids == []

    def test_bulk_delete_request_max_50_rejected(self):
        import uuid
        import json
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import HTTPException
        from app.api.routes.reports import bulk_delete_reports
        from app.models.user import User

        user = User()
        user.id = "bulk-test-user"
        user.tier = "pro"
        user.is_active = True

        body = BulkDeleteRequest(report_ids=[str(uuid.uuid4()) for _ in range(51)])

        db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(bulk_delete_reports(body=body, current_user=user, db=db))
            finally:
                loop.close()
        assert exc.value.status_code == 400
        assert "50" in exc.value.detail


class TestSendReportToClient:
    def test_send_report_request_valid(self):
        from app.api.routes.reports import SendReportRequest
        req = SendReportRequest(recipients=["a@test.com", "b@test.com"])
        assert len(req.recipients) == 2
        assert req.message is None

    def test_send_report_request_with_message(self):
        from app.api.routes.reports import SendReportRequest
        req = SendReportRequest(recipients=["a@test.com"], message="Here is your report")
        assert req.message == "Here is your report"

    def test_send_report_request_invalid_email_rejected(self):
        from pydantic import ValidationError
        from app.api.routes.reports import SendReportRequest
        with pytest.raises(ValidationError):
            SendReportRequest(recipients=["not-an-email"])

    def test_send_report_request_empty_recipients_rejected(self):
        from pydantic import ValidationError
        from app.api.routes.reports import SendReportRequest
        with pytest.raises(ValidationError):
            SendReportRequest(recipients=[])

    @pytest.mark.asyncio
    async def test_send_success(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import HTTPException
        from app.api.routes.reports import send_report_to_client, SendReportRequest
        from app.models.user import User

        user = User()
        user.id = "send-test-user"
        user.tier = "pro"
        user.is_active = True
        user.company_name = "Acme Co"
        user.email = "user@acme.com"

        body = SendReportRequest(recipients=["client@example.com"], message="Great report!")

        class _FoundReport:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.__getitem__ = lambda self_, key: {
                    "id": "report-send-1",
                    "title": "Q1 Report",
                    "pdf_url": "reports/send-test-user/report-send-1/report.pdf",
                    "user_id": "send-test-user",
                }.get(key)
                return row

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _FoundReport()
            async def commit(self):
                pass

        db = _AsyncDB()

        with (
            patch("app.api.routes.reports._get_supabase"),
            patch("app.api.routes.reports._run_sync", return_value=b"fake-pdf-content"),
            patch("app.api.routes.reports.send_email", return_value=True) as mock_email,
        ):
            result = await send_report_to_client(
                report_id="report-send-1",
                payload=body,
                current_user=user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["sent"] is True
        assert result["data"]["recipients"] == 1
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        assert call_args[1]["to"] == ["client@example.com"]
        assert call_args[1]["subject"] == "Q1 Report — from Acme Co"
        assert len(call_args[1]["attachments"]) == 1
        assert call_args[1]["attachments"][0]["filename"] == "Q1 Report.pdf"

    @pytest.mark.asyncio
    async def test_send_report_not_found(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import send_report_to_client, SendReportRequest
        from app.models.user import User

        user = User()
        user.id = "send-test-user"
        user.tier = "pro"
        user.is_active = True

        body = SendReportRequest(recipients=["c@test.com"])

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _NotFound()
            async def commit(self):
                pass

        db = _AsyncDB()

        with (
            patch("app.api.routes.reports._run_sync"),
            patch("app.api.routes.reports.send_email"),
        ):
            with pytest.raises(HTTPException) as exc:
                await send_report_to_client(
                    report_id="nonexistent", payload=body, current_user=user, db=db,
                )
        assert exc.value.status_code == 404
        assert "Report not found" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_send_other_users_report_rejected(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import send_report_to_client, SendReportRequest
        from app.models.user import User

        user = User()
        user.id = "other-user"
        user.tier = "pro"
        user.is_active = True

        body = SendReportRequest(recipients=["c@test.com"])

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _NotFound()
            async def commit(self):
                pass

        db = _AsyncDB()

        with (
            patch("app.api.routes.reports._run_sync"),
            patch("app.api.routes.reports.send_email"),
        ):
            with pytest.raises(HTTPException) as exc:
                await send_report_to_client(
                    report_id="someone-elses-report", payload=body, current_user=user, db=db,
                )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_send_missing_pdf_rejected(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import send_report_to_client, SendReportRequest
        from app.models.user import User

        user = User()
        user.id = "send-test-user"
        user.tier = "pro"
        user.is_active = True

        body = SendReportRequest(recipients=["c@test.com"])

        class _NoPdfReport:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.__getitem__ = lambda self_, key: {
                    "id": "report-no-pdf",
                    "title": "No PDF",
                    "pdf_url": None,
                    "user_id": "send-test-user",
                }.get(key)
                row.get.return_value = None
                return row

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _NoPdfReport()
            async def commit(self):
                pass

        db = _AsyncDB()

        with (
            patch("app.api.routes.reports._run_sync"),
            patch("app.api.routes.reports.send_email"),
        ):
            with pytest.raises(HTTPException) as exc:
                await send_report_to_client(
                    report_id="report-no-pdf", payload=body, current_user=user, db=db,
                )
        assert exc.value.status_code == 409
        assert "no pdf" in str(exc.value.detail).lower()

    @pytest.mark.asyncio
    async def test_send_failed_email_returns_502(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import send_report_to_client, SendReportRequest
        from app.models.user import User

        user = User()
        user.id = "send-test-user"
        user.tier = "pro"
        user.is_active = True
        user.company_name = "Co"

        body = SendReportRequest(recipients=["c@test.com"])

        class _FoundReport:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.__getitem__ = lambda self_, key: {
                    "id": "report-send-2",
                    "title": "Test",
                    "pdf_url": "reports/send-test-user/report-send-2/report.pdf",
                    "user_id": "send-test-user",
                }.get(key)
                return row

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _FoundReport()
            async def commit(self):
                pass

        db = _AsyncDB()

        with (
            patch("app.api.routes.reports._get_supabase"),
            patch("app.api.routes.reports._run_sync", return_value=b"fake-pdf"),
            patch("app.api.routes.reports.send_email", return_value=False),
        ):
            with pytest.raises(HTTPException) as exc:
                await send_report_to_client(
                    report_id="report-send-2", payload=body, current_user=user, db=db,
                )
        assert exc.value.status_code == 502
        assert "Failed to send" in exc.value.detail


class TestGenerateReportErrors:
    @pytest.mark.asyncio
    async def test_invalid_upload_id_returns_404(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import generate_report
        from app.models.user import User

        user = User()
        user.id = "user-err-001"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="nonexistent-upload",
            title="Error Test",
            sections=["charts"],
        )

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _NotFound()
            async def commit(self):
                pass
            async def rollback(self):
                pass

        db = _AsyncDB()

        scope = {
            "type": "http", "method": "POST", "path": "/reports/generate",
            "headers": [], "query_string": b"",
            "client": ("127.0.0.1", 8000), "scheme": "http",
            "server": ("test", 80), "root_path": "",
        }
        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        request = Request(scope, receive=receive)

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            with pytest.raises(HTTPException) as exc:
                await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=db,
                )

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_ai_sections_gate_free_user(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import generate_report
        from app.models.user import User

        user = User()
        user.id = "user-err-002"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="upload-ai-gate",
            title="AI Gate Test",
            sections=["executive_summary"],
        )

        class _FoundUpload:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _FoundUpload()
            async def commit(self):
                pass
            async def rollback(self):
                pass

        db = _AsyncDB()

        scope = {
            "type": "http", "method": "POST", "path": "/reports/generate",
            "headers": [], "query_string": b"",
            "client": ("127.0.0.1", 8000), "scheme": "http",
            "server": ("test", 80), "root_path": "",
        }
        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        request = Request(scope, receive=receive)

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            with pytest.raises(HTTPException) as exc:
                await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=db,
                )

        assert exc.value.status_code in (400, 403)

    @pytest.mark.asyncio
    async def test_non_ai_sections_free_user_ok(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks
        from app.api.routes.reports import generate_report
        from app.models.user import User

        user = User()
        user.id = "user-err-003"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="upload-non-ai",
            title="Non-AI Test",
            sections=["charts", "data_table"],
        )

        class _FoundUpload:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _AsyncDB:
            def __init__(self):
                self.call_count = 0
            async def execute(self, query, params=None):
                idx = self.call_count
                self.call_count += 1
                if idx == 0:
                    return _FoundUpload()
                return _NotFound()
            async def commit(self):
                pass
            async def rollback(self):
                pass

        db = _AsyncDB()

        scope = {
            "type": "http", "method": "POST", "path": "/reports/generate",
            "headers": [], "query_string": b"",
            "client": ("127.0.0.1", 8000), "scheme": "http",
            "server": ("test", 80), "root_path": "",
        }
        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        request = Request(scope, receive=receive)

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            resp = await generate_report(
                request=request, body=body,
                background_tasks=BackgroundTasks(),
                current_user=user, db=db,
            )

        assert resp["success"] is True
        assert resp["data"]["status"] == "processing"


def _make_test_request(method="POST", path="/reports/upload"):
    from starlette.requests import Request
    scope = {
        "type": "http", "method": method, "path": path,
        "headers": [(b"authorization", b"Bearer test")],
        "query_string": b"", "client": ("127.0.0.1", 8000),
        "scheme": "http", "server": ("test", 80), "root_path": "",
    }
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    return Request(scope, receive=receive)


class TestUploadFile:
    @pytest.mark.asyncio
    async def test_invalid_mime_type_rejected(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_file
        from app.models.user import User

        user = User()
        user.id = "user-upload-001"
        user.tier = "free"
        user.reports_this_month = 0
        user.is_active = True

        file = MagicMock()
        file.content_type = "application/pdf"
        file.filename = "test.pdf"

        request = _make_test_request()
        db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await upload_file(request=request, file=file, current_user=user, db=db)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_file_too_large(self):
        from unittest.mock import MagicMock, AsyncMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_file
        from app.models.user import User

        user = User()
        user.id = "user-upload-002"
        user.tier = "free"
        user.reports_this_month = 0
        user.is_active = True

        file = MagicMock()
        file.content_type = "text/csv"
        file.filename = "large.csv"
        file.read = AsyncMock(return_value=b"x" * (10 * 1024 * 1024 + 1))

        request = _make_test_request()
        db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await upload_file(request=request, file=file, current_user=user, db=db)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_parse_error_returns_400(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import upload_file
        from app.models.user import User

        user = User()
        user.id = "user-upload-003"
        user.tier = "free"
        user.reports_this_month = 0
        user.is_active = True

        file = MagicMock()
        file.content_type = "text/csv"
        file.filename = "bad.csv"
        file.read = AsyncMock(return_value=b"invalid,content\nbroken")

        request = _make_test_request()
        db = MagicMock()

        with patch("app.api.routes.reports.parse_csv", side_effect=ValueError("Invalid CSV")):
            with pytest.raises(HTTPException) as exc:
                await upload_file(request=request, file=file, current_user=user, db=db)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_free_tier_monthly_limit_exceeded(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_file
        from app.models.user import User

        user = User()
        user.id = "user-upload-004"
        user.tier = "free"
        user.reports_this_month = 3
        user.is_active = True

        file = MagicMock()
        file.content_type = "text/csv"
        file.filename = "test.csv"

        request = _make_test_request()
        db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await upload_file(request=request, file=file, current_user=user, db=db)

        assert exc.value.status_code == 402


class TestGetReport:
    @pytest.mark.asyncio
    async def test_get_report_parses_ai_insights_json_string(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-get-001"
        user.is_active = True

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-get-001", "title": "Test Report", "status": "completed",
            "ai_summary": "Summary", "ai_insights": '["insight 1", "insight 2"]',
            "ai_anomalies": None, "template_type": "marketing",
            "user_id": "user-get-001", "created_at": datetime(2026, 1, 1),
            "pdf_url": None, "share_token": None, "share_view_count": 0,
            "error_message": None, "ai_skipped": False,
            "row_count": None, "column_count": None, "trend_pct": None,
            "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None):
                return row
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-get-001", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == ["insight 1", "insight 2"]

    @pytest.mark.asyncio
    async def test_get_report_ai_insights_null(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-get-002"
        user.is_active = True

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-get-002", "title": "Null Insights", "status": "completed",
            "ai_summary": None, "ai_insights": None, "ai_anomalies": None,
            "template_type": "marketing", "user_id": "user-get-002",
            "created_at": datetime(2026, 1, 1), "pdf_url": None,
            "share_token": None, "share_view_count": 0, "error_message": None,
            "ai_skipped": False, "row_count": None, "column_count": None,
            "trend_pct": None, "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None):
                return row
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-get-002", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == []

    @pytest.mark.asyncio
    async def test_get_report_not_found_404(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-get-003"
        user.is_active = True

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _NotFound()
            async def commit(self):
                pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await get_report(report_id="nonexistent", current_user=user, db=db)

        assert exc.value.status_code == 404


class TestListReports:
    @pytest.mark.asyncio
    async def test_list_reports_with_workspace_filter(self):
        from unittest.mock import MagicMock, patch
        from app.api.routes.reports import list_reports
        from app.models.user import User

        user = User()
        user.id = "user-list-001"
        user.is_active = True

        class _Result:
            def mappings(self):
                return self
            def all(self):
                return []
            def scalar(self):
                return 0

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _Result()
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await list_reports(
                limit=20, offset=0,
                workspace_id="ws-001",
                current_user=user, db=db,
            )

        assert result["success"] is True
        assert any("workspace_id" in q.lower() for q in db.executed_queries)

    @pytest.mark.asyncio
    async def test_list_reports_pagination(self):
        from unittest.mock import MagicMock, patch
        from app.api.routes.reports import list_reports
        from app.models.user import User

        user = User()
        user.id = "user-list-002"
        user.is_active = True

        class _Result:
            def mappings(self):
                return self
            def all(self):
                return []
            def scalar(self):
                return 0

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _Result()
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await list_reports(
                limit=5, offset=10,
                workspace_id=None,
                current_user=user, db=db,
            )

        assert result["success"] is True
        assert result["data"]["limit"] == 5
        assert result["data"]["offset"] == 10


class TestRetryReport:
    @pytest.mark.asyncio
    async def test_retry_non_failed_returns_400(self):
        from unittest.mock import MagicMock
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import retry_report
        from app.models.user import User

        user = User()
        user.id = "user-retry-001"
        user.is_active = True

        class _FoundNonFailed:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.__getitem__ = lambda self_, k: "completed" if k == "status" else None
                row.get.return_value = None
                return row

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _FoundNonFailed()
            async def commit(self):
                pass
            async def rollback(self):
                pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await retry_report(
                report_id="rep-completed",
                background_tasks=BackgroundTasks(),
                current_user=user, db=db,
            )

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_retry_not_found_returns_404(self):
        from unittest.mock import MagicMock
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import retry_report
        from app.models.user import User

        user = User()
        user.id = "user-retry-002"
        user.is_active = True

        class _NotFound:
            def mappings(self):
                return self
            def first(self):
                return None

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _NotFound()
            async def commit(self):
                pass
            async def rollback(self):
                pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await retry_report(
                report_id="nonexistent",
                background_tasks=BackgroundTasks(),
                current_user=user, db=db,
            )

        assert exc.value.status_code == 404


class TestShareReport:
    @pytest.mark.asyncio
    async def test_share_report_success(self):
        from unittest.mock import MagicMock, patch
        from app.api.routes.reports import share_report, ShareRequest
        from app.models.user import User

        user = User()
        user.id = "user-share-001"
        user.is_active = True

        class _FoundReport:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.__getitem__ = lambda self_, k: "rep-share-001" if k == "id" else None
                row.get.return_value = None
                return row

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _FoundReport()
            async def commit(self):
                pass

        db = _AsyncDB()

        body = ShareRequest(expires_days=30)

        with patch("app.api.routes.reports.settings") as mock_settings:
            mock_settings.FRONTEND_BASE_URL = "https://app.naxely.com"
            result = await share_report(
                report_id="rep-share-001", body=body,
                current_user=user, db=db,
            )

        assert result["success"] is True
        assert "share_token" in result["data"]
        assert result["data"]["share_url"].startswith("https://app.naxely.com/share/")

    @pytest.mark.asyncio
    async def test_revoke_share_success(self):
        from unittest.mock import MagicMock
        from app.api.routes.reports import revoke_share
        from app.models.user import User

        user = User()
        user.id = "user-share-002"
        user.is_active = True

        class _FoundReport:
            def mappings(self):
                return self
            def first(self):
                row = MagicMock()
                row.__getitem__ = lambda self_, k: "rep-share-002" if k == "id" else None
                row.get.return_value = None
                return row

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _FoundReport()
            async def commit(self):
                pass

        db = _AsyncDB()

        result = await revoke_share(
            report_id="rep-share-002", current_user=user, db=db,
        )

        assert result["success"] is True
        assert result["data"]["revoked"] is True
        assert any("share_token = NULL" in q for q in db.executed_queries)


class TestGenerateSignedUrl:
    @pytest.mark.asyncio
    async def test_generate_signed_url_supabase_failure(self):
        from unittest.mock import patch
        from app.api.routes.reports import _generate_signed_url

        with patch("app.api.routes.reports._run_sync", side_effect=Exception("Supabase error")):
            result = await _generate_signed_url("reports/test/report.pdf")

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_signed_url_unbound_local_error(self):
        from unittest.mock import patch
        from app.api.routes.reports import _generate_signed_url

        with patch("app.api.routes.reports._run_sync", return_value=None):
            result = await _generate_signed_url("reports/test/report.pdf")

        assert result is None


class TestBulkDeleteStorage:
    @pytest.mark.asyncio
    async def test_bulk_delete_skips_storage_for_no_pdf_url(self):
        from unittest.mock import MagicMock, patch
        from app.api.routes.reports import bulk_delete_reports, BulkDeleteRequest
        from app.models.user import User

        user = User()
        user.id = "user-bulk-001"
        user.is_active = True

        body = BulkDeleteRequest(report_ids=["rep-1", "rep-2"])

        class _Result:
            def mappings(self):
                return self
            def all(self):
                return [
                    {"id": "rep-1", "pdf_url": None},
                    {"id": "rep-2", "pdf_url": None},
                ]

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _Result()
            async def commit(self):
                pass

        db = _AsyncDB()

        result = await bulk_delete_reports(body=body, current_user=user, db=db)

        assert result["deleted"] == 2
        assert not any("remove" in str(q).lower() for q in db.executed_queries)

    @pytest.mark.asyncio
    async def test_bulk_delete_empty_list_returns_zero(self):
        from unittest.mock import MagicMock
        from app.api.routes.reports import bulk_delete_reports, BulkDeleteRequest
        from app.models.user import User

        user = User()
        user.id = "user-bulk-002"
        user.is_active = True

        body = BulkDeleteRequest(report_ids=[])
        db = MagicMock()

        result = await bulk_delete_reports(body=body, current_user=user, db=db)

        assert result["deleted"] == 0


class TestStoreCsvUpload:
    @pytest.mark.asyncio
    async def test_store_csv_upload_success(self):
        import json, uuid
        from unittest.mock import MagicMock, patch, AsyncMock
        import pandas as pd
        from app.api.routes.reports import _store_csv_upload

        df = pd.DataFrame({"col_a": [1, 2], "col_b": ["x", "y"]})

        class _AsyncDB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                return MagicMock()
            async def commit(self):
                self.committed = True

        db = _AsyncDB()

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.return_value.storage = mock_storage
            mock_storage.from_.return_value.upload = AsyncMock()

            result = await _store_csv_upload(
                db=db, user_id="user-1", csv_bytes=b"a,b\n1,x\n2,y",
                source_type="csv", filename="test.csv", df=df,
            )

        assert "id" in result
        assert result["file_url"].endswith("raw.csv")
        assert db.committed

    @pytest.mark.asyncio
    async def test_store_csv_upload_storage_first_upload_fails(self):
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from fastapi import HTTPException
        from app.api.routes.reports import _store_csv_upload

        df = pd.DataFrame({"a": [1]})

        class _AsyncDB:
            async def execute(self, query, params=None): return MagicMock()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.return_value.storage = mock_storage
            mock_storage.from_.return_value.upload = MagicMock(side_effect=Exception("Storage down"))

            with pytest.raises(HTTPException) as exc:
                await _store_csv_upload(
                    db=db, user_id="user-1", csv_bytes=b"a\n1",
                    source_type="csv", filename="t.csv", df=df,
                )

        assert exc.value.status_code == 500
        assert "Failed to upload file" in exc.value.detail

    @pytest.mark.asyncio
    async def test_store_csv_upload_scheduled_source_fails_with_cleanup(self):
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from fastapi import HTTPException
        from app.api.routes.reports import _store_csv_upload

        df = pd.DataFrame({"a": [1]})

        class _AsyncDB:
            async def execute(self, query, params=None): return MagicMock()
            async def commit(self): pass

        db = _AsyncDB()
        call_log = []

        def _upload(bucket, path, content, conf=None):
            call_log.append((bucket, path))
            if len(call_log) == 1:
                return MagicMock()
            raise Exception("scheduled-source down")

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.return_value.storage = mock_storage
            mock_storage.from_.return_value.upload = _upload

            with pytest.raises(HTTPException) as exc:
                await _store_csv_upload(
                    db=db, user_id="user-1", csv_bytes=b"a\n1",
                    source_type="csv", filename="t.csv", df=df,
                )

        assert exc.value.status_code == 500
        assert "scheduled-source copy" in exc.value.detail

    @pytest.mark.asyncio
    async def test_store_csv_upload_permanent_copy_fails_with_cleanup(self):
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from fastapi import HTTPException
        from app.api.routes.reports import _store_csv_upload

        df = pd.DataFrame({"a": [1]})

        class _AsyncDB:
            async def execute(self, query, params=None): return MagicMock()
            async def commit(self): pass

        db = _AsyncDB()
        call_log = []

        def _upload(bucket, path, content, conf=None):
            call_log.append(bucket)
            if "permanent" in bucket:
                raise Exception("permanent storage down")
            return MagicMock()

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_supabase.return_value.storage.from_.return_value.upload = _upload

            with pytest.raises(HTTPException) as exc:
                await _store_csv_upload(
                    db=db, user_id="user-1", csv_bytes=b"a\n1",
                    source_type="csv", filename="t.csv", df=df,
                )

        assert exc.value.status_code == 500
        assert "permanent copy" in exc.value.detail

    @pytest.mark.asyncio
    async def test_store_csv_upload_db_insert_fails_with_cleanup(self):
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from fastapi import HTTPException
        from app.api.routes.reports import _store_csv_upload

        df = pd.DataFrame({"a": [1]})

        class _AsyncDB:
            async def execute(self, query, params=None):
                raise Exception("DB down")
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_supabase.return_value.storage.from_.return_value.upload = MagicMock()

            with pytest.raises(HTTPException) as exc:
                await _store_csv_upload(
                    db=db, user_id="user-1", csv_bytes=b"a\n1",
                    source_type="csv", filename="t.csv", df=df,
                )

        assert exc.value.status_code == 500
        assert "upload metadata" in exc.value.detail

    @pytest.mark.asyncio
    async def test_store_csv_upload_cleanup_exceptions_silently_swallowed(self):
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from fastapi import HTTPException
        from app.api.routes.reports import _store_csv_upload

        df = pd.DataFrame({"a": [1]})

        class _AsyncDB:
            async def execute(self, query, params=None): return MagicMock()
            async def commit(self): pass

        db = _AsyncDB()
        call_log = []

        def _upload(bucket, path, content, conf=None):
            call_log.append(bucket)
            if len(call_log) >= 2:
                raise Exception("fail")
            return MagicMock()

        remove_called = []

        def _remove(paths):
            remove_called.append(paths)
            raise Exception("cleanup also fails")

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.return_value.storage = mock_storage
            mock_storage.from_.return_value.upload = _upload
            mock_storage.from_.return_value.remove = _remove

            with pytest.raises(HTTPException):
                await _store_csv_upload(
                    db=db, user_id="user-1", csv_bytes=b"a\n1",
                    source_type="csv", filename="t.csv", df=df,
                )

        assert len(remove_called) >= 1

    @pytest.mark.asyncio
    async def test_store_csv_upload_custom_upload_id(self):
        import uuid
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from app.api.routes.reports import _store_csv_upload

        df = pd.DataFrame({"a": [1, 2]})
        my_id = str(uuid.uuid4())

        class _AsyncDB:
            async def execute(self, query, params=None): return MagicMock()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_supabase.return_value.storage.from_.return_value.upload = MagicMock()
            result = await _store_csv_upload(
                db=db, user_id="user-1", csv_bytes=b"a\n1\n2",
                source_type="csv", filename="t.csv", df=df, upload_id=my_id,
            )

        assert result["id"] == my_id


class TestUploadSheets:
    @pytest.mark.asyncio
    async def test_upload_sheets_success(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        import pandas as pd
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-001"
        user.tier = "agency"
        user.is_active = True

        sheets_data = {"sheets_url": "https://docs.google.com/spreadsheets/d/abc123/edit"}

        class _AsyncDB:
            async def execute(self, query, params=None): return MagicMock()
            async def commit(self): pass

        db = _AsyncDB()

        df = pd.DataFrame({"Date": ["2026-01-01", "2026-01-02", "2026-01-03"], "Revenue": [1000, 1200, 1100]})

        with (
            patch("app.api.routes.reports.sheets_service.extract_sheet_id", return_value="abc123"),
            patch("app.api.routes.reports.sheets_service.build_credentials"),
            patch("app.api.routes.reports.asyncio.get_event_loop"),
            patch("app.api.routes.reports._store_csv_upload", AsyncMock(return_value={
                "id": "upload-sheets-1", "file_url": "user-1/upload-sheets-1/raw.csv",
                "columns": [],
            })),
        ):
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=df)
            from unittest.mock import patch as _p2
            with _p2("app.api.routes.reports.asyncio.get_event_loop", return_value=mock_loop):
                result = await upload_sheets(
                    sheets_data=sheets_data, current_user=user, db=db,
                )

        assert result["success"] is True
        assert result["data"]["source_type"] == "sheets"

    @pytest.mark.asyncio
    async def test_upload_sheets_missing_url(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-002"
        user.tier = "agency"
        user.is_active = True

        with pytest.raises(HTTPException) as exc:
            await upload_sheets(sheets_data={}, current_user=user, db=MagicMock())

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_sheets_invalid_url(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-003"
        user.tier = "agency"
        user.is_active = True

        with pytest.raises(HTTPException) as exc:
            await upload_sheets(
                sheets_data={"sheets_url": "https://example.com"},
                current_user=user, db=MagicMock(),
            )

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_sheets_extract_failure(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-004"
        user.tier = "agency"
        user.is_active = True

        with patch("app.api.routes.reports.sheets_service.extract_sheet_id", side_effect=ValueError("bad id")):
            with pytest.raises(HTTPException) as exc:
                await upload_sheets(
                    sheets_data={"sheets_url": "https://docs.google.com/spreadsheets/d/abc"},
                    current_user=user, db=MagicMock(),
                )

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_sheets_build_creds_failure(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-005"
        user.tier = "agency"
        user.is_active = True

        with (
            patch("app.api.routes.reports.sheets_service.extract_sheet_id", return_value="abc"),
            patch("app.api.routes.reports.sheets_service.build_credentials", side_effect=ValueError("no creds")),
        ):
            with pytest.raises(HTTPException) as exc:
                await upload_sheets(
                    sheets_data={"sheets_url": "https://docs.google.com/spreadsheets/d/abc"},
                    current_user=user, db=MagicMock(),
                )

        assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_upload_sheets_fetch_permission_error(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import HTTPException
        import pandas as pd
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-006"
        user.tier = "agency"
        user.is_active = True

        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(side_effect=PermissionError("access denied"))

        with (
            patch("app.api.routes.reports.sheets_service.extract_sheet_id", return_value="abc"),
            patch("app.api.routes.reports.sheets_service.build_credentials"),
            patch("app.api.routes.reports.asyncio.get_event_loop", return_value=mock_loop),
        ):
            with pytest.raises(HTTPException) as exc:
                await upload_sheets(
                    sheets_data={"sheets_url": "https://docs.google.com/spreadsheets/d/abc"},
                    current_user=user, db=MagicMock(),
                )

        assert exc.value.status_code == 403


class TestSampleUpload:
    @pytest.mark.asyncio
    async def test_sample_upload_success(self):
        from io import BytesIO
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from app.api.routes.reports import sample_upload
        from app.models.user import User

        user = User()
        user.id = "user-sample-001"
        user.tier = "pro"
        user.is_active = True

        class _AsyncDB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None): return MagicMock()
            async def commit(self): self.committed = True

        db = _AsyncDB()

        df = pd.DataFrame({"project": ["Project A", "Project B"], "hours": [120, 80]})

        with (
            patch("app.api.routes.reports.SAMPLE_CSV_PATH") as mock_path,
            patch("builtins.open", return_value=BytesIO(b"project,hours\nProject A,120\nProject B,80")),
            patch("app.api.routes.reports.parse_csv", return_value=df),
            patch("app.api.routes.reports._get_supabase") as mock_supabase,
        ):
            mock_path.exists.return_value = True
            mock_storage = MagicMock()
            mock_supabase.return_value.storage = mock_storage
            mock_storage.from_.return_value.upload = MagicMock()

            result = await sample_upload(current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["filename"] == "agency_billable_hours.csv"
        assert db.committed

    @pytest.mark.asyncio
    async def test_sample_upload_file_not_found(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import sample_upload
        from app.models.user import User

        user = User()
        user.id = "user-sample-002"
        user.tier = "pro"
        user.is_active = True

        with patch("app.api.routes.reports.SAMPLE_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            with pytest.raises(HTTPException) as exc:
                await sample_upload(current_user=user, db=MagicMock())

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_sample_upload_parse_error(self):
        from io import BytesIO
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import sample_upload
        from app.models.user import User

        user = User()
        user.id = "user-sample-003"
        user.tier = "pro"
        user.is_active = True

        with (
            patch("app.api.routes.reports.SAMPLE_CSV_PATH") as mock_path,
            patch("builtins.open", return_value=BytesIO(b"bad")),
            patch("app.api.routes.reports.parse_csv", side_effect=ValueError("bad csv")),
        ):
            mock_path.exists.return_value = True

            with pytest.raises(HTTPException) as exc:
                await sample_upload(current_user=user, db=MagicMock())

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_sample_upload_storage_fails(self):
        from io import BytesIO
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from fastapi import HTTPException
        from app.api.routes.reports import sample_upload
        from app.models.user import User

        user = User()
        user.id = "user-sample-004"
        user.tier = "pro"
        user.is_active = True

        df = pd.DataFrame({"a": [1], "b": [2]})

        with (
            patch("app.api.routes.reports.SAMPLE_CSV_PATH") as mock_path,
            patch("builtins.open", return_value=BytesIO(b"a,b\n1,2")),
            patch("app.api.routes.reports.parse_csv", return_value=df),
            patch("app.api.routes.reports._get_supabase") as mock_supabase,
        ):
            mock_path.exists.return_value = True
            mock_supabase.return_value.storage.from_.return_value.upload = MagicMock(side_effect=Exception("storage fail"))

            with pytest.raises(HTTPException) as exc:
                await sample_upload(current_user=user, db=MagicMock())

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_sample_upload_db_insert_fails(self):
        from io import BytesIO
        from unittest.mock import MagicMock, patch
        import pandas as pd
        from fastapi import HTTPException
        from app.api.routes.reports import sample_upload
        from app.models.user import User

        user = User()
        user.id = "user-sample-005"
        user.tier = "pro"
        user.is_active = True

        df = pd.DataFrame({"a": [1], "b": [2]})

        class _AsyncDB:
            async def execute(self, query, params=None):
                raise Exception("db fail")
            async def commit(self): pass

        db = _AsyncDB()

        with (
            patch("app.api.routes.reports.SAMPLE_CSV_PATH") as mock_path,
            patch("builtins.open", return_value=BytesIO(b"a,b\n1,2")),
            patch("app.api.routes.reports.parse_csv", return_value=df),
            patch("app.api.routes.reports._get_supabase") as mock_supabase,
        ):
            mock_path.exists.return_value = True
            mock_supabase.return_value.storage.from_.return_value.upload = MagicMock()

            with pytest.raises(HTTPException) as exc:
                await sample_upload(current_user=user, db=db)

        assert exc.value.status_code == 500


class TestListUploads:
    @pytest.mark.asyncio
    async def test_list_uploads_success(self):
        from unittest.mock import MagicMock
        from datetime import datetime
        from app.api.routes.reports import list_uploads
        from app.models.user import User

        user = User()
        user.id = "user-list-u-001"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row1 = _Row()
        row1.set_kw({"id": "up-1", "filename": "f1.csv", "row_count": 10, "column_count": 3, "created_at": datetime(2026, 7, 1)})

        class _Result:
            def mappings(self):
                return self
            def all(self):
                return [row1]

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        result = await list_uploads(current_user=user, db=db)

        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["upload_id"] == "up-1"

    @pytest.mark.asyncio
    async def test_list_uploads_empty(self):
        from unittest.mock import MagicMock
        from app.api.routes.reports import list_uploads
        from app.models.user import User

        user = User()
        user.id = "user-list-u-002"
        user.is_active = True

        class _Empty:
            def mappings(self): return self
            def all(self): return []

        class _AsyncDB:
            async def execute(self, query, params=None): return _Empty()
            async def commit(self): pass

        db = _AsyncDB()

        result = await list_uploads(current_user=user, db=db)

        assert result["success"] is True
        assert result["data"] == []


class TestDeleteReport:
    @pytest.mark.asyncio
    async def test_delete_report_success(self):
        from unittest.mock import MagicMock
        from app.api.routes.reports import delete_report
        from app.models.user import User

        user = User()
        user.id = "user-del-001"
        user.is_active = True

        class _Found:
            def mappings(self): return self
            def first(self):
                row = MagicMock()
                row.__getitem__ = lambda self_, k: "rep-del-001" if k == "id" else None
                row.get.return_value = "rep-del-001"
                return row

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _Found()
            async def commit(self): pass

        db = _AsyncDB()

        result = await delete_report(report_id="rep-del-001", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["deleted"] is True
        assert any("deleted_at" in q for q in db.executed_queries)

    @pytest.mark.asyncio
    async def test_delete_report_not_found(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import delete_report
        from app.models.user import User

        user = User()
        user.id = "user-del-002"
        user.is_active = True

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            async def execute(self, query, params=None): return _NotFound()
            async def commit(self): pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await delete_report(report_id="nonexistent", current_user=user, db=db)

        assert exc.value.status_code == 404


class TestGetReportStatus:
    @pytest.mark.asyncio
    async def test_get_status_completed_with_pdf(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report_status
        from app.models.user import User

        user = User()
        user.id = "user-st-001"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-st-001", "status": "completed",
            "pdf_url": "reports/user-1/rep-st-001/report.pdf",
            "generation_time_seconds": 42, "error_message": None,
            "config": "{}",
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"):
            result = await get_report_status(report_id="rep-st-001", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["status"] == "completed"
        assert result["data"]["progress_percent"] == 100
        assert result["data"]["pdf_url"] == "https://signed.url/pdf"

    @pytest.mark.asyncio
    async def test_get_status_failed(self):
        from unittest.mock import MagicMock
        from datetime import datetime
        from app.api.routes.reports import get_report_status
        from app.models.user import User

        user = User()
        user.id = "user-st-002"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-st-002", "status": "failed",
            "pdf_url": None, "generation_time_seconds": None,
            "error_message": "Something broke", "config": "{}",
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        result = await get_report_status(report_id="rep-st-002", current_user=user, db=db)

        assert result["success"] is False
        assert result["data"]["status"] == "failed"
        assert result["data"]["error_message"] == "Something broke"

    @pytest.mark.asyncio
    async def test_get_status_processing_with_ai_sections(self):
        from unittest.mock import MagicMock
        from datetime import datetime
        from app.api.routes.reports import get_report_status
        from app.models.user import User

        user = User()
        user.id = "user-st-003"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-st-003", "status": "processing",
            "pdf_url": None, "generation_time_seconds": None,
            "error_message": None, "current_step": "charts",
            "config": '{"sections": ["executive_summary", "charts"]}',
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        result = await get_report_status(report_id="rep-st-003", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["status"] == "processing"
        assert result["data"]["progress_percent"] == 45

    @pytest.mark.asyncio
    async def test_get_status_not_found(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import get_report_status
        from app.models.user import User

        user = User()
        user.id = "user-st-004"
        user.is_active = True

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            async def execute(self, query, params=None): return _NotFound()
            async def commit(self): pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await get_report_status(report_id="nonexistent", current_user=user, db=db)

        assert exc.value.status_code == 404


class TestDownloadReport:
    @pytest.mark.asyncio
    async def test_download_report_success(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from app.api.routes.reports import download_report
        from app.models.user import User

        user = User()
        user.id = "user-dl-001"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-dl-001", "status": "completed",
            "pdf_url": "reports/user-1/rep-dl-001/report.pdf",
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        class _FakeResponse:
            status_code = 200
            content = b"fake-pdf-bytes"
            def raise_for_status(self): pass

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=_FakeResponse())

        with (
            patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"),
            patch("httpx.AsyncClient", return_value=mock_client),
        ):
            result = await download_report(report_id="rep-dl-001", current_user=user, db=db)

        assert result.status_code == 200
        assert result.body == b"fake-pdf-bytes"

    @pytest.mark.asyncio
    async def test_download_report_not_found(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import download_report
        from app.models.user import User

        user = User()
        user.id = "user-dl-002"
        user.is_active = True

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            async def execute(self, query, params=None): return _NotFound()
            async def commit(self): pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await download_report(report_id="nonexistent", current_user=user, db=db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_download_report_not_completed(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import download_report
        from app.models.user import User

        user = User()
        user.id = "user-dl-003"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({"id": "rep-dl-003", "status": "processing", "pdf_url": None})

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await download_report(report_id="rep-dl-003", current_user=user, db=db)

        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_download_report_signed_url_failure(self):
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from app.api.routes.reports import download_report
        from app.models.user import User

        user = User()
        user.id = "user-dl-004"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-dl-004", "status": "completed",
            "pdf_url": "reports/user-1/rep-dl-004/report.pdf",
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await download_report(report_id="rep-dl-004", current_user=user, db=db)

        assert exc.value.status_code == 502

    @pytest.mark.asyncio
    async def test_download_report_http_failure(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import HTTPException
        from app.api.routes.reports import download_report
        from app.models.user import User

        user = User()
        user.id = "user-dl-005"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-dl-005", "status": "completed",
            "pdf_url": "reports/user-1/rep-dl-005/report.pdf",
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(side_effect=Exception("connection error"))

        with (
            patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"),
            patch("httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(HTTPException) as exc:
                await download_report(report_id="rep-dl-005", current_user=user, db=db)

        assert exc.value.status_code == 502


class TestPreviewCharts:
    @pytest.mark.asyncio
    async def test_preview_charts_upload_not_found(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import preview_charts, PreviewChartsRequest
        from app.models.user import User

        user = User()
        user.id = "user-pc-001"
        user.is_active = True
        user.tier = "pro"

        body = PreviewChartsRequest(upload_id="nonexistent")

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            async def execute(self, query, params=None): return _NotFound()
            async def commit(self): pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await preview_charts(body=body, current_user=user, db=db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_preview_charts_ai_selection_success(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from app.api.routes.reports import preview_charts, PreviewChartsRequest
        from app.models.user import User

        user = User()
        user.id = "user-pc-002"
        user.is_active = True
        user.tier = "agency"

        body = PreviewChartsRequest(upload_id="up-pc-002")

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw
            def keys(self):
                return self._kw.keys()

        row = _Row()
        row.set_kw({"id": "up-pc-002", "file_url": "user-1/up-pc-002/raw.csv"})

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        ai_specs = [{"x": "Date", "y": "Sales", "type": "bar", "title": "Sales by Date"}]

        with (
            patch("app.api.routes.reports._run_sync", return_value=b"a,b\n1,2"),
            patch("app.api.routes.reports._get_supabase"),
            patch("app.api.routes.reports._process_csv", return_value=(MagicMock(), MagicMock())),
            patch("app.api.routes.reports.ai_service_mod.get_user_api_key", return_value=("openai", "sk-test")),
            patch("app.api.routes.reports.chart_service_mod.select_charts_with_ai", return_value=ai_specs),
        ):
            result = await preview_charts(body=body, current_user=user, db=db)

        assert result["chart_specs"] == ai_specs

    @pytest.mark.asyncio
    async def test_preview_charts_ai_fallback_to_rule_based(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        import pandas as pd
        from app.api.routes.reports import preview_charts, PreviewChartsRequest
        from app.models.user import User

        user = User()
        user.id = "user-pc-003"
        user.is_active = True
        user.tier = "agency"

        body = PreviewChartsRequest(upload_id="up-pc-003")

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({"id": "up-pc-003", "file_url": "user-1/up-pc-003/raw.csv"})

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        df_norm = pd.DataFrame({"Date": ["2024-01", "2024-02"], "Sales": [100, 200], "Category": ["A", "B"]})

        with (
            patch("app.api.routes.reports._run_sync", return_value=b"Date,Sales,Category\n2024-01,100,A\n2024-02,200,B"),
            patch("app.api.routes.reports._get_supabase"),
            patch("app.api.routes.reports._process_csv", return_value=(MagicMock(), df_norm)),
            patch("app.api.routes.reports.ai_service_mod.get_user_api_key", return_value=("openai", "sk-test")),
            patch("app.api.routes.reports.chart_service_mod.select_charts_with_ai", side_effect=Exception("AI down")),
            patch("app.api.routes.reports.chart_service_mod._select_chart_pairs", return_value=[("Date", "Sales")]),
            patch("app.api.routes.reports.chart_service_mod.select_chart_type", return_value="bar"),
        ):
            result = await preview_charts(body=body, current_user=user, db=db)

        assert len(result["chart_specs"]) >= 1
        assert result["chart_specs"][0]["y"] == "Sales"


class TestBulkDeleteWithStorageCleanup:
    @pytest.mark.asyncio
    async def test_bulk_delete_removes_storage_files(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from app.api.routes.reports import bulk_delete_reports, BulkDeleteRequest
        from app.models.user import User

        user = User()
        user.id = "user-bulk-st-001"
        user.is_active = True

        body = BulkDeleteRequest(report_ids=["rep-st-1", "rep-st-2"])

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        r1 = _Row()
        r1.set_kw({"id": "rep-st-1", "pdf_url": "reports/user-bulk-st-001/rep-st-1/report.pdf"})
        r2 = _Row()
        r2.set_kw({"id": "rep-st-2", "pdf_url": "reports/user-bulk-st-001/rep-st-2/report.pdf"})

        class _Result:
            def mappings(self): return self
            def all(self): return [r1, r2]

        remove_called = []

        class _AsyncDB:
            def __init__(self):
                self.executed_queries = []
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.return_value.storage = mock_storage
            mock_storage.from_.return_value.remove = MagicMock()

            result = await bulk_delete_reports(body=body, current_user=user, db=db)

        assert result["deleted"] == 2
        assert any("DELETE FROM reports" in q for q in db.executed_queries)

    @pytest.mark.asyncio
    async def test_bulk_delete_storage_remove_ignores_error(self):
        from unittest.mock import MagicMock, patch
        from app.api.routes.reports import bulk_delete_reports, BulkDeleteRequest
        from app.models.user import User

        user = User()
        user.id = "user-bulk-st-002"
        user.is_active = True

        body = BulkDeleteRequest(report_ids=["rep-st-3"])

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({"id": "rep-st-3", "pdf_url": "reports/user-bulk-st-002/rep-st-3/report.pdf"})

        class _Result:
            def mappings(self): return self
            def all(self): return [row]

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._get_supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.return_value.storage = mock_storage
            mock_storage.from_.return_value.remove = MagicMock(side_effect=Exception("storage remove failed"))

            result = await bulk_delete_reports(body=body, current_user=user, db=db)

        assert result["deleted"] == 1

    @pytest.mark.asyncio
    async def test_bulk_delete_no_matching_rows_returns_zero(self):
        from unittest.mock import MagicMock
        from app.api.routes.reports import bulk_delete_reports, BulkDeleteRequest
        from app.models.user import User

        user = User()
        user.id = "user-bulk-st-003"
        user.is_active = True

        body = BulkDeleteRequest(report_ids=["no-match"])

        class _Empty:
            def mappings(self): return self
            def all(self): return []

        class _AsyncDB:
            async def execute(self, query, params=None): return _Empty()
            async def commit(self): pass

        db = _AsyncDB()

        result = await bulk_delete_reports(body=body, current_user=user, db=db)

        assert result["deleted"] == 0


class TestGenerateReportWithAISections:
    @pytest.mark.asyncio
    async def test_ai_insights_section_gates_free_user(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import generate_report, ReportGenerateRequest
        from app.models.user import User

        user = User()
        user.id = "user-ai-sec-001"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="up-ai-sec-001", title="AI Insights",
            sections=["insights"],
        )

        class _FoundUpload:
            def mappings(self): return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _FoundUpload()
            async def commit(self): pass
            async def rollback(self): pass

        db = _AsyncDB()
        request = _make_test_request()

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            with pytest.raises(HTTPException) as exc:
                await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=db,
                )

        assert exc.value.status_code in (400, 403)

    @pytest.mark.asyncio
    async def test_anomalies_section_gates_free_user(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import generate_report, ReportGenerateRequest
        from app.models.user import User

        user = User()
        user.id = "user-ai-sec-002"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="up-ai-sec-002", title="Anomalies",
            sections=["anomalies"],
        )

        class _FoundUpload:
            def mappings(self): return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _FoundUpload()
            async def commit(self): pass
            async def rollback(self): pass

        db = _AsyncDB()
        request = _make_test_request()

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            with pytest.raises(HTTPException) as exc:
                await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=db,
                )

        assert exc.value.status_code in (400, 403)

    @pytest.mark.asyncio
    async def test_trends_section_gates_free_user(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import generate_report, ReportGenerateRequest
        from app.models.user import User

        user = User()
        user.id = "user-ai-sec-003"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="up-ai-sec-003", title="Trends",
            sections=["trends"],
        )

        class _FoundUpload:
            def mappings(self): return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _FoundUpload()
            async def commit(self): pass
            async def rollback(self): pass

        db = _AsyncDB()
        request = _make_test_request()

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            with pytest.raises(HTTPException) as exc:
                await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=db,
                )

        assert exc.value.status_code in (400, 403)

    @pytest.mark.asyncio
    async def test_multiple_ai_sections_gate_free_user(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks, HTTPException
        from app.api.routes.reports import generate_report, ReportGenerateRequest
        from app.models.user import User

        user = User()
        user.id = "user-ai-sec-004"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="up-ai-sec-004", title="All AI",
            sections=["executive_summary", "insights", "anomalies", "trends"],
        )

        class _FoundUpload:
            def mappings(self): return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _FoundUpload()
            async def commit(self): pass
            async def rollback(self): pass

        db = _AsyncDB()
        request = _make_test_request()

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            with pytest.raises(HTTPException) as exc:
                await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=db,
                )

        assert exc.value.status_code in (400, 403)


class TestGenerateReportChartSpecsOverride:
    @pytest.mark.asyncio
    async def test_chart_specs_override_in_config(self):
        import json
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks
        from app.api.routes.reports import generate_report, ReportGenerateRequest, ChartSpecOverride
        from app.models.user import User

        user = User()
        user.id = "user-cso-001"
        user.tier = "pro"
        user.report_count = 5
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="up-cso-001", title="CSO Test",
            sections=["charts"],
            chart_specs=[ChartSpecOverride(x="Date", y="Sales", type="bar", title="Sales")],
        )

        class _FoundUpload:
            def mappings(self): return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            def __init__(self):
                self.call_count = 0
                self.executed_queries = []
            async def execute(self, query, params=None):
                qs = str(query)
                self.executed_queries.append(qs)
                idx = self.call_count
                self.call_count += 1
                if idx == 0:
                    return _FoundUpload()
                return _NotFound()
            async def commit(self): pass
            async def rollback(self): pass

        db = _AsyncDB()
        request = _make_test_request()

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            resp = await generate_report(
                request=request, body=body,
                background_tasks=BackgroundTasks(),
                current_user=user, db=db,
            )

        assert resp["success"] is True
        insert_q = [q for q in db.executed_queries if "INSERT INTO reports" in q]
        assert len(insert_q) == 1


class TestGetReportWithAnomalies:
    @pytest.mark.asyncio
    async def test_get_report_parses_ai_anomalies_json_string(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-ga-001"
        user.is_active = True

        class _Row:
            def mappings(self): return self
            def first(self): return self
            def __getitem__(self, k): return self._kw.get(k)
            def get(self, k, default=None): return self._kw.get(k, default)
            def set_kw(self, kw): self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-ga-001", "title": "Anomalies Test", "status": "completed",
            "ai_summary": None, "ai_insights": None,
            "ai_anomalies": '["anomaly 1", "anomaly 2"]',
            "template_type": "marketing", "user_id": "user-ga-001",
            "created_at": datetime(2026, 1, 1), "pdf_url": None,
            "share_token": None, "share_view_count": 0, "error_message": None,
            "ai_skipped": False, "row_count": None, "column_count": None,
            "trend_pct": None, "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None): return row
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-ga-001", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_anomalies"] == ["anomaly 1", "anomaly 2"]

    @pytest.mark.asyncio
    async def test_get_report_ai_anomalies_list(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-ga-002"
        user.is_active = True

        class _Row:
            def mappings(self): return self
            def first(self): return self
            def __getitem__(self, k): return self._kw.get(k)
            def get(self, k, default=None): return self._kw.get(k, default)
            def set_kw(self, kw): self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-ga-002", "title": "Anomalies List", "status": "completed",
            "ai_summary": None, "ai_insights": None,
            "ai_anomalies": ["a1", "a2"],
            "template_type": "marketing", "user_id": "user-ga-002",
            "created_at": datetime(2026, 1, 1), "pdf_url": None,
            "share_token": None, "share_view_count": 0, "error_message": None,
            "ai_skipped": False, "row_count": None, "column_count": None,
            "trend_pct": None, "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None): return row
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-ga-002", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_anomalies"] == ["a1", "a2"]


class TestShareReportNotFound:
    @pytest.mark.asyncio
    async def test_share_report_not_found(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import share_report, ShareRequest
        from app.models.user import User

        user = User()
        user.id = "user-share-nf-001"
        user.is_active = True

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            async def execute(self, query, params=None): return _NotFound()
            async def commit(self): pass

        db = _AsyncDB()
        body = ShareRequest(expires_days=30)

        with pytest.raises(HTTPException) as exc:
            await share_report(report_id="nonexistent", body=body, current_user=user, db=db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_share_not_found(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import revoke_share
        from app.models.user import User

        user = User()
        user.id = "user-revoke-nf-001"
        user.is_active = True

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            async def execute(self, query, params=None): return _NotFound()
            async def commit(self): pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await revoke_share(report_id="nonexistent", current_user=user, db=db)

        assert exc.value.status_code == 404


class TestGetSharedReportNotFound:
    @pytest.mark.asyncio
    async def test_get_shared_report_not_found(self):
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.routes.reports import get_shared_report

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            async def execute(self, query, params=None): return _NotFound()
            async def commit(self): pass

        db = _AsyncDB()

        with pytest.raises(HTTPException) as exc:
            await get_shared_report(share_token="bad-token", db=db)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_shared_report_parses_ai_insights_json(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime, timezone
        from app.api.routes.reports import get_shared_report

        class _Row:
            def __getitem__(self, k): return self._kw.get(k)
            def get(self, k, default=None): return self._kw.get(k, default)
            def set_kw(self, kw): self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-shared-ai-001", "title": "Shared AI", "status": "completed",
            "template_type": "marketing", "user_tier": "pro",
            "pdf_url": "reports/pro/report.pdf", "share_expires_at": None,
            "ai_summary": "Summary text",
            "ai_insights": '["insight a", "insight b"]',
            "ai_anomalies": '["anomaly x"]',
            "created_at": datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"):
            result = await get_shared_report(share_token="ai-token", db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == ["insight a", "insight b"]
        assert result["data"]["ai_anomalies"] == ["anomaly x"]

    @pytest.mark.asyncio
    async def test_get_shared_report_ai_insights_null(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime, timezone
        from app.api.routes.reports import get_shared_report

        class _Row:
            def __getitem__(self, k): return self._kw.get(k)
            def get(self, k, default=None): return self._kw.get(k, default)
            def set_kw(self, kw): self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-shared-null-001", "title": "Null AI", "status": "completed",
            "template_type": "marketing", "user_tier": "free",
            "pdf_url": None, "share_expires_at": None,
            "ai_summary": None, "ai_insights": None, "ai_anomalies": None,
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_shared_report(share_token="null-token", db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == []
        assert result["data"]["ai_anomalies"] == []


class TestGenerateSignedUrlInner:
    @pytest.mark.asyncio
    async def test_signed_url_unbound_local_error_returns_none(self):
        from unittest.mock import patch
        from app.api.routes.reports import _generate_signed_url

        with patch("app.api.routes.reports._run_sync", side_effect=UnboundLocalError("mock unbound")):
            result = await _generate_signed_url("reports/test/report.pdf")
            assert result is None

    @pytest.mark.asyncio
    async def test_signed_url_generic_exception_returns_none(self):
        from unittest.mock import patch
        from app.api.routes.reports import _generate_signed_url

        with patch("app.api.routes.reports._run_sync", side_effect=Exception("generic error")):
            result = await _generate_signed_url("reports/test/report.pdf")
            assert result is None

    @pytest.mark.asyncio
    async def test_signed_url_outer_exception_returns_none(self):
        from unittest.mock import patch
        from app.api.routes.reports import _generate_signed_url

        with patch("app.api.routes.reports._run_sync", side_effect=Exception("outer error")):
            result = await _generate_signed_url("reports/test/report.pdf")
            assert result is None


class TestGenerateReportIntegrityErrorReraise:
    @pytest.mark.asyncio
    async def test_integrity_error_no_winner_reraises(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from starlette.requests import Request
        from fastapi import BackgroundTasks
        from sqlalchemy.exc import IntegrityError
        from app.api.routes.reports import generate_report, ReportGenerateRequest
        from app.models.user import User

        user = User()
        user.id = "user-int-001"
        user.tier = "free"
        user.report_count = 0
        user.is_active = True

        body = ReportGenerateRequest(
            upload_id="up-int-001", title="Integrity Test",
            sections=["charts"],
        )

        class _FoundUpload:
            def mappings(self): return self
            def first(self):
                row = MagicMock()
                row.get.return_value = "test.csv"
                row.__getitem__.return_value = "test.csv"
                return row

        class _NotFound:
            def mappings(self): return self
            def first(self): return None

        class _AsyncDB:
            def __init__(self):
                self.call_count = 0
            async def execute(self, query, params=None):
                idx = self.call_count
                self.call_count += 1
                if idx == 0:
                    return _FoundUpload()
                if idx == 1:
                    return _NotFound()
                if "INSERT INTO reports" in str(query):
                    raise IntegrityError("duplicate key", {}, None)
                return _NotFound()
            async def commit(self): pass
            async def rollback(self): pass

        db = _AsyncDB()
        request = _make_test_request()

        with patch("app.api.routes.reports.check_report_limit", AsyncMock()):
            with pytest.raises(IntegrityError):
                await generate_report(
                    request=request, body=body,
                    background_tasks=BackgroundTasks(),
                    current_user=user, db=db,
                )


class TestGetSheetsConfig:
    @pytest.mark.asyncio
    async def test_sheets_config_configured(self):
        from unittest.mock import patch
        from app.api.routes.reports import get_sheets_config
        from app.models.user import User

        user = User()
        user.id = "user-sc-001"
        user.tier = "pro"
        user.is_active = True

        with patch("app.api.routes.reports.sheets_service.get_service_account_email", return_value="service@naxely.iam.gserviceaccount.com"):
            result = await get_sheets_config(current_user=user)

        assert result["configured"] is True
        assert result["service_account_email"] == "service@naxely.iam.gserviceaccount.com"

    @pytest.mark.asyncio
    async def test_sheets_config_not_configured(self):
        from unittest.mock import patch
        from app.api.routes.reports import get_sheets_config
        from app.models.user import User

        user = User()
        user.id = "user-sc-002"
        user.tier = "pro"
        user.is_active = True

        with patch("app.api.routes.reports.sheets_service.get_service_account_email", return_value=None):
            result = await get_sheets_config(current_user=user)

        assert result["configured"] is False
        assert result["service_account_email"] is None


class TestUploadFileFreeTierLimit:
    @pytest.mark.asyncio
    async def test_upload_storage_failure(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_file
        from app.models.user import User

        user = User()
        user.id = "user-uf-001"
        user.tier = "pro"
        user.reports_this_month = 0
        user.is_active = True

        file = MagicMock()
        file.content_type = "text/csv"
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=b"a,b\n1,2")

        request = _make_test_request()
        db = MagicMock()

        with (
            patch("app.api.routes.reports._store_csv_upload", side_effect=HTTPException(status_code=500, detail="Storage failed")),
            patch("slowapi.extension.Limiter._check_request_limit"),
        ):
            with pytest.raises(HTTPException) as exc:
                await upload_file(request=request, file=file, current_user=user, db=db)

        assert exc.value.status_code == 500


class TestGetReportJsonParse:
    @pytest.mark.asyncio
    async def test_get_report_ai_insights_json_parse_fails(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-get-parse-001"
        user.is_active = True

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-parse-001", "title": "Test", "status": "completed",
            "ai_summary": None, "ai_insights": "not-valid-json",
            "ai_anomalies": None, "template_type": "marketing",
            "user_id": "user-get-parse-001", "created_at": datetime(2026, 1, 1),
            "pdf_url": None, "share_token": None, "share_view_count": 0,
            "error_message": None, "ai_skipped": False,
            "row_count": None, "column_count": None, "trend_pct": None,
            "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None):
                return row
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-parse-001", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == []

    @pytest.mark.asyncio
    async def test_get_report_ai_anomalies_json_string(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-get-parse-002"
        user.is_active = True

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-parse-002", "title": "Test", "status": "completed",
            "ai_summary": None, "ai_insights": None,
            "ai_anomalies": '["anomaly 1"]', "template_type": "marketing",
            "user_id": "user-get-parse-002", "created_at": datetime(2026, 1, 1),
            "pdf_url": None, "share_token": None, "share_view_count": 0,
            "error_message": None, "ai_skipped": False,
            "row_count": None, "column_count": None, "trend_pct": None,
            "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None):
                return row
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-parse-002", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_anomalies"] == ["anomaly 1"]

    @pytest.mark.asyncio
    async def test_get_report_ai_anomalies_json_parse_fails(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-get-parse-003"
        user.is_active = True

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-parse-003", "title": "Test", "status": "completed",
            "ai_summary": None, "ai_insights": None,
            "ai_anomalies": "not-valid-json",
            "template_type": "marketing",
            "user_id": "user-get-parse-003", "created_at": datetime(2026, 1, 1),
            "pdf_url": None, "share_token": None, "share_view_count": 0,
            "error_message": None, "ai_skipped": False,
            "row_count": None, "column_count": None, "trend_pct": None,
            "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None):
                return row
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-parse-003", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_anomalies"] == []


class TestListReportsCompleted:
    @pytest.mark.asyncio
    async def test_list_reports_with_completed_pdf(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import list_reports
        from app.models.user import User

        user = User()
        user.id = "user-list-pdf-001"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-list-pdf-1", "title": "Completed Report",
            "template_type": "marketing", "status": "completed",
            "row_count": 100, "trend_pct": 5.2,
            "created_at": datetime(2026, 7, 1),
            "generation_time_seconds": 30,
            "pdf_url": "reports/user-1/rep-list-pdf-1/report.pdf",
        })

        notfound = _Row()
        notfound.set_kw({
            "id": "rep-list-pdf-2", "title": "Pending Report",
            "template_type": "marketing", "status": "pending",
            "row_count": None, "trend_pct": None,
            "created_at": datetime(2026, 7, 1),
            "generation_time_seconds": None,
            "pdf_url": None,
        })

        class _Result:
            def __init__(self):
                self._call_count = 0
            def mappings(self):
                return self
            def all(self):
                self._call_count += 1
                if self._call_count == 1:
                    return [row, notfound]
                return []
            def scalar(self):
                return 2

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _Result()
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url/pdf"):
            result = await list_reports(
                limit=20, offset=0, workspace_id=None,
                current_user=user, db=db,
            )

        assert result["success"] is True
        assert result["data"]["total"] == 2
        completed = result["data"]["reports"][0]
        assert completed["status"] == "completed"
        assert completed["pdf_url"] == "https://signed.url/pdf"
        pending = result["data"]["reports"][1]
        assert pending["status"] == "pending"
        assert pending["pdf_url"] is None

    @pytest.mark.asyncio
    async def test_list_reports_completed_no_pdf(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import list_reports
        from app.models.user import User

        user = User()
        user.id = "user-list-nopdf"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-list-nopdf-1", "title": "No PDF",
            "template_type": "marketing", "status": "completed",
            "row_count": 10, "trend_pct": None,
            "created_at": datetime(2026, 7, 1),
            "generation_time_seconds": 15,
            "pdf_url": None,
        })

        class _Result:
            def mappings(self):
                return self
            def all(self):
                return [row]
            def scalar(self):
                return 1

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _Result()
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await list_reports(
                limit=20, offset=0, workspace_id=None,
                current_user=user, db=db,
            )

        assert result["success"] is True
        assert result["data"]["reports"][0]["pdf_url"] is None


class TestRetryReportSuccess:
    @pytest.mark.asyncio
    async def test_retry_report_success_with_string_config(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import BackgroundTasks
        from app.api.routes.reports import retry_report
        from app.models.user import User

        user = User()
        user.id = "user-retry-succ"
        user.is_active = True

        class _Row:
            def __init__(self):
                self._kw = {}
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)

        row = _Row()
        row._kw = {"id": "rep-fail-1", "status": "failed", "config": '{"upload_id": "up-1"}'}

        class _Result:
            def mappings(self):
                return self
            def first(self):
                return row

        class _AsyncDB:
            def __init__(self):
                self.committed = False
                self.update_executed = False
            async def execute(self, query, params=None):
                if "UPDATE reports SET" in str(query):
                    self.update_executed = True
                return _Result()
            async def commit(self):
                self.committed = True

        db = _AsyncDB()
        bt = BackgroundTasks()

        with patch("app.api.routes.reports.run_report_pipeline"):
            result = await retry_report(
                report_id="rep-fail-1",
                background_tasks=bt,
                current_user=user, db=db,
            )

        assert result["success"] is True
        assert result["data"]["status"] == "processing"
        assert db.update_executed
        assert db.committed

    @pytest.mark.asyncio
    async def test_retry_report_with_dict_config(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import BackgroundTasks
        from app.api.routes.reports import retry_report
        from app.models.user import User

        user = User()
        user.id = "user-retry-dict"
        user.is_active = True

        class _Row:
            def __init__(self):
                self._kw = {}
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)

        row = _Row()
        row._kw = {"id": "rep-fail-2", "status": "failed", "config": {"upload_id": "up-2"}}

        class _Result:
            def mappings(self):
                return self
            def first(self):
                return row

        class _AsyncDB:
            async def execute(self, query, params=None):
                return _Result()
            async def commit(self):
                pass

        db = _AsyncDB()
        bt = BackgroundTasks()

        with patch("app.api.routes.reports.run_report_pipeline"):
            result = await retry_report(
                report_id="rep-fail-2",
                background_tasks=bt,
                current_user=user, db=db,
            )

        assert result["success"] is True
        assert result["data"]["status"] == "processing"


class TestGetReportStatusConfigParse:
    @pytest.mark.asyncio
    async def test_get_status_config_parse_exception(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report_status
        from app.models.user import User

        user = User()
        user.id = "user-st-cfg-001"
        user.is_active = True

        class _Row:
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-st-cfg-001", "status": "processing",
            "pdf_url": None,
            "generation_time_seconds": None, "error_message": None,
            "current_step": "charts",
            "config": "{invalid json!!!}",
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            async def execute(self, query, params=None): return _Result()
            async def commit(self): pass

        db = _AsyncDB()

        result = await get_report_status(report_id="rep-st-cfg-001", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["status"] == "processing"
        assert result["data"]["progress_percent"] == 45


class TestUploadSheetsErrors:
    @pytest.mark.asyncio
    async def test_upload_sheets_value_error_422(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-422"
        user.tier = "agency"
        user.is_active = True

        with (
            patch("app.api.routes.reports.sheets_service.extract_sheet_id", return_value="abc"),
            patch("app.api.routes.reports.sheets_service.build_credentials"),
            patch("app.api.routes.reports.asyncio.get_event_loop") as mock_loop,
        ):
            mock_loop.return_value.run_in_executor = AsyncMock(side_effect=ValueError("invalid data"))
            with pytest.raises(HTTPException) as exc:
                await upload_sheets(
                    sheets_data={"sheets_url": "https://docs.google.com/spreadsheets/d/abc"},
                    current_user=user, db=MagicMock(),
                )
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_sheets_runtime_error_502(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        from fastapi import HTTPException
        from app.api.routes.reports import upload_sheets
        from app.models.user import User

        user = User()
        user.id = "user-sheets-502"
        user.tier = "agency"
        user.is_active = True

        with (
            patch("app.api.routes.reports.sheets_service.extract_sheet_id", return_value="abc"),
            patch("app.api.routes.reports.sheets_service.build_credentials"),
            patch("app.api.routes.reports.asyncio.get_event_loop") as mock_loop,
        ):
            mock_loop.return_value.run_in_executor = AsyncMock(side_effect=RuntimeError("timeout"))
            with pytest.raises(HTTPException) as exc:
                await upload_sheets(
                    sheets_data={"sheets_url": "https://docs.google.com/spreadsheets/d/abc"},
                    current_user=user, db=MagicMock(),
                )
        assert exc.value.status_code == 502


class TestUploadFileXlsx:
    @pytest.mark.asyncio
    async def test_xlsx_upload_success(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        import pandas as pd
        from app.api.routes.reports import upload_file
        from app.models.user import User

        user = User()
        user.id = "user-xlsx-001"
        user.tier = "agency"
        user.reports_this_month = 0
        user.is_active = True

        file = MagicMock()
        file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        file.filename = "report.xlsx"
        file.read = AsyncMock(return_value=b"col1,col2\n1,2")

        df = pd.DataFrame({"col1": [1], "col2": [2]})

        request = _make_test_request()
        request.state.view_rate_limit = None
        db = MagicMock()

        with (
            patch("app.api.routes.reports.parse_csv", return_value=df),
            patch("app.api.routes.reports._store_csv_upload") as mock_store,
            patch("slowapi.extension.Limiter._check_request_limit"),
        ):
            mock_store.return_value = {
                "id": "upload-xlsx-1",
                "file_url": "user-1/upload-xlsx-1/raw.xlsx",
                "columns": [],
            }
            result = await upload_file(request=request, file=file, current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["upload_id"] == "upload-xlsx-1"


class TestGetReportInsightsAnomaliesList:
    @pytest.mark.asyncio
    async def test_get_report_ai_insights_as_list(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_report
        from app.models.user import User

        user = User()
        user.id = "user-inslist"
        user.is_active = True

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-inslist-1", "title": "Test", "status": "completed",
            "ai_summary": None,
            "ai_insights": ["insight 1", "insight 2"],
            "ai_anomalies": ["anomaly 1", "anomaly 2"],
            "template_type": "marketing",
            "user_id": "user-inslist", "created_at": datetime(2026, 1, 1),
            "pdf_url": None, "share_token": None, "share_view_count": 0,
            "error_message": None, "ai_skipped": False,
            "row_count": None, "column_count": None, "trend_pct": None,
            "generation_time_seconds": None,
        })

        class _AsyncDB:
            async def execute(self, query, params=None):
                return row
            async def commit(self):
                pass

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_report(report_id="rep-inslist-1", current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == ["insight 1", "insight 2"]
        assert result["data"]["ai_anomalies"] == ["anomaly 1", "anomaly 2"]


class TestGetSharedReportJsonParse:
    @pytest.mark.asyncio
    async def test_shared_report_ai_insights_parse_fails(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_shared_report
        from app.models.user import User

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-shared-parse-1", "title": "Shared", "status": "completed",
            "ai_summary": None, "ai_insights": "not-valid-json",
            "ai_anomalies": None, "pdf_url": None,
            "share_expires_at": None, "user_tier": "pro",
            "created_at": datetime(2026, 1, 1),
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None): return _Result()
            async def commit(self): self.committed = True

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_shared_report(share_token="tok-001", db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == []
        assert db.committed

    @pytest.mark.asyncio
    async def test_shared_report_ai_insights_as_list(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_shared_report
        from app.models.user import User

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-shared-parse-2", "title": "Shared", "status": "completed",
            "ai_summary": None, "ai_insights": ["insight 1", "insight 2"],
            "ai_anomalies": None, "pdf_url": None,
            "share_expires_at": None, "user_tier": "agency",
            "created_at": datetime(2026, 1, 1),
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None): return _Result()
            async def commit(self): self.committed = True

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_shared_report(share_token="tok-002", db=db)

        assert result["success"] is True
        assert result["data"]["ai_insights"] == ["insight 1", "insight 2"]

    @pytest.mark.asyncio
    async def test_shared_report_ai_anomalies_parse_fails(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_shared_report
        from app.models.user import User

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-shared-parse-3", "title": "Shared", "status": "completed",
            "ai_summary": None, "ai_insights": None,
            "ai_anomalies": "not-valid-json", "pdf_url": None,
            "share_expires_at": None, "user_tier": "agency",
            "created_at": datetime(2026, 1, 1),
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None): return _Result()
            async def commit(self): self.committed = True

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_shared_report(share_token="tok-003", db=db)

        assert result["success"] is True
        assert result["data"]["ai_anomalies"] == []

    @pytest.mark.asyncio
    async def test_shared_report_ai_anomalies_as_list(self):
        from unittest.mock import MagicMock, patch
        from datetime import datetime
        from app.api.routes.reports import get_shared_report
        from app.models.user import User

        class _Row:
            def mappings(self):
                return self
            def first(self):
                return self
            def __getitem__(self, k):
                return self._kw.get(k)
            def get(self, k, default=None):
                return self._kw.get(k, default)
            def set_kw(self, kw):
                self._kw = kw

        row = _Row()
        row.set_kw({
            "id": "rep-shared-parse-4", "title": "Shared", "status": "completed",
            "ai_summary": None, "ai_insights": None,
            "ai_anomalies": ["anomaly A", "anomaly B"],
            "pdf_url": None,
            "share_expires_at": None, "user_tier": "agency",
            "created_at": datetime(2026, 1, 1),
        })

        class _Result:
            def mappings(self): return self
            def first(self): return row

        class _AsyncDB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None): return _Result()
            async def commit(self): self.committed = True

        db = _AsyncDB()

        with patch("app.api.routes.reports._generate_signed_url"):
            result = await get_shared_report(share_token="tok-004", db=db)

        assert result["success"] is True
        assert result["data"]["ai_anomalies"] == ["anomaly A", "anomaly B"]
