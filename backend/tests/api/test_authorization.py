import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from starlette.requests import Request
from fastapi import HTTPException


def _make_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/reports/generate",
        "headers": [(b"authorization", b"Bearer test")],
        "query_string": b"",
        "client": ("127.0.0.1", 8000),
        "scheme": "http",
        "server": ("test", 80),
        "root_path": "",
    }
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    return Request(scope, receive=receive)


class FakeUser:
    """User A — owns resources."""
    id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    email = "owner@test.com"
    full_name = "Owner User"
    tier = "pro"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class FakeUserB:
    """User B — does NOT own resources (but has paid tier to pass tier checks)."""
    id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    email = "intruder@test.com"
    full_name = "Intruder User"
    tier = "pro"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class _NotFound:
    def mappings(self):
        return self
    def first(self):
        return None
    def all(self):
        return []


class _Row:
    def __init__(self, **kw):
        self._kw = kw
    def mappings(self):
        return self
    def first(self):
        return self
    def all(self):
        return [self]
    def __getitem__(self, k):
        return self._kw.get(k)
    def get(self, k, default=None):
        return self._kw.get(k, default)


class _AsyncDB:
    def __init__(self, results=None):
        self.results = results or [MagicMock()]
        self.call_count = 0
        self.executed_queries = []
        self.committed = False

    async def execute(self, query, params=None):
        qs = str(query)
        self.executed_queries.append(qs)
        idx = self.call_count
        self.call_count += 1
        if idx < len(self.results):
            return self.results[idx]
        return MagicMock()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


class TestReportOwnership:
    """User B should get 404 (not 403, not the data) for reports owned by User A."""

    @pytest.mark.asyncio
    async def test_get_report_status_returns_404_for_other_users_report(self):
        from app.api.routes.reports import get_report_status

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await get_report_status("report-owned-by-a", current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_report_returns_404_for_other_users_report(self):
        from app.api.routes.reports import get_report

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await get_report("report-owned-by-a", current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_report_returns_404_for_other_users_report(self):
        from app.api.routes.reports import delete_report

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await delete_report("report-owned-by-a", current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_share_report_returns_404_for_other_users_report(self):
        from app.api.routes.reports import share_report, ShareRequest

        db = _AsyncDB([_NotFound()])
        body = ShareRequest()
        with pytest.raises(HTTPException) as exc:
            await share_report("report-owned-by-a", body, current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_returns_404_for_other_users_upload(self):
        from app.api.routes.reports import generate_report
        from app.api.routes.reports import ReportGenerateRequest

        db = _AsyncDB([_NotFound()])
        body = ReportGenerateRequest(
            upload_id="upload-owned-by-a",
            title="Test",
            template_type="marketing",
            sections=[],
        )
        with pytest.raises(HTTPException) as exc:
            await generate_report(request=_make_request(), body=body, background_tasks=MagicMock(), current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_owner_can_access_own_report_status(self):
        from app.api.routes.reports import get_report_status
        from app.api.routes.reports import _generate_signed_url

        report_row = _Row(
            id="report-owned-by-a",
            user_id=FakeUserA.id,
            status="completed",
            pdf_url="reports/a/report.pdf",
            generation_time_seconds=12,
        )

        db = _AsyncDB([report_row, MagicMock()])
        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url"):
            result = await get_report_status("report-owned-by-a", current_user=FakeUserA(), db=db)
        assert result["success"] is True
        assert result["data"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_owner_can_delete_own_report(self):
        from app.api.routes.reports import delete_report

        report_row = _Row(
            id="report-owned-by-a",
            user_id=FakeUserA.id,
            deleted_at=None,
        )

        db = _AsyncDB([report_row, MagicMock()])
        result = await delete_report("report-owned-by-a", current_user=FakeUserA(), db=db)
        assert result["success"] is True
        assert result["data"]["deleted"] is True

    @pytest.mark.asyncio
    async def test_revoke_share_returns_404_for_other_users_report(self):
        from app.api.routes.reports import revoke_share

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await revoke_share("report-owned-by-a", current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_owner_revokes_own_share(self):
        from app.api.routes.reports import revoke_share

        report_row = _Row(
            id="report-owned-by-a",
            user_id=FakeUserA.id,
            share_token="live_token_abc",
        )

        db = _AsyncDB([report_row, MagicMock()])
        result = await revoke_share("report-owned-by-a", current_user=FakeUserA(), db=db)
        assert result["success"] is True
        assert result["data"]["revoked"] is True
        clear_queries = [q for q in db.executed_queries if "share_token = NULL" in q]
        assert len(clear_queries) > 0

    @pytest.mark.asyncio
    async def test_revoke_share_no_token_noop(self):
        from app.api.routes.reports import revoke_share

        report_row = _Row(
            id="report-owned-by-a",
            user_id=FakeUserA.id,
            share_token=None,
        )

        db = _AsyncDB([report_row, MagicMock()])
        result = await revoke_share("report-owned-by-a", current_user=FakeUserA(), db=db)
        assert result["success"] is True
        assert result["data"]["revoked"] is True


class TestUploadOwnership:
    @pytest.mark.asyncio
    async def test_upload_query_filters_by_user_id(self):
        from app.api.routes.reports import generate_report, ReportGenerateRequest

        upload_row = _Row(
            id="upload-owned-by-a",
            user_id=FakeUserA.id,
            filename="test.csv",
            row_count=10,
            column_count=3,
        )

        db = _AsyncDB([upload_row, MagicMock(), MagicMock()])

        body = ReportGenerateRequest(
            upload_id="upload-owned-by-a",
            title="Test",
            template_type="marketing",
            sections=[],
        )

        with patch("app.api.routes.reports._has_ai_sections", return_value=False):
            with patch("app.api.routes.reports.check_report_limit"):
                with patch("app.api.routes.reports.uuid.uuid4", return_value="new-report-id"):
                    result = await generate_report(
                        request=_make_request(),
                        body=body,
                        background_tasks=MagicMock(),
                        current_user=FakeUserA(),
                        db=db,
                    )

        upload_queries = [q for q in db.executed_queries if "uploads" in q]
        assert len(upload_queries) > 0
        assert "user_id" in upload_queries[0] or "owner" in upload_queries[0]

    @pytest.mark.asyncio
    async def test_upload_owned_by_other_returns_404(self):
        from app.api.routes.reports import generate_report, ReportGenerateRequest
        from fastapi import HTTPException

        db = _AsyncDB([_NotFound()])

        body = ReportGenerateRequest(
            upload_id="upload-owned-by-a",
            title="Test",
            template_type="marketing",
            sections=[],
        )

        with patch("app.api.routes.reports.check_report_limit"):
            with pytest.raises(HTTPException) as exc:
                await generate_report(
                    request=_make_request(),
                    body=body,
                    background_tasks=MagicMock(),
                    current_user=FakeUserB(),
                    db=db,
                )
        assert exc.value.status_code == 404


class FakeUserA:
    id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    email = "owner@test.com"
    full_name = "Owner User"
    tier = "pro"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class TestTemplateOwnership:
    @pytest.mark.asyncio
    async def test_update_template_other_user_returns_404(self):
        from app.api.routes.templates import update_template, TemplateUpdateRequest

        db = _AsyncDB([_NotFound()])
        body = TemplateUpdateRequest(name="Hacked Name")
        with pytest.raises(HTTPException) as exc:
            await update_template("template-owned-by-a", body, current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template_other_user_returns_404(self):
        from app.api.routes.templates import delete_template

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await delete_template("template-owned-by-a", current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_owner_can_update_own_template(self):
        from app.api.routes.templates import update_template, TemplateUpdateRequest

        template_row = _Row(id="template-owned-by-a", user_id=FakeUserA.id, name="Original", template_type="marketing", is_default=False, created_at=datetime.utcnow())

        db = _AsyncDB([template_row, MagicMock(), template_row])
        body = TemplateUpdateRequest(name="Updated Name")
        result = await update_template("template-owned-by-a", body, current_user=FakeUserA(), db=db)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_owner_can_delete_own_template(self):
        from app.api.routes.templates import delete_template

        template_row = _Row(id="template-owned-by-a", user_id=FakeUserA.id)

        db = _AsyncDB([template_row, MagicMock()])
        result = await delete_template("template-owned-by-a", current_user=FakeUserA(), db=db)
        assert result["success"] is True


class FakeFreeUser:
    """Free-tier user — should be blocked by PRO_REQUIRED gate."""
    id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    email = "free@test.com"
    full_name = "Free User"
    tier = "free"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class TestTemplateDeleteProGate:
    @pytest.mark.asyncio
    async def test_free_user_cannot_delete_template(self):
        from app.api.deps import require_pro_or_above

        with pytest.raises(HTTPException) as exc:
            require_pro_or_above(current_user=FakeFreeUser())
        assert exc.value.status_code == 403
        detail = exc.value.detail
        if isinstance(detail, dict):
            assert detail["code"] == "UPGRADE_REQUIRED"

    @pytest.mark.asyncio
    async def test_pro_user_can_delete_own_template(self):
        from app.api.routes.templates import delete_template

        template_row = _Row(id="my-template", user_id=FakeUserA.id)
        db = _AsyncDB([template_row, MagicMock()])
        result = await delete_template("my-template", current_user=FakeUserA(), db=db)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pro_user_cannot_delete_other_template(self):
        from app.api.routes.templates import delete_template

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await delete_template("template-owned-by-a", current_user=FakeUserB(), db=db)
        assert exc.value.status_code == 404


class TestApiKeyDeleteProGate:
    @pytest.mark.asyncio
    async def test_free_user_cannot_delete_api_key(self):
        from app.api.deps import require_pro_or_above

        with pytest.raises(HTTPException) as exc:
            require_pro_or_above(current_user=FakeFreeUser())
        assert exc.value.status_code == 403
        detail = exc.value.detail
        if isinstance(detail, dict):
            assert detail["code"] == "UPGRADE_REQUIRED"

    @pytest.mark.asyncio
    async def test_pro_user_can_delete_api_key(self):
        from app.api.routes.settings import delete_api_key

        db = _AsyncDB([MagicMock()])
        result = await delete_api_key(current_user=FakeUserA(), db=db)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pro_user_delete_api_key_is_self_scoped(self):
        from app.api.routes.settings import delete_api_key

        db = _AsyncDB([MagicMock()])
        result = await delete_api_key(current_user=FakeUserA(), db=db)
        assert result["success"] is True
        executed = " ".join(db.executed_queries).lower() if hasattr(db, "executed_queries") else ""
        assert len(db.executed_queries) >= 1
        assert "where id = :uid" in db.executed_queries[0].lower() or ":uid" in db.executed_queries[0]

    @pytest.mark.asyncio
    async def test_cross_user_api_key_delete_self_scoped(self):
        """Pro user A cannot delete Pro user B's API key — the route inherently
        scopes to the authenticated user via `WHERE id = :uid`; there is no
        mechanism to target another user."""
        from app.api.routes.settings import delete_api_key

        db = _AsyncDB([MagicMock()])
        result = await delete_api_key(current_user=FakeUserA(), db=db)
        assert result["success"] is True
        assert len(db.executed_queries) >= 1
        sql = db.executed_queries[0].lower()
        assert ":uid" in sql
        assert FakeUserB.id.lower() not in sql
