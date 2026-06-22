import pytest
from app.api.routes.reports import (
    _has_ai_sections,
    ReportGenerateRequest,
    ShareRequest,
    ColumnConfigItem,
    DateRange,
    BrandConfig,
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
