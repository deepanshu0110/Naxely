import hashlib
import secrets
import pytest
from unittest.mock import patch, MagicMock


# ── Unit tests for API key service ────────────────────────────────────────────

class TestApiKeyService:

    def test_generate_key_format(self):
        """Generated key starts with 'nax_' and is 36 chars."""
        from app.services.api_key_service import generate_api_key
        raw, prefix, suffix, key_hash = generate_api_key()
        assert raw.startswith("nax_")
        assert len(raw) == 36
        assert prefix == raw[:8]
        assert suffix == raw[-4:]

    def test_key_hash_is_sha256(self):
        """Stored hash is sha256 of the raw key."""
        from app.services.api_key_service import generate_api_key
        raw, prefix, suffix, key_hash = generate_api_key()
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert key_hash == expected

    def test_two_keys_are_unique(self):
        """Two generated keys are always different."""
        from app.services.api_key_service import generate_api_key
        raw1, *_ = generate_api_key()
        raw2, *_ = generate_api_key()
        assert raw1 != raw2

    def test_verify_key_correct(self):
        """verify_api_key returns True for matching key."""
        from app.services.api_key_service import generate_api_key, verify_api_key
        raw, _, _, key_hash = generate_api_key()
        assert verify_api_key(raw, key_hash) is True

    def test_verify_key_wrong(self):
        """verify_api_key returns False for wrong key."""
        from app.services.api_key_service import generate_api_key, verify_api_key
        raw, _, _, key_hash = generate_api_key()
        assert verify_api_key("nax_wrongkeyabcdef1234567890abcd", key_hash) is False


# ── Key management route tests ─────────────────────────────────────────────────

class TestApiKeyManagement:

    def test_generate_key_agency_only(self, client, pro_user_token):
        """Pro user cannot generate a Naxely API key."""
        resp = client.post(
            "/settings/api-keys",
            json={"name": "My integration"},
            headers={"Authorization": f"Bearer {pro_user_token}"}
        )
        assert resp.status_code == 403

    def test_generate_key_returns_raw_key_once(self, client, agency_user_token):
        """Agency user gets raw key in response (only time it's returned)."""
        resp = client.post(
            "/settings/api-keys",
            json={"name": "CI integration"},
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"].startswith("nax_")
        assert len(data["key"]) == 36
        assert "id" in data
        assert "key" in data

    def test_list_keys_does_not_return_raw_key(self, client, agency_user_token):
        """List endpoint shows prefix/suffix only, not raw key or hash."""
        resp = client.get(
            "/settings/api-keys",
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        assert resp.status_code == 200
        keys = resp.json()
        for k in keys:
            assert "key" not in k or k.get("key") is None
            assert "key_hash" not in k
            assert "key_prefix" in k or "prefix" in k

    def test_revoke_key(self, client, agency_user_token):
        """Agency user can revoke a key by ID."""
        create_resp = client.post(
            "/settings/api-keys",
            json={"name": "Temp key"},
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        key_id = create_resp.json()["id"]
        resp = client.delete(
            f"/settings/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        assert resp.status_code == 200

    def test_cannot_revoke_other_users_key(self, client, agency_user_token):
        """User cannot revoke another user's API key."""
        create_resp = client.post(
            "/settings/api-keys",
            json={"name": "My key"},
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        key_id = create_resp.json()["id"]

        # Switch to a different agency user
        from app.api import deps
        from app.main import app
        from tests.conftest import _make_user
        other = _make_user("agency", user_id="other-agency-user-id")
        app.dependency_overrides[deps.get_current_user] = lambda: other

        resp = client.delete(
            f"/settings/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        assert resp.status_code == 404


# ── Public API endpoint tests ──────────────────────────────────────────────────

class TestPublicApiEndpoints:

    def test_v1_reports_requires_api_key(self, client):
        """POST /v1/reports without X-API-Key returns 401."""
        resp = client.post("/v1/reports", data={}, files={})
        assert resp.status_code == 401

    def test_v1_reports_invalid_key_returns_401(self, client):
        """Invalid API key returns 401."""
        resp = client.post(
            "/v1/reports",
            headers={"X-API-Key": "nax_invalidkeyabcdef1234567890ab"},
        )
        assert resp.status_code == 401

    def test_v1_reports_revoked_key_returns_401(self, client, agency_user_token):
        """Revoked key returns 401 even if format is valid."""
        create_resp = client.post(
            "/settings/api-keys",
            json={"name": "To revoke"},
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        raw_key = create_resp.json()["key"]
        key_id = create_resp.json()["id"]
        client.delete(
            f"/settings/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        resp = client.post(
            "/v1/reports",
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 401

    def test_v1_reports_valid_key_accepts_csv(self, client, agency_user_token):
        """Valid API key with CSV file returns 202 with report_id."""
        create_resp = client.post(
            "/settings/api-keys",
            json={"name": "Test key"},
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        raw_key = create_resp.json()["key"]

        csv_content = b"Date,Revenue\n2024-01-01,1000\n2024-01-02,1200\n"
        with patch("app.api.routes.v1.run_report_pipeline"):
            with patch("app.api.routes.reports._store_csv_upload") as mock_store:
                mock_store.return_value = {"id": "mock-upload-id", "file_url": "mock/path", "columns": []}
                resp = client.post(
                    "/v1/reports",
                    headers={"X-API-Key": raw_key},
                    files={"file": ("data.csv", csv_content, "text/csv")},
                    data={"title": "API Test Report", "sections": '["kpi","charts"]'}
                )
        assert resp.status_code == 202
        data = resp.json()
        assert "report_id" in data
        assert "status_url" in data

    def test_v1_report_status_returns_status(self, client, agency_user_token):
        """GET /v1/reports/{id} returns report status."""
        create_resp = client.post(
            "/settings/api-keys",
            json={"name": "Status test key"},
            headers={"Authorization": f"Bearer {agency_user_token}"}
        )
        raw_key = create_resp.json()["key"]

        resp = client.get(
            "/v1/reports/00000000-0000-0000-0000-000000000000",
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 404
