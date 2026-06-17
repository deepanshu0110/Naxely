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


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_email_mismatch_rejected(self):
        from app.api.routes.settings import delete_account, DeleteAccountRequest
        from app.models.user import User

        user = User()
        user.id = "user-123"
        user.email = "actual@test.com"

        class FakeBody:
            email = "wrong@test.com"

        with pytest.raises(HTTPException) as exc:
            await delete_account(body=FakeBody(), current_user=user)
        assert exc.value.status_code == 400
        assert "does not match" in str(exc.value.detail).lower()

    @pytest.mark.asyncio
    async def test_full_deletion_flow(self):
        from app.api.routes.settings import delete_account
        from app.models.user import User

        user = User()
        user.id = "user-123"
        user.email = "delete@test.com"
        user.logo_url = "logos/user-123/logo.png"

        class FakeBody:
            email = "delete@test.com"

        upload_row = MagicMock()
        upload_row.__getitem__.side_effect = lambda k: "uploads/user-123/report.csv" if k == "file_url" else None

        report_pdf_row = MagicMock()
        report_pdf_row.__getitem__.side_effect = lambda k: "reports/user-123/r1/report.pdf" if k == "pdf_url" else "reports/user-123/r1/report.pptx"

        upload_result = MagicMock()
        upload_result.mappings.return_value.all.return_value = [upload_row]

        report_result = MagicMock()
        report_result.mappings.return_value.all.return_value = [report_pdf_row]

        delete_result = MagicMock()

        db = _AsyncDB([upload_result, report_result, delete_result])

        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage
        mock_auth_admin = MagicMock()
        mock_supabase.auth.admin = mock_auth_admin

        async def fake_run_sync(func, *args, **kwargs):
            return func(*args, **kwargs)

        call_order: list = []

        original_db_execute = db.execute
        async def tracking_execute(query, params=None):
            call_order.append(("db_execute", str(query)))
            return await original_db_execute(query, params)
        db.execute = tracking_execute

        original_auth_delete = mock_auth_admin.delete_user
        def tracking_auth_delete(*args, **kwargs):
            call_order.append("auth_delete")
            return original_auth_delete(*args, **kwargs)
        mock_auth_admin.delete_user = tracking_auth_delete

        with patch("app.api.routes.settings._get_supabase", return_value=mock_supabase):
            with patch("app.api.routes.settings._run_sync", fake_run_sync):
                resp = await delete_account(body=FakeBody(), current_user=user, db=db)

        assert resp["success"] is True
        assert resp["data"]["deleted"] is True

        auth_pos = None
        delete_pos = None
        for i, entry in enumerate(call_order):
            if entry == "auth_delete":
                auth_pos = i
            elif isinstance(entry, tuple) and "DELETE FROM users" in entry[1]:
                delete_pos = i

        assert auth_pos is not None, "auth.admin.delete_user was never called"
        assert delete_pos is not None, "DELETE FROM users was never called"
        assert auth_pos < delete_pos, "Auth deletion must happen before DB row deletion"

        assert mock_bucket.remove.called
        assert original_auth_delete.call_args[0][0] == "user-123"

    @pytest.mark.asyncio
    async def test_no_storage_paths(self):
        from app.api.routes.settings import delete_account
        from app.models.user import User

        user = User()
        user.id = "user-456"
        user.email = "nostorage@test.com"
        user.logo_url = None

        class FakeBody:
            email = "nostorage@test.com"

        empty_upload_result = MagicMock()
        empty_upload_result.mappings.return_value.all.return_value = []

        empty_report_result = MagicMock()
        empty_report_result.mappings.return_value.all.return_value = []

        delete_result = MagicMock()

        db = _AsyncDB([empty_upload_result, empty_report_result, delete_result])

        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage
        mock_auth_admin = MagicMock()
        mock_supabase.auth.admin = mock_auth_admin

        async def fake_run_sync(func, *args, **kwargs):
            return func(*args, **kwargs)

        with patch("app.api.routes.settings._get_supabase", return_value=mock_supabase):
            with patch("app.api.routes.settings._run_sync", fake_run_sync):
                resp = await delete_account(body=FakeBody(), current_user=user, db=db)

        assert resp["success"] is True
        assert resp["data"]["deleted"] is True

        delete_stmt = [q for q in db.executed_queries if "DELETE FROM users" in q]
        assert len(delete_stmt) > 0

    @pytest.mark.asyncio
    async def test_auth_deletion_failure_aborts(self):
        from app.api.routes.settings import delete_account
        from app.models.user import User
        from gotrue.errors import AuthApiError

        user = User()
        user.id = "user-789"
        user.email = "fail@test.com"
        user.logo_url = None

        class FakeBody:
            email = "fail@test.com"

        upload_result = MagicMock()
        upload_result.mappings.return_value.all.return_value = []

        report_result = MagicMock()
        report_result.mappings.return_value.all.return_value = []

        db = _AsyncDB([upload_result, report_result])

        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage
        mock_auth_admin = MagicMock()
        mock_auth_admin.delete_user.side_effect = AuthApiError("Server error", 500, "server_error")
        mock_supabase.auth.admin = mock_auth_admin

        async def fake_run_sync(func, *args, **kwargs):
            return func(*args, **kwargs)

        with patch("app.api.routes.settings._get_supabase", return_value=mock_supabase):
            with patch("app.api.routes.settings._run_sync", fake_run_sync):
                with pytest.raises(HTTPException) as exc:
                    await delete_account(body=FakeBody(), current_user=user, db=db)

        assert exc.value.status_code == 502
        assert "please try again" in str(exc.value.detail).lower()

        delete_stmt = [q for q in db.executed_queries if "DELETE FROM users" in q]
        assert len(delete_stmt) == 0, "DB row must NOT be deleted when Auth deletion fails"

    @pytest.mark.asyncio
    async def test_auth_deletion_already_gone(self):
        from app.api.routes.settings import delete_account
        from app.models.user import User
        from gotrue.errors import AuthApiError

        user = User()
        user.id = "user-101112"
        user.email = "alreadygone@test.com"
        user.logo_url = None

        class FakeBody:
            email = "alreadygone@test.com"

        upload_result = MagicMock()
        upload_result.mappings.return_value.all.return_value = []

        report_result = MagicMock()
        report_result.mappings.return_value.all.return_value = []

        delete_result = MagicMock()

        db = _AsyncDB([upload_result, report_result, delete_result])

        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage
        mock_auth_admin = MagicMock()
        mock_auth_admin.delete_user.side_effect = AuthApiError("User not found", 404, "user_not_found")
        mock_supabase.auth.admin = mock_auth_admin

        async def fake_run_sync(func, *args, **kwargs):
            return func(*args, **kwargs)

        with patch("app.api.routes.settings._get_supabase", return_value=mock_supabase):
            with patch("app.api.routes.settings._run_sync", fake_run_sync):
                resp = await delete_account(body=FakeBody(), current_user=user, db=db)

        assert resp["success"] is True
        assert resp["data"]["deleted"] is True

        delete_stmt = [q for q in db.executed_queries if "DELETE FROM users" in q]
        assert len(delete_stmt) > 0, "DB row must be deleted when Auth user is already gone"
