import pytest
import json
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock


# ── Unit tests for sheets_service ──────────────────────────────────────────────

class TestSheetsService:

    def test_extract_sheet_id_standard_url(self):
        """Extracts sheet ID from a standard Google Sheets URL."""
        from app.services.sheets_service import extract_sheet_id
        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit#gid=0"
        assert extract_sheet_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"

    def test_extract_sheet_id_pub_url(self):
        """Extracts sheet ID from a /pub URL."""
        from app.services.sheets_service import extract_sheet_id
        url = "https://docs.google.com/spreadsheets/d/ABC123XYZ/pub?output=csv"
        assert extract_sheet_id(url) == "ABC123XYZ"

    def test_extract_sheet_id_invalid_url(self):
        """Raises ValueError on a non-Sheets URL."""
        from app.services.sheets_service import extract_sheet_id
        with pytest.raises(ValueError, match="Invalid Google Sheets URL"):
            extract_sheet_id("https://drive.google.com/file/d/abc/view")

    def test_build_credentials_from_json(self):
        """Builds Google credentials from service account JSON string."""
        from app.services.sheets_service import build_credentials
        fake_sa = json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA0Z3VS5JJcds3xHn/ygWep4BkOPcPUTRPzPnBAm7gj1Sic4+8\n-----END RSA PRIVATE KEY-----\n",
            "client_email": "naxely@test-project.iam.gserviceaccount.com",
            "client_id": "123",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        with patch("google.oauth2.service_account.Credentials.from_service_account_info") as mock:
            mock.return_value = MagicMock()
            creds = build_credentials(fake_sa)
        mock.assert_called_once()
        assert creds is not None

    def test_build_credentials_empty_config_raises(self):
        """Raises ValueError when GOOGLE_SERVICE_ACCOUNT_JSON is empty."""
        from app.services.sheets_service import build_credentials
        with pytest.raises(ValueError, match="not configured"):
            build_credentials("")

    def _patch_build(self, mock_service):
        return patch("app.services.sheets_service.build", return_value=mock_service)

    def test_fetch_sheet_as_df_returns_dataframe(self):
        """fetch_sheet_as_df returns a non-empty DataFrame."""
        from app.services.sheets_service import fetch_sheet_as_df

        mock_creds = MagicMock()
        mock_service = MagicMock()
        mock_values = {
            "values": [
                ["Date", "Revenue", "Units"],
                ["2024-01-01", "1000", "50"],
                ["2024-01-02", "1200", "60"],
            ]
        }
        (mock_service.spreadsheets.return_value
             .values.return_value
             .get.return_value
             .execute.return_value) = mock_values

        with self._patch_build(mock_service):
            df = fetch_sheet_as_df("sheet_id_abc", mock_creds)

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["Date", "Revenue", "Units"]
        assert len(df) == 2

    def test_fetch_sheet_empty_raises(self):
        """Raises ValueError when sheet has no data."""
        from app.services.sheets_service import fetch_sheet_as_df

        mock_creds = MagicMock()
        mock_service = MagicMock()
        (mock_service.spreadsheets.return_value
             .values.return_value
             .get.return_value
             .execute.return_value) = {"values": []}

        with self._patch_build(mock_service):
            with pytest.raises(ValueError, match="empty"):
                fetch_sheet_as_df("sheet_id_abc", mock_creds)

    def test_fetch_sheet_permission_error_raises_descriptive(self):
        """Permission denied from Sheets API raises a descriptive error."""
        from app.services.sheets_service import fetch_sheet_as_df
        from googleapiclient.errors import HttpError

        mock_creds = MagicMock()
        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 403
        (mock_service.spreadsheets.return_value
             .values.return_value
             .get.return_value
             .execute.side_effect) = HttpError(mock_resp, b"Permission denied")

        with self._patch_build(mock_service):
            with pytest.raises(PermissionError, match="share"):
                fetch_sheet_as_df("sheet_id_abc", mock_creds)

    def test_get_service_account_email(self):
        """Extracts service account email from JSON string."""
        from app.services.sheets_service import get_service_account_email
        sa_json = json.dumps({
            "type": "service_account",
            "client_email": "naxely@my-project.iam.gserviceaccount.com"
        })
        assert get_service_account_email(sa_json) == "naxely@my-project.iam.gserviceaccount.com"

    def test_get_service_account_email_empty_returns_none(self):
        """Returns None when JSON is empty."""
        from app.services.sheets_service import get_service_account_email
        assert get_service_account_email("") is None


# ── Route tests ────────────────────────────────────────────────────────────────

class TestUploadSheetsRoute:

    @pytest.fixture
    def pro_user(self):
        u = type("FakeUser", (), {})()
        u.id = "pro-user-123"
        u.tier = "pro"
        u.subscription_tier = "pro"
        u.email = "pro@test.com"
        u.reports_this_month = 0
        return u

    @pytest.fixture
    def free_user(self):
        u = type("FakeUser", (), {})()
        u.id = "free-user-123"
        u.tier = "free"
        u.subscription_tier = "free"
        u.email = "free@test.com"
        u.reports_this_month = 0
        return u

    @pytest.fixture
    def mock_db(self):
        class _MockDB:
            def __init__(self):
                self.executed_queries = []
                self.call_count = 0
            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                return MagicMock()
            async def commit(self):
                pass
            async def rollback(self):
                pass
        return _MockDB()

    @pytest.fixture
    def pro_user_token(self, app, pro_user, mock_db):
        from app.api.deps import get_current_user
        from app.core.database import get_db
        from app.api.routes.reports import router

        async def _override_user():
            return pro_user

        async def _override_db():
            return mock_db

        app.dependency_overrides[get_current_user] = _override_user
        app.dependency_overrides[get_db] = _override_db
        yield "mock-pro-token"
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    @pytest.fixture
    def free_user_token(self, app, free_user, mock_db):
        from app.api.deps import get_current_user
        from app.core.database import get_db

        async def _override_user():
            return free_user

        async def _override_db():
            return mock_db

        app.dependency_overrides[get_current_user] = _override_user
        app.dependency_overrides[get_db] = _override_db
        yield "mock-free-token"
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    def test_upload_sheets_invalid_url_returns_400(self, client, pro_user_token):
        """Non-Sheets URL returns 400."""
        resp = client.post(
            "/reports/upload-sheets",
            json={"sheets_url": "https://drive.google.com/file/d/abc"},
            headers={"Authorization": f"Bearer {pro_user_token}"}
        )
        assert resp.status_code == 400

    def test_upload_sheets_missing_url_returns_400(self, client, pro_user_token):
        """Missing sheets_url returns 400."""
        resp = client.post(
            "/reports/upload-sheets",
            json={},
            headers={"Authorization": f"Bearer {pro_user_token}"}
        )
        assert resp.status_code == 400

    def test_upload_sheets_free_user_returns_403(self, client, free_user_token):
        """Free user is blocked."""
        resp = client.post(
            "/reports/upload-sheets",
            json={"sheets_url": "https://docs.google.com/spreadsheets/d/abc123/edit"},
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert resp.status_code == 403

    def test_upload_sheets_success_returns_upload_id(self, client, pro_user_token):
        """Valid sheet URL with mocked Sheets API returns upload_id."""
        mock_df = pd.DataFrame({
            "Date": ["2024-01-01", "2024-01-02"],
            "Revenue": [1000, 1200],
        })
        mock_creds = MagicMock()
        mock_creds.universe_domain = "googleapis.com"
        with patch("app.api.routes.reports.sheets_service.fetch_sheet_as_df",
                   return_value=mock_df), \
             patch("app.api.routes.reports.sheets_service.build_credentials",
                   return_value=mock_creds), \
             patch("app.api.routes.reports._store_csv_upload",
                   new=AsyncMock(return_value={
                       "id": "mock-upload-id",
                       "file_url": "uploads/user/mock/raw.csv",
                       "columns": [{"name": "Date", "type": "dimension"}, {"name": "Revenue", "type": "metric"}],
                   })):
            resp = client.post(
                "/reports/upload-sheets",
                json={"sheets_url": "https://docs.google.com/spreadsheets/d/abc123/edit"},
                headers={"Authorization": f"Bearer {pro_user_token}"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "upload_id" in data.get("data", data)
