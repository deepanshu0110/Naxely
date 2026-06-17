import pytest
from app.services.report_service import _has_ai_sections, _make_user_proxy
from app.models.user import User


class TestReportServiceHelpers:
    def test_has_ai_sections_with_ai(self):
        config = {"sections": ["executive_summary", "kpi_overview", "charts"]}
        assert _has_ai_sections(config) is True

    def test_has_ai_sections_without_ai(self):
        config = {"sections": ["kpi_overview", "charts", "data_table"]}
        assert _has_ai_sections(config) is False

    def test_has_ai_sections_empty(self):
        assert _has_ai_sections({}) is False

    def test_has_ai_sections_insights(self):
        config = {"sections": ["insights"]}
        assert _has_ai_sections(config) is True

    def test_has_ai_sections_anomalies(self):
        config = {"sections": ["anomalies", "trends"]}
        assert _has_ai_sections(config) is True

    def test_make_user_proxy(self):
        user_data = {
            "id": "test-uuid",
            "email": "test@example.com",
            "tier": "pro",
            "brand_color": "#1F3864",
            "encrypted_api_key": "enc",
            "api_key_iv": "iv",
            "ai_provider": "openai",
            "logo_url": "https://example.com/logo.png",
            "company_name": "Acme Corp",
        }
        user = _make_user_proxy(user_data)
        assert isinstance(user, User)
        assert user.tier == "pro"
        assert user.brand_color == "#1F3864"
        assert user.ai_provider == "openai"

    def test_make_user_proxy_empty(self):
        user = _make_user_proxy({})
        assert isinstance(user, User)
