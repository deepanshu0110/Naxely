import re
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
