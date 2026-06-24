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
    get_user_api_key() gating rules:
    - Free user + no key → (None, None, None) — AI skipped
    - Free user + stored key → their own provider config (BYOK)
    - Pro/Agency + stored key → their own provider config
    - Pro/Agency + no key → server Gemini fallback
    """

    def test_free_user_with_stored_key_uses_own_key(self):
        """
        Free user with a stored BYOK key gets their own provider config.
        """
        from app.services.ai_service import get_user_api_key

        free = _user("free", encrypted_api_key=b"ekey", api_key_iv=b"eiv")

        with patch("app.services.ai_service.decrypt_api_key", return_value="sk-stolen"):
            provider, key, _ = get_user_api_key(free)

        assert provider == "openai"
        assert key == "sk-stolen"

    def test_pro_user_with_stored_key_uses_own_key(self):
        """
        Pro user with stored key must still get their own key.
        Regression guard — should always pass.
        """
        from app.services.ai_service import get_user_api_key

        pro = _user("pro", encrypted_api_key=b"ekey", api_key_iv=b"eiv")

        with patch("app.services.ai_service.decrypt_api_key", return_value="sk-pro-key"):
            provider, key, _ = get_user_api_key(pro)

        assert provider == "openai"
        assert key == "sk-pro-key"

    def test_free_user_with_no_key_returns_none(self):
        """
        Free user with no stored key gets (None, None, None) — AI skipped.
        """
        from app.services.ai_service import get_user_api_key

        free = _user("free", ai_provider="gemini")
        provider, key, base_url = get_user_api_key(free)

        assert provider is None
        assert key is None

    def test_free_user_without_stored_key_returns_none(self):
        """
        Free user with no stored key (any provider) returns (None, None, None).
        """
        from app.services.ai_service import get_user_api_key

        free = _user("free")
        provider, key, base_url = get_user_api_key(free)

        assert provider is None
        assert key is None


class TestByokDepDirect:
    """
    Direct unit tests for require_byok.
    These complement test_auth_deps.py TestRequireByok.
    No TestClient needed — call the dep function directly.
    """

    def test_require_byok_allows_free_user_with_key(self):
        from app.api.deps import require_byok

        free = _user("free", encrypted_api_key=b"key", api_key_iv=b"iv")
        result = require_byok(current_user=free)
        assert result is free

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
