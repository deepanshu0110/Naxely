import re
from unittest.mock import patch, MagicMock
from app.api.routes.settings import (
    VALID_KEY_PATTERNS,
    ALLOWED_LOGO_EXTENSIONS,
    MAX_LOGO_SIZE,
    MONTHLY_LIMITS,
    HEX_COLOR_PATTERN,
    ProfileUpdateRequest,
    ApiKeyRequest,
    BrandingUpdateRequest,
)
from app.api.routes.payments import PLANS_DATA
from app.api.routes.templates import (
    TemplateCreateRequest,
    TemplateUpdateRequest,
)
import pytest


class TestApiKeyValidation:
    def test_openai_key_valid(self):
        pattern = VALID_KEY_PATTERNS["openai"]
        assert re.match(pattern, "sk-proj-abcdefghijklmnopqrstuv")

    def test_openai_key_invalid_no_prefix(self):
        pattern = VALID_KEY_PATTERNS["openai"]
        assert not re.match(pattern, "proj-abcdefghijklmnopqrstuv")

    def test_openai_key_too_short(self):
        pattern = VALID_KEY_PATTERNS["openai"]
        assert not re.match(pattern, "sk-short")

    def test_claude_key_valid(self):
        pattern = VALID_KEY_PATTERNS["claude"]
        assert re.match(pattern, "sk-ant-abcdefghijklmnopqrstuv")

    def test_claude_key_invalid_openai_prefix(self):
        pattern = VALID_KEY_PATTERNS["claude"]
        assert not re.match(pattern, "sk-proj-abcdefghijklmnopqrstuv")

    def test_claude_key_missing_ant(self):
        pattern = VALID_KEY_PATTERNS["claude"]
        assert not re.match(pattern, "sk-abcdefghijklmnopqrstuv")

    def test_gemini_key_valid(self):
        pattern = VALID_KEY_PATTERNS["gemini"]
        assert re.match(pattern, "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        assert re.match(pattern, "AQ.ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abc")

    def test_gemini_key_invalid_prefix(self):
        pattern = VALID_KEY_PATTERNS["gemini"]
        assert not re.match(pattern, "sk-proj-abcdefghijklmnopqrstuv")

    def test_gemini_key_too_short(self):
        pattern = VALID_KEY_PATTERNS["gemini"]
        assert not re.match(pattern, "AIzaShort")


class TestHexColorValidation:
    def test_valid_hex_color(self):
        assert HEX_COLOR_PATTERN.match("#6366F1")
        assert HEX_COLOR_PATTERN.match("#1F3864")
        assert HEX_COLOR_PATTERN.match("#ffffff")

    def test_invalid_hex_color_no_hash(self):
        assert not HEX_COLOR_PATTERN.match("6366F1")

    def test_invalid_hex_color_short(self):
        assert not HEX_COLOR_PATTERN.match("#FFF")

    def test_invalid_hex_color_long(self):
        assert not HEX_COLOR_PATTERN.match("#6366F11")

    def test_invalid_hex_color_non_hex(self):
        assert not HEX_COLOR_PATTERN.match("#GGGGGG")


class TestMonthlyLimits:
    def test_free_limit(self):
        assert MONTHLY_LIMITS["free"] == 3

    def test_pro_no_limit(self):
        assert MONTHLY_LIMITS["pro"] is None

    def test_agency_no_limit(self):
        assert MONTHLY_LIMITS["agency"] is None


class TestLogoValidation:
    def test_allowed_extensions(self):
        assert "png" in ALLOWED_LOGO_EXTENSIONS
        assert "jpg" in ALLOWED_LOGO_EXTENSIONS
        assert "svg" in ALLOWED_LOGO_EXTENSIONS

    def test_disallowed_extensions(self):
        assert "gif" not in ALLOWED_LOGO_EXTENSIONS
        assert "bmp" not in ALLOWED_LOGO_EXTENSIONS

    def test_max_logo_size(self):
        assert MAX_LOGO_SIZE == 2 * 1024 * 1024


class TestProfileUpdateRequest:
    def test_valid_name(self):
        req = ProfileUpdateRequest(full_name="Sarah Johnson")
        assert req.full_name == "Sarah Johnson"

    def test_name_max_length(self):
        long_name = "x" * 255
        req = ProfileUpdateRequest(full_name=long_name)
        assert len(req.full_name) == 255


class TestApiKeyRequest:
    def test_valid_provider(self):
        req = ApiKeyRequest(provider="openai", api_key="sk-test-key-123456789012")
        assert req.provider == "openai"

    def test_api_key_max_length(self):
        key = "sk-" + "a" * 200
        req = ApiKeyRequest(provider="openai", api_key=key[:200])
        assert req.api_key is not None


class TestBrandingUpdateRequest:
    def test_defaults(self):
        req = BrandingUpdateRequest()
        assert req.brand_color is None
        assert req.company_name is None

    def test_with_values(self):
        req = BrandingUpdateRequest(brand_color="#1F3864", company_name="Acme Corp")
        assert req.brand_color == "#1F3864"
        assert req.company_name == "Acme Corp"



class TestPlansData:
    def test_three_plans(self):
        assert len(PLANS_DATA) == 3

    def test_free_plan(self):
        free = PLANS_DATA[0]
        assert free["id"] == "free"
        assert free["price_monthly"] == 0

    def test_pro_plan(self):
        pro = PLANS_DATA[1]
        assert pro["id"] == "pro"
        assert pro["price_monthly"] == 29

    def test_agency_plan(self):
        agency = PLANS_DATA[2]
        assert agency["id"] == "agency"
        assert agency["price_monthly"] == 79


class TestTemplateCreateRequest:
    def test_defaults(self):
        req = TemplateCreateRequest(name="My Template")
        assert req.template_type == "marketing"
        assert req.config == {}

    def test_with_all_fields(self):
        req = TemplateCreateRequest(
            name="Monthly Marketing Report",
            template_type="financial",
            config={"tone": "professional"},
        )
        assert req.name == "Monthly Marketing Report"
        assert req.template_type == "financial"
        assert req.config == {"tone": "professional"}


class TestTemplateUpdateRequest:
    def test_defaults(self):
        req = TemplateUpdateRequest()
        assert req.name is None
        assert req.is_default is None

    def test_with_name_only(self):
        req = TemplateUpdateRequest(name="New Name")
        assert req.name == "New Name"
        assert req.is_default is None

    def test_with_is_default_only(self):
        req = TemplateUpdateRequest(is_default=True)
        assert req.name is None
        assert req.is_default is True


class TestGeminiSaveApiKey:
    """Gemini BYOK fix: Gemini now encrypt-and-store like every other provider."""

    VALID_GEMINI_KEY = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    VALID_GROQ_KEY = "gsk_abcdefghijklmnopqrstuvwxyz012345"

    @pytest.fixture
    def mock_request(self):
        from starlette.requests import Request
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/settings/api-key",
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

    @pytest.fixture
    def db(self):
        class _AsyncDB:
            def __init__(self):
                self.call_count = 0
                self.executed_queries = []
                self.committed = False
                self.rows = []
            async def execute(self, query, params=None):
                self.executed_queries.append((str(query), params))
                return self
            async def commit(self):
                self.committed = True
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []
            def __getitem__(self, k):
                return None
            def get(self, k, default=None):
                return default
        return _AsyncDB()

    @pytest.fixture
    def user(self):
        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        return u

    def _get_executed_update(self, db):
        """Return the last UPDATE query's params dict."""
        for item in reversed(db.executed_queries):
            q, params = item
            qs = str(q)
            if "UPDATE" in qs.upper():
                return params
        return None

    def _patch_limiter(self):
        return patch("app.api.routes.settings.limiter", MagicMock())

    # ── Test 1: Normal Gemini key save ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_gemini_key_stored_normally(self, mock_request, db, user):
        """Submitting a valid Gemini key stores it (encrypted), not null."""
        from app.api.routes.settings import save_api_key, ApiKeyRequest

        with self._patch_limiter():
            with patch("app.api.routes.settings.encrypt_api_key", return_value=("encrypted_abc", "iv_xyz")):
                with patch("app.api.routes.settings.get_master_key", return_value="master" * 8):
                    result = await save_api_key(
                        request=mock_request,
                        body=ApiKeyRequest(provider="gemini", api_key=self.VALID_GEMINI_KEY),
                        current_user=user,
                        db=db,
                    )

        assert result["success"] is True
        assert result["data"]["provider"] == "gemini"
        assert result["data"]["key_preview"] == "...6789"

        params = self._get_executed_update(db)
        assert params is not None
        assert params["encrypted"] == "encrypted_abc"
        assert params["iv"] == "iv_xyz"
        assert params["provider"] == "gemini"
        assert params["preview"] == "...6789"
        assert db.committed is True

    # ── Test 2: Destructive regression — Groq key replaced by Gemini ────

    @pytest.mark.asyncio
    async def test_gemini_replaces_previous_provider_key(self, mock_request, db, user):
        """User with a stored Groq key can switch to Gemini with a real key."""
        from app.api.routes.settings import save_api_key, ApiKeyRequest

        with self._patch_limiter():
            with patch("app.api.routes.settings.encrypt_api_key", return_value=("enc_groq", "iv_groq")):
                with patch("app.api.routes.settings.get_master_key", return_value="master" * 8):
                    await save_api_key(
                        request=mock_request,
                        body=ApiKeyRequest(provider="groq", api_key=self.VALID_GROQ_KEY),
                        current_user=user,
                        db=db,
                    )

        groq_params = self._get_executed_update(db)
        assert groq_params["encrypted"] == "enc_groq"
        assert groq_params["provider"] == "groq"

        with self._patch_limiter():
            with patch("app.api.routes.settings.encrypt_api_key", return_value=("enc_gemini", "iv_gemini")):
                with patch("app.api.routes.settings.get_master_key", return_value="master" * 8):
                    result = await save_api_key(
                        request=mock_request,
                        body=ApiKeyRequest(provider="gemini", api_key=self.VALID_GEMINI_KEY),
                        current_user=user,
                        db=db,
                    )

        assert result["success"] is True
        assert result["data"]["provider"] == "gemini"

        gemini_params = self._get_executed_update(db)
        assert gemini_params["encrypted"] == "enc_gemini"
        assert gemini_params["iv"] == "iv_gemini"
        assert gemini_params["provider"] == "gemini"
        assert gemini_params["preview"] == "...6789"

    # ── Test 3: No-accidental-wipe — empty Gemini submission rejected ────

    @pytest.mark.asyncio
    async def test_empty_gemini_submission_rejected_key_unchanged(self, mock_request, db, user):
        """Submitting Gemini with no API key is rejected (400), preserving existing key."""
        from app.api.routes.settings import save_api_key, ApiKeyRequest

        with self._patch_limiter():
            with patch("app.api.routes.settings.encrypt_api_key", return_value=("enc_groq", "iv_groq")):
                with patch("app.api.routes.settings.get_master_key", return_value="master" * 8):
                    await save_api_key(
                        request=mock_request,
                        body=ApiKeyRequest(provider="groq", api_key=self.VALID_GROQ_KEY),
                        current_user=user,
                        db=db,
                    )

        groq_params = self._get_executed_update(db)
        assert groq_params["provider"] == "groq"
        db.executed_queries.clear()

        from fastapi import HTTPException
        with self._patch_limiter():
            with pytest.raises(HTTPException) as exc:
                await save_api_key(
                    request=mock_request,
                    body=ApiKeyRequest(provider="gemini", api_key=""),
                    current_user=user,
                    db=db,
                )
        assert exc.value.status_code == 400

        no_new_update = self._get_executed_update(db)
        assert no_new_update is None, "No UPDATE should execute when validation fails"

    # ── Test 4: Invalid Gemini format rejected ──────────────────────────

    @pytest.mark.asyncio
    async def test_invalid_gemini_key_format_rejected(self, mock_request, db, user):
        """Invalid Gemini key format returns 400."""
        from app.api.routes.settings import save_api_key, ApiKeyRequest
        from fastapi import HTTPException

        with self._patch_limiter():
            with pytest.raises(HTTPException) as exc:
                await save_api_key(
                    request=mock_request,
                    body=ApiKeyRequest(provider="gemini", api_key="sk-not-a-gemini-key"),
                    current_user=user,
                    db=db,
                )
        assert exc.value.status_code == 400
        assert "Invalid API key format" in str(exc.value.detail)
