import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


def _user(
    tier: str,
    encrypted_api_key: bytes | None = None,
    api_key_iv: bytes | None = None,
    ai_provider: str = "openai",
    id: str = "user-test-123",
):
    u = type("FakeUser", (), {})()
    u.id = id
    u.tier = tier
    u.subscription_tier = tier
    u.ai_provider = ai_provider
    u.encrypted_api_key = encrypted_api_key
    u.api_key_iv = api_key_iv
    return u


class TestGetUserApiKeyTierCheck:
    """
    Defense-in-depth: get_user_api_key() must return server Gemini for Free
    users even if they have a stored BYOK key.

    These target Phase 3 Fix 4.
    """

    def test_free_user_with_stored_key_returns_gemini(self):
        """
        MUST FAIL before Phase 3 Fix 4.
        Currently returns ("openai", "sk-stolen") — does NOT check tier.
        After fix: returns ("gemini", GEMINI_API_KEY).
        """
        from app.services.ai_service import get_user_api_key
        import app.services.ai_service as ai_svc

        free = _user("free", encrypted_api_key=b"ekey", api_key_iv=b"eiv")

        with patch("app.services.ai_service.decrypt_api_key", return_value="sk-stolen"):
            with patch.object(ai_svc.settings, "GEMINI_API_KEY", "test-gemini-key"):
                provider, key = get_user_api_key(free)

        assert provider == "gemini"
        assert key == "test-gemini-key"

    def test_pro_user_with_stored_key_uses_own_key(self):
        """
        Pro user with stored key must still get their own key.
        Regression guard — should always pass.
        """
        from app.services.ai_service import get_user_api_key

        pro = _user("pro", encrypted_api_key=b"ekey", api_key_iv=b"eiv")

        with patch("app.services.ai_service.decrypt_api_key", return_value="sk-pro-key"):
            provider, key = get_user_api_key(pro)

        assert provider == "openai"
        assert key == "sk-pro-key"

    def test_free_user_with_gemini_provider_still_gets_gemini(self):
        """
        Free user who chose Gemini provider still gets server Gemini.
        Should pass before and after fix.
        """
        from app.services.ai_service import get_user_api_key
        import app.services.ai_service as ai_svc

        free = _user("free", ai_provider="gemini")

        with patch.object(ai_svc.settings, "GEMINI_API_KEY", "server-gemini-key"):
            provider, key = get_user_api_key(free)

        assert provider == "gemini"
        assert key == "server-gemini-key"

    def test_free_user_without_key_gets_gemini_after_fix(self):
        """
        BEFORE Fix 4: Free user with no stored key and non-gemini provider
        raises HTTPException(402).
        AFTER Fix 4: Returns server Gemini instead (graceful fallback).
        This test expects the post-fix behavior.
        """
        from app.services.ai_service import get_user_api_key
        import app.services.ai_service as ai_svc

        free = _user("free")

        with patch.object(ai_svc.settings, "GEMINI_API_KEY", "test-gemini-key"):
            provider, key = get_user_api_key(free)

        assert provider == "gemini"
        assert key == "test-gemini-key"


class TestByokDepDirect:
    """
    Direct unit tests for require_byok.
    These complement test_auth_deps.py TestRequireByok.
    No TestClient needed — call the dep function directly.
    """

    def test_require_byok_blocks_free_user_with_key(self):
        from app.api.deps import require_byok

        free = _user("free", encrypted_api_key=b"key", api_key_iv=b"iv")
        with pytest.raises(HTTPException) as exc:
            require_byok(current_user=free)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "UPGRADE_REQUIRED"

    def test_require_byok_allows_free_user_without_key(self):
        from app.api.deps import require_byok

        free = _user("free")
        result = require_byok(current_user=free)
        assert result is free

    def test_require_byok_allows_pro_user_with_key(self):
        from app.api.deps import require_byok

        pro = _user("pro", encrypted_api_key=b"key", api_key_iv=b"iv")
        result = require_byok(current_user=pro)
        assert result is pro


class TestByokRouteImports:
    """
    Smoke tests: verify the routes that must use require_byok can be
    imported after Phase 3 Fixes 1-3 are applied.
    """

    def test_reports_routes_importable(self):
        from app.api.routes import reports
        assert hasattr(reports, "retry_report")
        assert hasattr(reports, "preview_charts")

    def test_settings_routes_importable(self):
        from app.api.routes import settings
        assert hasattr(settings, "save_api_key")

    def test_deps_importable(self):
        from app.api.deps import require_byok
        assert callable(require_byok)
