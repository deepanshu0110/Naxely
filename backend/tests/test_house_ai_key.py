import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import patch
from fastapi import HTTPException


def _user(
    tier: str,
    encrypted_api_key: bytes | None = None,
    api_key_iv: bytes | None = None,
    ai_provider: str = "openai",
):
    u = type("FakeUser", (), {})()
    u.id = "user-test-123"
    u.tier = tier
    u.subscription_tier = tier
    u.ai_provider = ai_provider
    u.encrypted_api_key = encrypted_api_key
    u.api_key_iv = api_key_iv
    return u


@pytest.fixture
def house_env(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "HOUSE_AI_KEY_MISTRAL", "hk-mistral-test")
    monkeypatch.setattr(settings, "HOUSE_AI_KEY_GROQ", "hk-groq-test")
    monkeypatch.setattr(settings, "FREE_TIER_HOUSE_KEY_ENABLED", True)
    from app.services import ai_service
    for k in list(ai_service.HOUSE_KEY_STATS.keys()):
        ai_service.HOUSE_KEY_STATS[k] = 0
    return settings


class TestHouseKeyGating:
    def test_free_no_key_gets_house_mistral(self, house_env):
        from app.services.ai_service import get_user_api_key
        provider, key, base_url = get_user_api_key(_user("free"))
        assert provider == "mistral"
        assert key == "hk-mistral-test"
        assert base_url == "https://api.mistral.ai/v1"

    def test_free_own_key_takes_precedence(self, house_env):
        from app.services.ai_service import get_user_api_key
        free = _user("free", encrypted_api_key=b"ekey", api_key_iv=b"eiv")
        with patch("app.services.ai_service.decrypt_api_key", return_value="sk-user"):
            provider, key, _ = get_user_api_key(free)
        assert provider == "openai"
        assert key == "sk-user"

    def test_pro_no_key_untouched(self, house_env):
        from app.services.ai_service import get_user_api_key
        provider, key, _ = get_user_api_key(_user("pro"))
        assert provider is None
        assert key is None

    def test_agency_no_key_untouched(self, house_env):
        from app.services.ai_service import get_user_api_key
        provider, key, _ = get_user_api_key(_user("agency"))
        assert provider is None
        assert key is None

    def test_kill_switch_off_falls_back_to_none(self, house_env, monkeypatch):
        from app.core.config import settings
        from app.services.ai_service import get_user_api_key
        monkeypatch.setattr(settings, "FREE_TIER_HOUSE_KEY_ENABLED", False)
        provider, key, _ = get_user_api_key(_user("free"))
        assert provider is None
        assert key is None

    def test_no_house_keys_configured_falls_back_to_none(self, monkeypatch):
        from app.core.config import settings
        from app.services.ai_service import get_user_api_key
        monkeypatch.setattr(settings, "HOUSE_AI_KEY_MISTRAL", "")
        monkeypatch.setattr(settings, "HOUSE_AI_KEY_GROQ", "")
        monkeypatch.setattr(settings, "FREE_TIER_HOUSE_KEY_ENABLED", True)
        provider, key, _ = get_user_api_key(_user("free"))
        assert provider is None
        assert key is None


class TestFreeAiSectionsGate:
    """generate_report's AI-section gate: free users pass with own key or house coverage."""

    def test_free_no_key_house_on_allowed(self, house_env):
        from app.api.routes.reports import _free_may_use_ai_sections
        assert _free_may_use_ai_sections(_user("free")) is True

    def test_free_no_key_house_off_denied(self, house_env, monkeypatch):
        from app.core.config import settings
        from app.api.routes.reports import _free_may_use_ai_sections
        monkeypatch.setattr(settings, "FREE_TIER_HOUSE_KEY_ENABLED", False)
        assert _free_may_use_ai_sections(_user("free")) is False

    def test_free_own_key_allowed_without_house(self, house_env, monkeypatch):
        from app.core.config import settings
        from app.api.routes.reports import _free_may_use_ai_sections
        monkeypatch.setattr(settings, "FREE_TIER_HOUSE_KEY_ENABLED", False)
        free = _user("free", encrypted_api_key=b"ekey", api_key_iv=b"eiv")
        assert _free_may_use_ai_sections(free) is True

    def test_pro_never_uses_helper_allow(self, house_env):
        # Pro/Agency are allowed upstream by require_pro_or_above; the helper
        # only answers the free-tier question.
        from app.api.routes.reports import _free_may_use_ai_sections
        assert _free_may_use_ai_sections(_user("pro")) is False
        assert _free_may_use_ai_sections(_user("agency")) is False


class TestHouseKeyFallback:
    def test_mistral_ok_no_fallback(self, house_env):
        from app.services import ai_service
        with patch.object(ai_service, "call_openai_compat", return_value="summary text") as m:
            out = ai_service._call_ai("mistral", "p", "s", "hk-mistral-test")
        assert out == "summary text"
        assert m.call_count == 1
        assert ai_service.HOUSE_KEY_STATS["mistral_ok"] == 1
        assert ai_service.HOUSE_KEY_STATS["groq_ok"] == 0

    def test_mistral_429_falls_back_to_groq(self, house_env):
        from app.services import ai_service
        calls = []
        def fake(prompt, system, key, timeout, base_url=None, model=None):
            calls.append(base_url)
            if "mistral" in (base_url or ""):
                raise HTTPException(status_code=429, detail="rate limit")
            return "groq text"
        with patch.object(ai_service, "call_openai_compat", side_effect=fake):
            out = ai_service._call_ai("mistral", "p", "s", "hk-mistral-test")
        assert out == "groq text"
        assert len(calls) == 2
        assert ai_service.HOUSE_KEY_STATS["mistral_fail"] == 1
        assert ai_service.HOUSE_KEY_STATS["groq_ok"] == 1

    def test_both_fail_returns_empty(self, house_env):
        from app.services import ai_service
        with patch.object(ai_service, "call_openai_compat", side_effect=Exception("down")):
            out = ai_service._call_ai("mistral", "p", "s", "hk-mistral-test")
        assert out == ""
        assert ai_service.HOUSE_KEY_STATS["mistral_fail"] == 1
        assert ai_service.HOUSE_KEY_STATS["groq_fail"] == 1

    def test_user_byok_key_never_touches_house_path(self, house_env):
        from app.services import ai_service
        with patch.object(ai_service, "_call_house_ai") as house_mock, \
             patch.object(ai_service, "call_openai_compat", return_value="x") as compat_mock:
            out = ai_service._call_ai("openai", "p", "s", "sk-user-key")
        assert out == "x"
        house_mock.assert_not_called()
        compat_mock.assert_called_once()

    def test_semaphore_timeout_skips_ai(self, house_env, monkeypatch):
        from app.services import ai_service
        monkeypatch.setattr(ai_service, "HOUSE_SEMAPHORE_TIMEOUT_S", 0.05)
        ai_service._HOUSE_SEMAPHORE.acquire()  # hold the only... (bounded 4, hold all)
        held = [ai_service._HOUSE_SEMAPHORE.acquire(blocking=False) for _ in range(3)]
        assert all(held)
        try:
            with pytest.raises(HTTPException) as exc:
                ai_service._call_house_ai("p", "s")
            assert exc.value.status_code == 429
            assert ai_service.HOUSE_KEY_STATS["semaphore_timeout"] == 1
        finally:
            for _ in range(4):
                try:
                    ai_service._HOUSE_SEMAPHORE.release()
                except ValueError:
                    pass

    def test_stats_snapshot(self, house_env):
        from app.services.ai_service import get_house_key_stats
        snap = get_house_key_stats()
        assert set(snap) == {"mistral_ok", "mistral_fail", "groq_ok", "groq_fail", "semaphore_timeout"}
        assert all(v == 0 for v in snap.values())
