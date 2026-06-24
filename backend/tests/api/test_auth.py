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
            assert exc.value.status_code == 401


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