import os
import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, AsyncMock

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("MASTER_ENCRYPTION_KEY", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", "")


class MockDB:
    """In-memory mock for AsyncSession that tracks state across calls."""

    def __init__(self):
        self._api_keys: dict[str, dict] = {}
        self._reports: dict[str, dict] = {}
        self._uploads: dict[str, dict] = {}
        self._users: dict[str, dict] = {}
        self.committed = False
        self._sequence = 0

    def add_user(self, user_id: str, tier: str = "agency"):
        self._users[user_id] = {
            "id": user_id,
            "tier": tier,
            "email": f"{tier}@test.com",
            "full_name": f"Test {tier.title()} User",
            "deleted_at": None,
        }

    async def execute(self, sql, params=None):
        self._sequence += 1
        raw = str(sql) if not isinstance(sql, str) else sql
        sql_str = ' '.join(raw.split())
        params = params or {}

        result = MagicMock()

        if "INSERT INTO api_keys" in sql_str and "RETURNING" in sql_str:
            key_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            self._api_keys[key_id] = {
                "id": key_id,
                "user_id": params.get("uid", ""),
                "name": params.get("name", ""),
                "key_hash": params.get("hash", ""),
                "key_prefix": params.get("prefix", ""),
                "key_suffix": params.get("suffix", ""),
                "created_at": now,
                "last_used_at": None,
                "revoked_at": None,
            }
            mappings = MagicMock()
            mappings.first.return_value = {"id": key_id, "created_at": now}
            result.mappings.return_value = mappings

        elif "SELECT COUNT(*) FROM api_keys" in sql_str:
            count = sum(
                1 for k in self._api_keys.values()
                if k["user_id"] == params.get("uid", "")
                and k["revoked_at"] is None
            )
            result.scalar.return_value = count

        elif "UPDATE api_keys SET revoked_at" in sql_str:
            key_id = str(params.get("id", ""))
            user_id = str(params.get("uid", ""))
            key = self._api_keys.get(key_id)
            if key:
                if key["user_id"] == user_id and key["revoked_at"] is None:
                    key["revoked_at"] = datetime.now(timezone.utc)
                    result.rowcount = 1
                elif key["user_id"] != user_id:
                    result.rowcount = 0
                else:
                    result.rowcount = 0
            else:
                result.rowcount = 0

        elif "FROM api_keys" in sql_str and "WHERE user_id" in sql_str:
            user_keys = [
                v for v in self._api_keys.values()
                if v["user_id"] == params.get("uid", "")
            ]
            user_keys.sort(key=lambda x: x["created_at"], reverse=True)
            mappings = MagicMock()
            mappings.all.return_value = user_keys
            result.mappings.return_value = mappings

        elif "FROM api_keys" in sql_str and "key_hash" in sql_str:
            hash_val = params.get("hash", "")
            match = None
            for v in self._api_keys.values():
                if v["key_hash"] == hash_val:
                    match = v
                    break
            if match:
                mappings = MagicMock()
                mappings.first.return_value = {
                    "id": match["id"],
                    "user_id": match["user_id"],
                    "revoked_at": match["revoked_at"],
                    "tier": "agency",
                }
                result.mappings.return_value = mappings
            else:
                result.mappings.return_value.first.return_value = None

        elif "FROM reports" in sql_str:
            report_id = params.get("id", "")
            report = self._reports.get(report_id)
            mappings = MagicMock()
            mappings.first.return_value = report
            result.mappings.return_value = mappings

        elif "FROM users" in sql_str and "WHERE id" in sql_str:
            uid = str(params.get("uid", "")) if params.get("uid") else ""
            if uid in self._users:
                mappings = MagicMock()
                mappings.first.return_value = self._users[uid]
                result.mappings.return_value = mappings
            else:
                result.mappings.return_value.first.return_value = None

        elif "INSERT INTO reports" in sql_str:
            report_id = params.get("id", "")
            self._reports[report_id] = {
                "id": report_id,
                "user_id": params.get("uid", ""),
                "title": params.get("title", ""),
                "status": "pending",
                "pdf_url": None,
                "error_message": None,
            }

        else:
            result.mappings.return_value.first.return_value = None
            result.mappings.return_value.all.return_value = []
            result.scalar.return_value = 0
            result.rowcount = 0

        return result

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass

    async def close(self):
        pass

    def add(self, obj):
        pass

    def add_all(self, objs):
        pass


_db_instance = None


def _get_mock_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = MockDB()
    return _db_instance


def _reset_mock_db():
    global _db_instance
    _db_instance = MockDB()


def _make_user(tier: str, user_id: str | None = None):
    u = MagicMock()
    u.id = user_id or str(uuid.uuid4())
    u.tier = tier
    u.email = f"{tier}@test.com"
    u.full_name = f"Test {tier.title()} User"
    u.encrypted_api_key = None
    u.api_key_iv = None
    u.ai_provider = "gemini"
    u.reports_this_month = 0
    u.logo_url = None
    u.company_name = None
    u.brand_color = "#6366F1"
    u.theme_preference = "light"
    u.has_completed_onboarding = True
    return u


def _set_deps(tier: str, user=None):
    from app.api import deps
    from app.main import app

    if user is None:
        user = _make_user(tier)

    mock_db = _get_mock_db()
    mock_db.add_user(str(user.id), tier=tier)

    app.dependency_overrides[deps.get_current_user] = lambda u=user: u
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    app.dependency_overrides[deps.check_report_limit] = lambda: None
    # require_byok, require_pro_or_above, require_agency are NOT overridden
    # They resolve through get_current_user, so swapping get_current_user
    # in a test body automatically swaps them too.
    return user


def _clear_deps():
    from app.main import app
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def app():
    from app.main import app
    return app


@pytest.fixture
def client(app):
    _reset_mock_db()
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture
def pro_user_token():
    _set_deps("pro")
    yield "fake-pro-token"
    _clear_deps()


@pytest.fixture
def agency_user_token():
    _set_deps("agency")
    yield "fake-agency-token"
    _clear_deps()


@pytest.fixture
def other_agency_user_token():
    other = _make_user("agency", user_id="other-agency-user-id")
    _set_deps("agency", user=other)
    yield "fake-other-agency-token"
    _clear_deps()
