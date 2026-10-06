import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


class _AsyncDB:
    def __init__(self, results):
        self.results = results
        self.call_count = 0
        self.executed_queries = []

    async def execute(self, query, params=None):
        self.executed_queries.append(str(query))
        result = self.results[self.call_count]
        self.call_count += 1
        return result

    async def commit(self):
        pass

    async def rollback(self):
        pass


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_missing_auth_header(self):
        from app.api.deps import get_current_user

        with pytest.raises(HTTPException) as exc:
            await get_current_user(authorization=None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_auth_scheme(self):
        from app.api.deps import get_current_user

        with pytest.raises(HTTPException) as exc:
            await get_current_user(authorization="Token abc123")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_bad_token_payload(self):
        from app.api.deps import get_current_user

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = {}
            with pytest.raises(HTTPException) as exc:
                await get_current_user(authorization="Bearer some.jwt.token")
            assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_exists_in_db(self):
        from app.api.deps import get_current_user

        mock_row = MagicMock()
        mock_row.items.return_value = [
            ("id", "user-123"), ("email", "test@test.com"), ("tier", "free"),
        ]
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = mock_row
        db = _AsyncDB([mock_result])

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = {"sub": "user-123", "email": "test@test.com"}
            user = await get_current_user(
                authorization="Bearer valid.jwt.token",
                db=db,
            )
            assert user is not None
            assert user.id == "user-123"

    @pytest.mark.asyncio
    async def test_user_fallback_creation(self):
        from app.api.deps import get_current_user

        first_result = MagicMock()
        first_result.mappings.return_value.first.return_value = None

        mock_new_row = MagicMock()
        mock_new_row.items.return_value = [
            ("id", "user-123"), ("email", "new@test.com"),
            ("full_name", "New User"), ("tier", "free"),
        ]
        second_result = MagicMock()
        second_result.mappings.return_value.first.return_value = mock_new_row

        db = _AsyncDB([first_result, first_result, second_result])

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = {
                "sub": "user-123",
                "email": "new@test.com",
                "user_metadata": {"full_name": "New User"},
            }
            user = await get_current_user(
                authorization="Bearer new.user.jwt",
                db=db,
            )
            assert user is not None
            assert user.email == "new@test.com"
        assert len(db.executed_queries) >= 2

    @pytest.mark.asyncio
    async def test_user_fallback_fails(self):
        # No row for this id after the upsert = email belongs to another id.
        # True identity mismatch: 409, never 500 (NAXELY-BACKEND-8).
        from app.api.deps import get_current_user

        none_result = MagicMock()
        none_result.mappings.return_value.first.return_value = None

        db = _AsyncDB([none_result, none_result, none_result])

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = {"sub": "user-123", "email": "fail@test.com"}
            with pytest.raises(HTTPException) as exc:
                await get_current_user(
                    authorization="Bearer fail.jwt.token",
                    db=db,
                )
            assert exc.value.status_code == 409
            assert exc.value.detail == "This email is linked to another account. Contact support."

    @pytest.mark.asyncio
    async def test_upsert_has_no_conflict_target(self):
        # Regression for NAXELY-BACKEND-8: ON CONFLICT (id) left the email
        # index as a non-arbiter, so concurrent same-id inserts raised
        # users_email_key. Every unique index must be an arbiter.
        from app.api.deps import get_current_user

        first_result = MagicMock()
        first_result.mappings.return_value.first.return_value = None

        mock_new_row = MagicMock()
        mock_new_row.items.return_value = [
            ("id", "user-123"), ("email", "race@test.com"), ("tier", "free"),
        ]
        second_result = MagicMock()
        second_result.mappings.return_value.first.return_value = mock_new_row

        db = _AsyncDB([first_result, first_result, second_result])

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify:
            mock_verify.return_value = {"sub": "user-123", "email": "race@test.com"}
            user = await get_current_user(
                authorization="Bearer race.jwt.token",
                db=db,
            )
            assert user is not None
        inserts = [q for q in db.executed_queries if "INSERT INTO users" in q]
        assert len(inserts) == 1
        assert "ON CONFLICT DO NOTHING" in inserts[0]
        assert "ON CONFLICT (id)" not in inserts[0]

    @pytest.mark.asyncio
    async def test_email_mismatch_alert_has_no_email(self):
        from app.api.deps import get_current_user

        none_result = MagicMock()
        none_result.mappings.return_value.first.return_value = None

        db = _AsyncDB([none_result, none_result, none_result])
        rolled_back = []

        orig_rollback = db.rollback

        async def tracking_rollback():
            rolled_back.append(True)
            await orig_rollback()

        db.rollback = tracking_rollback

        with patch("app.api.deps.verify_supabase_jwt") as mock_verify, patch(
            "app.utils.error_notifier.notify_telegram_error"
        ) as mock_notify:
            mock_verify.return_value = {"sub": "user-123", "email": "taken@test.com"}
            with pytest.raises(HTTPException) as exc:
                await get_current_user(
                    authorization="Bearer taken.jwt.token",
                    db=db,
                )
            assert exc.value.status_code == 409
        assert rolled_back, "session was not rolled back before the 409"
        assert mock_notify.call_count == 1
        alert_text = " ".join(str(a) for a in mock_notify.call_args[0])
        assert "taken@test.com" not in alert_text
        assert "user-123" in alert_text

    @pytest.mark.asyncio
    async def test_engine_hides_parameters(self):
        from app.core.database import engine

        assert engine.sync_engine.hide_parameters is True

    @pytest.mark.asyncio
    async def test_sentry_init_disables_local_variables(self):
        import importlib
        import app.main as main_module
        from app.core.config import settings

        with patch.object(settings, "ENVIRONMENT", "production"), patch.object(
            settings, "SENTRY_DSN", "https://example@sentry.io/1"
        ), patch("sentry_sdk.init") as mock_init:
            importlib.reload(main_module)
        assert mock_init.call_count == 1
        kwargs = mock_init.call_args[1]
        assert kwargs.get("send_default_pii") is False
        assert kwargs.get("include_local_variables") is False


class TestCheckReportLimit:
    @pytest.mark.asyncio
    async def test_free_tier_within_limit(self):
        from app.api.deps import check_report_limit
        from app.models.user import User

        user = User()
        user.tier = "free"
        user.reports_this_month = 2
        await check_report_limit(current_user=user)

    @pytest.mark.asyncio
    async def test_free_tier_at_limit_raises(self):
        from app.api.deps import check_report_limit
        from app.models.user import User

        user = User()
        user.tier = "free"
        user.reports_this_month = 3
        with pytest.raises(HTTPException) as exc:
            await check_report_limit(current_user=user)
        assert exc.value.status_code == 402

    @pytest.mark.asyncio
    async def test_pro_tier_no_limit(self):
        from app.api.deps import check_report_limit
        from app.models.user import User

        user = User()
        user.tier = "pro"
        user.reports_this_month = 999
        await check_report_limit(current_user=user)

    @pytest.mark.asyncio
    async def test_agency_tier_no_limit(self):
        from app.api.deps import check_report_limit
        from app.models.user import User

        user = User()
        user.tier = "agency"
        user.reports_this_month = 999
        await check_report_limit(current_user=user)


class TestCheckProTier:
    @pytest.mark.asyncio
    async def test_pro_tier_passes(self):
        from app.api.deps import require_pro_or_above
        from app.models.user import User

        user = User()
        user.tier = "pro"
        result = require_pro_or_above(current_user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_agency_tier_passes(self):
        from app.api.deps import require_pro_or_above
        from app.models.user import User

        user = User()
        user.tier = "agency"
        result = require_pro_or_above(current_user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_free_tier_fails(self):
        from app.api.deps import require_pro_or_above
        from app.models.user import User

        user = User()
        user.tier = "free"
        with pytest.raises(HTTPException) as exc:
            require_pro_or_above(current_user=user)
        assert exc.value.status_code == 403


class TestCheckAgencyTier:
    @pytest.mark.asyncio
    async def test_agency_tier_passes(self):
        from app.api.deps import require_agency
        from app.models.user import User

        user = User()
        user.tier = "agency"
        result = require_agency(current_user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_free_tier_fails(self):
        from app.api.deps import require_agency
        from app.models.user import User

        user = User()
        user.tier = "free"
        with pytest.raises(HTTPException) as exc:
            require_agency(current_user=user)
        assert exc.value.status_code == 403