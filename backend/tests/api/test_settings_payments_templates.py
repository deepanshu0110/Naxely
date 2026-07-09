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
        assert re.match(pattern, "AQ.AbCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abc")
        assert re.match(pattern, "AQ.abc.def.ghi.jkl.mno.pqr.stu.vwx.yz0123")

    def test_gemini_key_invalid_prefix(self):
        pattern = VALID_KEY_PATTERNS["gemini"]
        assert not re.match(pattern, "sk-proj-abcdefghijklmnopqrstuv")

    def test_gemini_key_too_short(self):
        pattern = VALID_KEY_PATTERNS["gemini"]
        assert not re.match(pattern, "AIzaShort")
        assert not re.match(pattern, "AQ.tooshort")


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
    VALID_GEMINI_KEY_AQ = "AQ.AbCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abc"
    VALID_GEMINI_KEY_AQ_DOTS = "AQ.abc.def.ghi.jkl.mno.pqr.stu.vwx.yz0123"
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

    # ── Test 2: AQ. format (Google AI Studio real-world format) ────────

    @pytest.mark.asyncio
    async def test_gemini_aq_format_with_dots(self, mock_request, db, user):
        """Key starting with AQ. and containing dots in body passes validation."""
        from app.api.routes.settings import save_api_key, ApiKeyRequest

        for key in [self.VALID_GEMINI_KEY_AQ, self.VALID_GEMINI_KEY_AQ_DOTS]:
            with self._patch_limiter():
                with patch("app.api.routes.settings.encrypt_api_key", return_value=("enc_aq", "iv_aq")):
                    with patch("app.api.routes.settings.get_master_key", return_value="master" * 8):
                        result = await save_api_key(
                            request=mock_request,
                            body=ApiKeyRequest(provider="gemini", api_key=key),
                            current_user=user,
                            db=db,
                        )
            assert result["success"] is True
            assert result["data"]["provider"] == "gemini"

    # ── Test 4: Destructive regression — Groq key replaced by Gemini ────

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

    # ── Test 5: No-accidental-wipe — empty Gemini submission rejected ────

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

    # ── Test 6: Invalid Gemini format rejected ──────────────────────────

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



class TestSettingsRoutes:
    VALID_GROQ_KEY = "gsk_abcdefghijklmnopqrstuvwxyz012345"

    @pytest.fixture
    def mock_request(self):
        from starlette.requests import Request
        scope = {
            "type": "http", "method": "POST", "path": "/settings/api-key",
            "headers": [(b"authorization", b"Bearer test")],
            "query_string": b"", "client": ("127.0.0.1", 8000),
            "scheme": "http", "server": ("test", 80), "root_path": "",
        }
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        return Request(scope, receive=receive)

    @pytest.fixture
    def user(self):
        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        return u

    @pytest.mark.asyncio
    async def test_save_api_key_encrypted(self, mock_request, user):
        from app.api.routes.settings import save_api_key, ApiKeyRequest

        class _DB:
            committed = False
            async def execute(self, query, params=None):
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

        db = _DB()

        mock_request.state.view_rate_limit = None

        with patch("slowapi.extension.Limiter._check_request_limit"):
            with patch("app.api.routes.settings.encrypt_api_key", return_value=("enc_val", "iv_val")):
                with patch("app.api.routes.settings.get_master_key", return_value="master" * 8):
                    result = await save_api_key(
                        request=mock_request,
                        body=ApiKeyRequest(provider="openai", api_key="sk-abcdefghijklmnopqrstuvwx"),
                        current_user=user,
                        db=db,
                    )
        assert result["success"] is True
        assert db.committed

    @pytest.mark.asyncio
    async def test_save_api_key_empty_rejected(self, mock_request, user):
        from app.api.routes.settings import save_api_key, ApiKeyRequest
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()

        with patch("slowapi.extension.Limiter._check_request_limit"):
            with pytest.raises(HTTPException) as exc:
                await save_api_key(
                    request=mock_request,
                    body=ApiKeyRequest(provider="openai", api_key=""),
                    current_user=user,
                    db=db,
                )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_profile_success(self, user):
        from app.api.routes.settings import get_profile

        class _Row(dict):
            def get(self, k, default=None):
                return dict.get(self, k, default)

        row = _Row({
            "email": "test@example.com",
            "full_name": "Test User",
            "tier": "pro",
            "ai_provider": "openai",
            "encrypted_api_key": None,
            "api_key_preview": None,
            "logo_url": None,
            "brand_color": "#6366F1",
            "reports_this_month": 0,
        })

        class _Mappings:
            def first(self):
                return row

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return _Mappings()
            def all(self):
                return []

        db = _DB()

        with patch("app.api.routes.settings._get_logo_signed_url", return_value=None):
            result = await get_profile(
                current_user=user,
                db=db,
            )
        assert result["success"] is True
        assert result["data"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_update_profile_empty_rejected(self, user):
        from app.api.routes.settings import update_profile, ProfileUpdateRequest
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()

        body = ProfileUpdateRequest(full_name="")
        with pytest.raises(HTTPException) as exc:
            await update_profile(
                body=body,
                current_user=user,
                db=db,
            )
        assert exc.value.status_code == 400


class TestBrandingEndpoint:
    def test_branding_hex_color_pattern(self):
        from app.api.routes.settings import HEX_COLOR_PATTERN

        assert not HEX_COLOR_PATTERN.match("#GGGGGG")
        assert not HEX_COLOR_PATTERN.match("not-a-color")
        assert HEX_COLOR_PATTERN.match("#1F3864")
        assert HEX_COLOR_PATTERN.match("#FF5733")
        assert not HEX_COLOR_PATTERN.match("#FFF")


class TestGetLogoSignedUrl:
    """Cover _get_logo_signed_url (lines 45-55)"""

    @pytest.mark.asyncio
    async def test_none_path_returns_none(self):
        from app.api.routes.settings import _get_logo_signed_url
        assert await _get_logo_signed_url(None) is None
        assert await _get_logo_signed_url("") is None

    @pytest.mark.asyncio
    async def test_success_returns_signed_url(self):
        from app.api.routes.settings import _get_logo_signed_url
        with patch("app.api.routes.settings._run_sync", return_value={"signedURL": "https://supabase.co/logo.png?token=abc"}):
            result = await _get_logo_signed_url("logos/user123/logo.png")
        assert result == "https://supabase.co/logo.png?token=abc"

    @pytest.mark.asyncio
    async def test_success_falls_back_to_signedUrl_key(self):
        from app.api.routes.settings import _get_logo_signed_url
        with patch("app.api.routes.settings._run_sync", return_value={"signedUrl": "https://supabase.co/fallback.png"}):
            result = await _get_logo_signed_url("logos/user123/logo.png")
        assert result == "https://supabase.co/fallback.png"

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        from app.api.routes.settings import _get_logo_signed_url
        with patch("app.api.routes.settings._run_sync", side_effect=Exception("boom")):
            result = await _get_logo_signed_url("logos/user123/logo.png")
        assert result is None


class TestExtractBrandColors:
    """Cover extract_brand_colors (lines 58-72)"""

    def test_extracts_colors_from_image(self):
        from app.api.routes.settings import extract_brand_colors
        from PIL import Image
        import io

        img = Image.new("RGB", (150, 150), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        colors = extract_brand_colors(buf.read())
        assert len(colors) > 0
        assert all(c.startswith("#") for c in colors)

    def test_filters_dark_colors(self):
        from app.api.routes.settings import extract_brand_colors
        from PIL import Image
        import io

        img = Image.new("RGB", (150, 150), color=(0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        colors = extract_brand_colors(buf.read())
        for c in colors:
            r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
            assert 20 <= (r + g + b) / 3 <= 235

    def test_filters_bright_colors(self):
        from app.api.routes.settings import extract_brand_colors
        from PIL import Image
        import io

        img = Image.new("RGB", (150, 150), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        colors = extract_brand_colors(buf.read())
        for c in colors:
            r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
            assert 20 <= (r + g + b) / 3 <= 235


class TestGetProfileApiKeyPreview:
    """Cover get_profile api_key_preview paths (lines 111-123)"""

    def base_row(self):
        return {
            "email": "test@example.com",
            "full_name": "Test User",
            "tier": "pro",
            "ai_provider": "openai",
            "encrypted_api_key": "some_encrypted_value",
            "api_key_preview": None,
            "logo_url": None,
            "brand_color": "#6366F1",
            "reports_this_month": 0,
        }

    @pytest.fixture
    def user(self):
        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        return u

    def _make_db(self, row):
        class _Mappings:
            def first(self):
                return row
        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return _Mappings()
            def all(self):
                return []
        return _DB()

    @pytest.mark.asyncio
    async def test_stored_preview_used(self, user):
        from app.api.routes.settings import get_profile
        row = self.base_row()
        row["api_key_preview"] = "sk-...abcd"
        db = self._make_db(row)
        with patch("app.api.routes.settings._get_logo_signed_url", return_value=None):
            result = await get_profile(current_user=user, db=db)
        assert result["data"]["api_key_preview"] == "sk-...abcd"

    @pytest.mark.asyncio
    async def test_no_preview_openai_prefix(self, user):
        from app.api.routes.settings import get_profile
        row = self.base_row()
        row["ai_provider"] = "openai"
        db = self._make_db(row)
        with patch("app.api.routes.settings._get_logo_signed_url", return_value=None):
            result = await get_profile(current_user=user, db=db)
        assert result["data"]["api_key_preview"] == "sk-...xxxx"

    @pytest.mark.asyncio
    async def test_no_preview_claude_prefix(self, user):
        from app.api.routes.settings import get_profile
        row = self.base_row()
        row["ai_provider"] = "claude"
        db = self._make_db(row)
        with patch("app.api.routes.settings._get_logo_signed_url", return_value=None):
            result = await get_profile(current_user=user, db=db)
        assert result["data"]["api_key_preview"] == "sk-ant-...xxxx"

    @pytest.mark.asyncio
    async def test_no_preview_other_prefix(self, user):
        from app.api.routes.settings import get_profile
        row = self.base_row()
        row["ai_provider"] = "gemini"
        db = self._make_db(row)
        with patch("app.api.routes.settings._get_logo_signed_url", return_value=None):
            result = await get_profile(current_user=user, db=db)
        assert result["data"]["api_key_preview"] == "AIza... or AQ.......xxxx"


class TestUpdateProfileSuccess:
    """Cover update_profile success path (lines 155-169)"""

    @pytest.mark.asyncio
    async def test_success_updates_and_returns(self):
        from app.api.routes.settings import update_profile, ProfileUpdateRequest
        from datetime import datetime, timezone

        row_dict = {"full_name": "New Name", "updated_at": datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)}

        class _DB:
            def __init__(self):
                self.call_n = 0
                self.committed = False
            async def execute(self, query, params=None):
                self.call_n += 1
                return self
            async def commit(self):
                self.committed = True
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return row_dict if self.call_n >= 2 else None
            def all(self):
                return []

        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"

        db = _DB()
        body = ProfileUpdateRequest(full_name="New Name")
        result = await update_profile(body=body, current_user=u, db=db)

        assert result["success"] is True
        assert result["data"]["full_name"] == "New Name"
        assert db.committed


class TestSaveApiKeyInvalidProvider:
    """Cover save_api_key invalid provider raises 400 (line 188)"""

    @pytest.mark.asyncio
    async def test_invalid_provider_raises_400(self):
        from app.api.routes.settings import save_api_key, ApiKeyRequest
        from fastapi import HTTPException
        from starlette.requests import Request

        scope = {
            "type": "http", "method": "POST", "path": "/settings/api-key",
            "headers": [(b"authorization", b"Bearer test")],
            "query_string": b"", "client": ("127.0.0.1", 8000),
            "scheme": "http", "server": ("test", 80), "root_path": "",
        }
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        mock_request = Request(scope, receive=receive)

        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()

        with patch("slowapi.extension.Limiter._check_request_limit"):
            with pytest.raises(HTTPException) as exc:
                await save_api_key(
                    request=mock_request,
                    body=ApiKeyRequest(provider="invalid_provider", api_key="sk-test"),
                    current_user=u,
                    db=db,
                )
        assert exc.value.status_code == 400
        assert "Provider must be one of" in str(exc.value.detail)


class TestUpdateBranding:
    """Cover update_branding full function (lines 273-346)"""

    @pytest.fixture
    def user(self):
        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        u.tier = "pro"
        return u

    @pytest.mark.asyncio
    async def test_update_brand_color_only(self, user):
        from app.api.routes.settings import update_branding

        class _Row(dict):
            def get(self, k, default=None):
                return dict.get(self, k, default)

        row = _Row({"logo_url": None, "brand_color": "#FF5733", "company_name": None})

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                self.committed = True
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return row
            def all(self):
                return []

        db = _DB()
        with patch("app.api.routes.settings._get_logo_signed_url", return_value=None):
            result = await update_branding(
                brand_color="#FF5733",
                company_name=None,
                logo=None,
                current_user=user,
                db=db,
            )
        assert result["success"] is True
        assert result["data"]["brand_color"] == "#FF5733"
        assert db.committed

    @pytest.mark.asyncio
    async def test_update_company_name_only(self, user):
        from app.api.routes.settings import update_branding

        class _Row(dict):
            def get(self, k, default=None):
                return dict.get(self, k, default)

        row = _Row({"logo_url": None, "brand_color": None, "company_name": "Acme Corp"})

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                self.committed = True
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return row
            def all(self):
                return []

        db = _DB()
        with patch("app.api.routes.settings._get_logo_signed_url", return_value=None):
            result = await update_branding(
                brand_color=None,
                company_name="Acme Corp",
                logo=None,
                current_user=user,
                db=db,
            )
        assert result["success"] is True
        assert result["data"]["company_name"] == "Acme Corp"
        assert db.committed

    @pytest.mark.asyncio
    async def test_no_fields_raises_400(self, user):
        from app.api.routes.settings import update_branding
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()
        with pytest.raises(HTTPException) as exc:
            await update_branding(brand_color=None, company_name=None, logo=None, current_user=user, db=db)
        assert exc.value.status_code == 400
        assert "No fields to update" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_hex_color_raises_400(self, user):
        from app.api.routes.settings import update_branding
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()
        with pytest.raises(HTTPException) as exc:
            await update_branding(brand_color="not-a-color", logo=None, current_user=user, db=db)
        assert exc.value.status_code == 400
        assert "valid hex color" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_with_logo_upload(self, user):
        from app.api.routes.settings import update_branding
        from unittest.mock import AsyncMock
        from PIL import Image
        import io

        img = Image.new("RGB", (50, 50), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        png_bytes = buf.read()

        logo = MagicMock()
        logo.filename = "logo.png"
        logo.content_type = "image/png"
        logo.read = AsyncMock(return_value=png_bytes)

        class _Row(dict):
            def get(self, k, default=None):
                return dict.get(self, k, default)

        row = _Row({"logo_url": "logos/u/logo.png", "brand_color": None, "company_name": None})

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                self.committed = True
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return row
            def all(self):
                return []

        db = _DB()
        with patch("app.api.routes.settings._get_logo_signed_url", return_value="https://supabase.co/logo.png?token=abc"):
            with patch("app.api.routes.settings._run_sync"):
                with patch("app.api.routes.settings._get_supabase"):
                    result = await update_branding(
                        brand_color=None,
                        company_name=None,
                        logo=logo,
                        current_user=user,
                        db=db,
                    )
        assert result["success"] is True
        assert result["data"]["logo_url"] == "https://supabase.co/logo.png?token=abc"
        assert isinstance(result["data"]["suggested_colors"], list)
        assert len(result["data"]["suggested_colors"]) > 0
        assert db.committed


class TestUpdateTheme:
    """Cover update_theme (lines 363-368)"""

    @pytest.mark.asyncio
    async def test_update_theme_success(self):
        from app.api.routes.settings import update_theme, ThemeUpdateRequest

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
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

        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"

        db = _DB()
        body = ThemeUpdateRequest(theme="dark")
        result = await update_theme(body=body, current_user=u, db=db)
        assert result["success"] is True
        assert result["data"]["theme"] == "dark"
        assert db.committed


class TestDeleteAccount:
    """Cover delete_account (lines 371-436) including storage cleanup error (416-417)"""

    @pytest.fixture
    def user(self):
        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        u.email = "user@example.com"
        u.logo_url = "logos/user123/logo.png"
        return u

    @pytest.mark.asyncio
    async def test_email_mismatch_raises_400(self, user):
        from app.api.routes.settings import delete_account, DeleteAccountRequest
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()
        body = DeleteAccountRequest(email="wrong@example.com")
        with pytest.raises(HTTPException) as exc:
            await delete_account(body=body, current_user=user, db=db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_success_deletes_account(self, user):
        from app.api.routes.settings import delete_account, DeleteAccountRequest

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                qs = str(query)
                if "FROM uploads" in qs:
                    self._rows = [{"file_url": "uploads/file1.csv"}, {"file_url": "uploads/file2.csv"}]
                elif "FROM reports" in qs:
                    self._rows = [{"pdf_url": "reports/r1.pdf", "ppt_url": "reports/r1.pptx"}]
                elif "DELETE FROM users" in qs:
                    self._rows = []
                else:
                    self._rows = []
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
                return self._rows

        db = _DB()
        body = DeleteAccountRequest(email="user@example.com")

        with patch("app.api.routes.settings._run_sync"):
            with patch("app.api.routes.settings._get_supabase") as mock_get_supabase:
                mock_get_supabase.return_value.auth.admin.delete_user.return_value = None
                result = await delete_account(body=body, current_user=user, db=db)

        assert result["success"] is True
        assert result["data"]["deleted"] is True
        assert db.committed

    @pytest.mark.asyncio
    async def test_storage_cleanup_error_continues(self, user):
        """Cover lines 416-417: storage cleanup error is non-fatal"""
        from app.api.routes.settings import delete_account, DeleteAccountRequest

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                qs = str(query)
                if "FROM uploads" in qs:
                    self._rows = [{"file_url": "uploads/file.csv"}]
                elif "FROM reports" in qs:
                    self._rows = []
                elif "DELETE FROM users" in qs:
                    self._rows = []
                else:
                    self._rows = []
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
                return self._rows

        db = _DB()
        body = DeleteAccountRequest(email="user@example.com")

        with patch("app.api.routes.settings._run_sync", side_effect=Exception("Storage error")):
            with patch("app.api.routes.settings._get_supabase") as mock_get_supabase:
                mock_get_supabase.return_value.auth.admin.delete_user.return_value = None
                result = await delete_account(body=body, current_user=user, db=db)

        assert result["success"] is True
        assert db.committed

    @pytest.mark.asyncio
    async def test_auth_delete_404_continues(self, user):
        from app.api.routes.settings import delete_account, DeleteAccountRequest
        from gotrue.errors import AuthApiError

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                qs = str(query)
                if "FROM uploads" in qs or "FROM reports" in qs:
                    self._rows = []
                elif "DELETE FROM users" in qs:
                    self._rows = []
                else:
                    self._rows = []
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
                return self._rows

        db = _DB()
        body = DeleteAccountRequest(email="user@example.com")

        auth_error = AuthApiError("User not found", status=404, code="user_not_found")
        with patch("app.api.routes.settings._run_sync"):
            with patch("app.api.routes.settings._get_supabase") as mock_get_supabase:
                mock_get_supabase.return_value.auth.admin.delete_user.side_effect = auth_error
                result = await delete_account(body=body, current_user=user, db=db)

        assert result["success"] is True
        assert db.committed


class TestCreateApiKey:
    """Cover create_api_key (lines 439-488)"""

    @pytest.fixture
    def user(self):
        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        u.tier = "agency"
        return u

    @pytest.mark.asyncio
    async def test_empty_name_raises_400(self, user):
        from app.api.routes.settings import create_api_key
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def scalar(self):
                return 0
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()
        with pytest.raises(HTTPException) as exc:
            await create_api_key(body={"name": ""}, current_user=user, db=db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_name_too_long_raises_400(self, user):
        from app.api.routes.settings import create_api_key
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def scalar(self):
                return 0
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()
        with pytest.raises(HTTPException) as exc:
            await create_api_key(body={"name": "x" * 101}, current_user=user, db=db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_max_keys_raises_400(self, user):
        from app.api.routes.settings import create_api_key
        from fastapi import HTTPException

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def scalar(self):
                return 10
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        db = _DB()
        with patch("app.api.routes.settings._generate_api_key", return_value=("raw_key", "nax_abc", "xyz", "hash123")):
            with pytest.raises(HTTPException) as exc:
                await create_api_key(body={"name": "My Key"}, current_user=user, db=db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_success_creates_key(self, user):
        from app.api.routes.settings import create_api_key
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                self.committed = True
            async def rollback(self):
                pass
            def scalar(self):
                return 0
            def mappings(self):
                return self
            def first(self):
                return {"id": "key-id-1", "created_at": now}
            def all(self):
                return []

        db = _DB()
        with patch("app.api.routes.settings._generate_api_key", return_value=("nax_abc123xyz", "nax_abc", "xyz", "hash123")):
            result = await create_api_key(body={"name": "My API Key"}, current_user=user, db=db)

        assert result["name"] == "My API Key"
        assert result["key"] == "nax_abc123xyz"
        assert result["key_prefix"] == "nax_abc"
        assert result["key_suffix"] == "xyz"
        assert db.committed


class TestListApiKeys:
    """Cover list_api_keys (lines 491-516)"""

    @pytest.mark.asyncio
    async def test_returns_list_of_keys(self):
        from app.api.routes.settings import list_api_keys
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        rows = [
            {"id": "key-1", "name": "Dev Key", "key_prefix": "nax_abc", "key_suffix": "xyz1",
             "created_at": now, "last_used_at": now, "revoked_at": None},
            {"id": "key-2", "name": "Revoked Key", "key_prefix": "nax_def", "key_suffix": "xyz2",
             "created_at": now, "last_used_at": None, "revoked_at": now},
        ]

        class _DB:
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return rows

        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        u.tier = "agency"

        db = _DB()
        result = await list_api_keys(current_user=u, db=db)

        assert len(result) == 2
        assert result[0]["name"] == "Dev Key"
        assert result[0]["revoked"] is False
        assert result[1]["name"] == "Revoked Key"
        assert result[1]["revoked"] is True


class TestRevokeApiKey:
    """Cover revoke_api_key (lines 519-536)"""

    @pytest.mark.asyncio
    async def test_revoke_success(self):
        from app.api.routes.settings import revoke_api_key

        class _DB:
            def __init__(self):
                self.committed = False
                self.rowcount = 1
            async def execute(self, query, params=None):
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

        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        u.tier = "agency"

        db = _DB()
        result = await revoke_api_key(key_id="key-1", current_user=u, db=db)
        assert result["success"] is True
        assert db.committed

    @pytest.mark.asyncio
    async def test_revoke_not_found_raises_404(self):
        from app.api.routes.settings import revoke_api_key
        from fastapi import HTTPException

        class _DB:
            def __init__(self):
                self.rowcount = 0
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            async def rollback(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        u.tier = "agency"

        db = _DB()
        with pytest.raises(HTTPException) as exc:
            await revoke_api_key(key_id="nonexistent", current_user=u, db=db)
        assert exc.value.status_code == 404


class TestDeleteApiKeyPermanent:
    """Cover delete_api_key_permanent (lines 539-550)"""

    @pytest.mark.asyncio
    async def test_permanent_delete_success(self):
        from app.api.routes.settings import delete_api_key_permanent

        class _DB:
            def __init__(self):
                self.committed = False
            async def execute(self, query, params=None):
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

        u = type("FakeUser", (), {})()
        u.id = "uuuuuuuu-uuuu-uuuu-uuuu-uuuuuuuuuuuu"
        u.tier = "agency"

        db = _DB()
        result = await delete_api_key_permanent(key_id="key-1", current_user=u, db=db)
        assert result["success"] is True
        assert db.committed
