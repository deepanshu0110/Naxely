import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _create_api_key(client, token: str) -> str:
    resp = client.post(
        "/settings/api-keys",
        json={"name": "v1 download test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["key"]


def _seed_report(report_id: str, user_id: str, status: str = "completed",
                 pdf_url: str | None = "reports/v1/report.pdf"):
    from tests.conftest import _get_mock_db
    _get_mock_db()._reports[report_id] = {
        "id": report_id,
        "user_id": user_id,
        "status": status,
        "pdf_url": pdf_url,
        "error_message": None,
        "created_at": None,
    }


def _client_setup(client, user_id: str = "v1-user-1"):
    """Seed deps + an agency user, return the raw API key for it."""
    from tests.conftest import _make_user, _set_deps, _clear_deps, _get_mock_db
    user = _make_user("agency", user_id=user_id)
    _set_deps("agency", user=user)
    key = _create_api_key(client, "fake-key")
    return user, key


# ── GET /v1/reports/{id}/download ─────────────────────────────────────────────
# Regression guard for the A1 fix: `_generate_signed_url` must run for real.

class TestV1Download:

    def test_download_completed_report(self, client):
        """200, application/pdf, and the REAL signed-URL + httpx retrieval code runs."""
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        user, key = _client_setup(client, "v1-dl-user")
        _seed_report("rep-dl-001", user.id, status="completed",
                     pdf_url="reports/v1-dl-user/rep-dl-001/report.pdf")

        class _Resp:
            content = b"%PDF-1.4 fake naxely report"

            def raise_for_status(self):
                pass

        with patch("app.api.routes.reports._get_supabase") as mock_sb, \
             patch("httpx.AsyncClient") as mock_http:
            mock_sb.return_value.storage.from_.return_value.create_signed_url.return_value = {
                "signedURL": "https://signed.example/rep-dl-001/report.pdf",
            }
            async_client = MagicMock()
            async_client.get = AsyncMock(return_value=_Resp())
            mock_http.return_value.__aenter__.return_value = async_client

            resp = client.get(
                "/v1/reports/rep-dl-001/download",
                headers={"X-API-Key": key},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content == b"%PDF-1.4 fake naxely report"
        disposition = resp.headers["content-disposition"]
        assert disposition.startswith("attachment;")
        assert "naxely_report_rep-dl-0.pdf" in disposition

        # The real signed-URL generation path must have executed (A1 regression guard)
        mock_sb.return_value.storage.from_.assert_called_once_with("reports")
        create_signed_url = mock_sb.return_value.storage.from_.return_value.create_signed_url
        create_signed_url.assert_called_once_with(
            "reports/v1-dl-user/rep-dl-001/report.pdf", 3600,
        )
        async_client.get.assert_called_once()

    def test_download_not_completed_returns_409(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        user, key = _client_setup(client, "v1-dl-user2")
        _seed_report("rep-dl-002", user.id, status="processing")

        resp = client.get(
            "/v1/reports/rep-dl-002/download",
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 409
        assert resp.json()["message"] == "Report is not yet completed"

    def test_download_report_not_found_404(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        _, key = _client_setup(client, "v1-dl-user3")

        resp = client.get(
            "/v1/reports/00000000-0000-0000-0000-000000000000/download",
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 404

    def test_download_requires_api_key(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        resp = client.get("/v1/reports/rep-x/download")
        assert resp.status_code == 401

    def test_download_invalid_api_key(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        resp = client.get(
            "/v1/reports/rep-x/download",
            headers={"X-API-Key": "nax_invalidkeyabcdef1234567890ab"},
        )
        assert resp.status_code == 401

    def test_download_signed_url_failure_502(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        user, key = _client_setup(client, "v1-dl-user4")
        _seed_report("rep-dl-004", user.id, status="completed")

        with patch("app.api.routes.reports._get_supabase") as mock_sb:
            mock_sb.return_value.storage.from_.return_value.create_signed_url.return_value = None
            resp = client.get(
                "/v1/reports/rep-dl-004/download",
                headers={"X-API-Key": key},
            )

        assert resp.status_code == 502
        assert "signed URL" in resp.json()["message"]

    def test_download_pdf_retrieval_failure_502(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        user, key = _client_setup(client, "v1-dl-user5")
        _seed_report("rep-dl-005", user.id, status="completed")

        with patch("app.api.routes.reports._get_supabase") as mock_sb, \
             patch("httpx.AsyncClient") as mock_http:
            mock_sb.return_value.storage.from_.return_value.create_signed_url.return_value = {
                "signedURL": "https://signed.example/rep-dl-005/report.pdf",
            }
            async_client = MagicMock()
            async_client.get = AsyncMock(side_effect=Exception("connection reset"))
            mock_http.return_value.__aenter__.return_value = async_client

            resp = client.get(
                "/v1/reports/rep-dl-005/download",
                headers={"X-API-Key": key},
            )

        assert resp.status_code == 502
        assert "retrieve PDF" in resp.json()["message"]


# ── GET /v1/reports/{id} status signed-URL branch ─────────────────────────────

class TestV1StatusSignedUrl:

    def test_status_completed_returns_signed_url(self, client):
        """Completed report → pdf_url signed via real _generate_signed_url + download_url."""
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        user, key = _client_setup(client, "v1-st-user")
        _seed_report("rep-st-001", user.id, status="completed",
                     pdf_url="reports/v1-st-user/rep-st-001/report.pdf")

        with patch("app.api.routes.reports._get_supabase") as mock_sb:
            mock_sb.return_value.storage.from_.return_value.create_signed_url.return_value = {
                "signedURL": "https://signed.example/rep-st-001/report.pdf",
            }
            resp = client.get("/v1/reports/rep-st-001", headers={"X-API-Key": key})

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["pdf_url"] == "https://signed.example/rep-st-001/report.pdf"
        assert data["download_url"] == "/v1/reports/rep-st-001/download"
        mock_sb.return_value.storage.from_.assert_called_once_with("reports")

    def test_status_in_progress_no_signed_url(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        user, key = _client_setup(client, "v1-st-user2")
        _seed_report("rep-st-002", user.id, status="processing")

        resp = client.get("/v1/reports/rep-st-002", headers={"X-API-Key": key})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processing"
        assert "pdf_url" not in data
        assert "download_url" not in data

    def test_status_failed_returns_error(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        user, key = _client_setup(client, "v1-st-user3")
        _seed_report("rep-st-003", user.id, status="failed")
        from tests.conftest import _get_mock_db
        _get_mock_db()._reports["rep-st-003"]["error_message"] = "AI provider down"

        resp = client.get("/v1/reports/rep-st-003", headers={"X-API-Key": key})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error"] == "AI provider down"

    def test_status_not_found_404(self, client):
        from tests.conftest import _reset_mock_db
        _reset_mock_db()
        _, key = _client_setup(client, "v1-st-user4")

        resp = client.get(
            "/v1/reports/00000000-0000-0000-0000-000000000000",
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 404


# ── Direct endpoint tests: ownership + full status branch ─────────────────────
# Uses a filter-aware fake DB so the WHERE user_id = :uid guard is real, which
# the shared MockDB cannot express (it ignores user_id on reports lookups).

class _OwnershipDB:
    def __init__(self):
        self.reports: dict = {}

    async def execute(self, sql, params=None):
        sql_str = " ".join(str(sql).split())
        params = params or {}
        result = MagicMock()
        if "FROM reports" in sql_str:
            rep = self.reports.get(params.get("id", ""))
            if rep and rep["user_id"] == str(params.get("uid", "")):
                result.mappings.return_value.first.return_value = rep
            else:
                result.mappings.return_value.first.return_value = None
        else:
            result.mappings.return_value.first.return_value = None
        return result

    async def commit(self):
        pass

    async def rollback(self):
        pass


class TestV1DirectOwnership:

    @pytest.mark.asyncio
    async def test_download_other_users_report_404(self):
        from fastapi import HTTPException
        from app.api.routes.v1 import api_download_report
        from tests.conftest import _make_user

        db = _OwnershipDB()
        db.reports["rep-own-1"] = {
            "id": "rep-own-1", "user_id": "owner-user", "status": "completed",
            "pdf_url": "reports/owner-user/rep-own-1/report.pdf", "error_message": None,
        }
        other = _make_user("other-user")

        with patch("app.api.routes.v1._generate_signed_url"):
            with pytest.raises(HTTPException) as exc:
                await api_download_report(report_id="rep-own-1", current_user=other, db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_status_other_users_report_404(self):
        from fastapi import HTTPException
        from app.api.routes.v1 import api_get_report_status
        from tests.conftest import _make_user

        db = _OwnershipDB()
        db.reports["rep-own-2"] = {
            "id": "rep-own-2", "user_id": "owner-user", "status": "completed",
            "pdf_url": "reports/owner-user/rep-own-2/report.pdf", "error_message": None,
        }
        other = _make_user("other-user")

        with pytest.raises(HTTPException) as exc:
            await api_get_report_status(report_id="rep-own-2", current_user=other, db=db)
        assert exc.value.status_code == 404