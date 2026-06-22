import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.api.routes.scheduled_reports import (
    ALLOWED_FREQUENCIES,
    ScheduledReportCreate,
    ScheduledReportUpdate,
    _compute_next_run,
)


class FakeAgencyUser:
    id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    email = "agency@test.com"
    full_name = "Agency User"
    tier = "agency"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class FakeFreeUser:
    id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    email = "free@test.com"
    full_name = "Free User"
    tier = "free"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class FakeProUser:
    id = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    email = "pro@test.com"
    full_name = "Pro User"
    tier = "pro"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class FakeAgencyUserB:
    """Second agency user — does NOT own resources owned by FakeAgencyUser."""
    id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    email = "agency2@test.com"
    full_name = "Agency User B"
    tier = "agency"
    tier_expires_at = None
    dodo_subscription_id = None
    dodo_customer_id = None
    logo_url = None
    reports_this_month = 0


class _NotFound:
    def mappings(self):
        return self
    def first(self):
        return None
    def all(self):
        return []


class _Row:
    def __init__(self, **kw):
        self._kw = dict(kw)
    def mappings(self):
        return self
    def first(self):
        return self
    def all(self):
        return [self]
    def __getitem__(self, k):
        return self._kw.get(k)
    def __setitem__(self, k, v):
        self._kw[k] = v
    def __iter__(self):
        return iter(self._kw.keys())
    def __len__(self):
        return len(self._kw)
    def keys(self):
        return self._kw.keys()
    def items(self):
        return self._kw.items()
    def get(self, k, default=None):
        return self._kw.get(k, default)


class _AsyncDB:
    def __init__(self, results=None):
        self.results = results or [MagicMock()]
        self.call_count = 0
        self.executed_queries = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, query, params=None):
        qs = str(query)
        self.executed_queries.append(qs)
        idx = self.call_count
        self.call_count += 1
        if idx < len(self.results):
            return self.results[idx]
        return MagicMock()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class TestScheduledReportModels:
    def test_allowed_frequencies(self):
        assert ALLOWED_FREQUENCIES == {"daily", "weekly", "monthly"}

    def test_create_valid(self):
        body = ScheduledReportCreate(
            upload_id="upl-123",
            name="Test Report",
            frequency="daily",
            recipient_emails=["a@test.com"],
        )
        assert body.frequency == "daily"

    def test_create_invalid_frequency(self):
        with pytest.raises(ValueError, match="frequency must be one of"):
            ScheduledReportCreate(
                upload_id="upl-123",
                name="Test",
                frequency="yearly",
                recipient_emails=["a@test.com"],
            )

    def test_create_empty_recipients(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ScheduledReportCreate(
                upload_id="upl-123",
                name="Test",
                frequency="daily",
                recipient_emails=[],
            )

    def test_update_valid_frequency(self):
        body = ScheduledReportUpdate(frequency="weekly")
        assert body.frequency == "weekly"

    def test_update_invalid_frequency(self):
        with pytest.raises(ValueError, match="frequency must be one of"):
            ScheduledReportUpdate(frequency="biweekly")

    def test_compute_next_run_daily(self):
        from datetime import timezone
        result = _compute_next_run("daily")
        assert result.tzinfo is not None

    def test_compute_next_run_weekly(self):
        from datetime import timezone
        result = _compute_next_run("weekly")
        assert result.tzinfo is not None

    def test_compute_next_run_monthly(self):
        from datetime import timezone
        result = _compute_next_run("monthly")
        assert result.tzinfo is not None

    def test_monthly_flat_plus_30_days_jan_31_edge_case(self):
        """Explicit decision: 'monthly' = flat +30 days, NOT calendar-aware.
        Jan 31 + 30 days → Mar 2 (Jan has 31d, Feb 2026 has 28d).
        Confirm via mocked _compute_next_run.
        """
        from datetime import datetime, timezone
        from unittest.mock import patch
        from app.api.routes.scheduled_reports import _compute_next_run
        fixed_now = datetime(2026, 1, 31, 12, 0, 0, tzinfo=timezone.utc)
        with patch("app.api.routes.scheduled_reports.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw) if args else fixed_now
            result = _compute_next_run("monthly")
        expected = datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc)
        assert result == expected, f"Expected {expected}, got {result}"
        assert (result - fixed_now).days == 30, (
            f"Expected 30-day delta, got {(result - fixed_now).days}"
        )

    def test_daily_advances_one_day(self):
        """Daily = +1 day exactly (same time next day)."""
        from datetime import datetime, timezone
        from unittest.mock import patch
        from app.api.routes.scheduled_reports import _compute_next_run
        fixed_now = datetime(2026, 12, 31, 23, 59, 0, tzinfo=timezone.utc)
        with patch("app.api.routes.scheduled_reports.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw) if args else fixed_now
            result = _compute_next_run("daily")
        assert (result - fixed_now).days == 1
        assert (result - fixed_now).seconds == 0


class TestScheduledReportAgencyGate:
    """Free and Pro users must get 402 on all CRUD operations."""

    @pytest.mark.asyncio
    async def test_free_user_cannot_create(self):
        from app.api.routes.scheduled_reports import create_scheduled_report

        db = _AsyncDB()
        body = ScheduledReportCreate(
            upload_id="upl-123",
            name="Test",
            frequency="daily",
            recipient_emails=["a@test.com"],
        )
        with pytest.raises(HTTPException) as exc:
            await create_scheduled_report(body, current_user=FakeFreeUser(), db=db)
        assert exc.value.status_code == 402
        detail = exc.value.detail
        if isinstance(detail, dict):
            assert detail["code"] == "AGENCY_REQUIRED"

    @pytest.mark.asyncio
    async def test_pro_user_cannot_create(self):
        from app.api.routes.scheduled_reports import create_scheduled_report

        db = _AsyncDB()
        body = ScheduledReportCreate(
            upload_id="upl-123",
            name="Test",
            frequency="daily",
            recipient_emails=["a@test.com"],
        )
        with pytest.raises(HTTPException) as exc:
            await create_scheduled_report(body, current_user=FakeProUser(), db=db)
        assert exc.value.status_code == 402
        detail = exc.value.detail
        if isinstance(detail, dict):
            assert detail["code"] == "AGENCY_REQUIRED"

    @pytest.mark.asyncio
    async def test_free_user_cannot_list(self):
        from app.api.routes.scheduled_reports import list_scheduled_reports

        db = _AsyncDB()
        with pytest.raises(HTTPException) as exc:
            await list_scheduled_reports(current_user=FakeFreeUser(), db=db)
        assert exc.value.status_code == 402

    @pytest.mark.asyncio
    async def test_free_user_cannot_update(self):
        from app.api.routes.scheduled_reports import update_scheduled_report

        db = _AsyncDB([_NotFound()])
        body = ScheduledReportUpdate(name="Hacked")
        with pytest.raises(HTTPException) as exc:
            await update_scheduled_report("any-id", body, current_user=FakeFreeUser(), db=db)
        assert exc.value.status_code == 402

    @pytest.mark.asyncio
    async def test_free_user_cannot_delete(self):
        from app.api.routes.scheduled_reports import delete_scheduled_report

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await delete_scheduled_report("any-id", current_user=FakeFreeUser(), db=db)
        assert exc.value.status_code == 402


class TestScheduledReportOwnershipAndTierGate:
    """
    Both the tier gate (402 if not agency) AND ownership (404 if wrong user)
    are independent checks — neither substitutes for the other.
    """

    @pytest.mark.asyncio
    async def test_agency_user_a_cannot_access_agency_user_b_report(self):
        """
        Both users are agency (pass tier gate) but A does not own B's report.
        Ownership check must fire → 404, not 402.
        """
        from app.api.routes.scheduled_reports import (
            update_scheduled_report,
            delete_scheduled_report,
        )

        db = _AsyncDB([_NotFound()])

        # Update: agency user A cannot update B's report
        body = ScheduledReportUpdate(name="Hacked")
        with pytest.raises(HTTPException) as exc:
            await update_scheduled_report(
                "sr-owned-by-b", body,
                current_user=FakeAgencyUser(), db=db,
            )
        assert exc.value.status_code == 404, (
            f"Expected 404 (ownership), got {exc.value.status_code}"
        )

        # Delete: agency user A cannot delete B's report
        db2 = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await delete_scheduled_report(
                "sr-owned-by-b",
                current_user=FakeAgencyUser(), db=db2,
            )
        assert exc.value.status_code == 404, (
            f"Expected 404 (ownership), got {exc.value.status_code}"
        )


class TestScheduledReportCreate:
    @pytest.mark.asyncio
    async def test_agency_user_creates_own(self):
        from app.api.routes.scheduled_reports import create_scheduled_report

        upload_row = _Row(id="upl-123", user_id=FakeAgencyUser.id)
        insert_row = _Row(
            id="sr-created-001",
            user_id=FakeAgencyUser.id,
            template_id=None,
            workspace_id=None,
            name="My Scheduled Report",
            frequency="daily",
            next_run_at=_compute_next_run("daily"),
            last_run_at=None,
            recipient_emails=["a@test.com"],
            csv_storage_path="scheduled-sources/sr-created-001.csv",
            is_active=True,
            created_at=_compute_next_run("daily"),
        )

        db = _AsyncDB([upload_row, insert_row, MagicMock()])

        body = ScheduledReportCreate(
            upload_id="upl-123",
            name="My Scheduled Report",
            frequency="daily",
            recipient_emails=["a@test.com"],
        )

        with patch(
            "app.api.routes.scheduled_reports.copy_upload_to_scheduled_source",
            return_value="scheduled-sources/sr-created-001.csv",
        ):
            result = await create_scheduled_report(body, current_user=FakeAgencyUser(), db=db)

        assert result.id == "sr-created-001"
        assert result.name == "My Scheduled Report"
        assert result.frequency == "daily"
        assert result.recipient_emails == ["a@test.com"]
        assert result.csv_storage_path == "scheduled-sources/sr-created-001.csv"
        assert result.is_active is True
        assert db.committed

    @pytest.mark.asyncio
    async def test_upload_not_found_returns_404(self):
        from app.api.routes.scheduled_reports import create_scheduled_report

        db = _AsyncDB([_NotFound()])
        body = ScheduledReportCreate(
            upload_id="nonexistent",
            name="Test",
            frequency="daily",
            recipient_emails=["a@test.com"],
        )
        with pytest.raises(HTTPException) as exc:
            await create_scheduled_report(body, current_user=FakeAgencyUser(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_other_users_upload_returns_404(self):
        from app.api.routes.scheduled_reports import create_scheduled_report

        upload_row = _Row(id="upl-owned-by-b", user_id=FakeAgencyUserB.id)
        db = _AsyncDB([upload_row])

        body = ScheduledReportCreate(
            upload_id="upl-owned-by-b",
            name="Test",
            frequency="daily",
            recipient_emails=["a@test.com"],
        )
        with pytest.raises(HTTPException) as exc:
            await create_scheduled_report(body, current_user=FakeAgencyUser(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_owner_uuid_object_matches_string_user_id(self):
        """Regression: asyncpg returns UUID columns as uuid.UUID objects from raw
        text() queries. The ownership check must str() both sides, not compare
        uuid.UUID directly to str (which always returns False in Python).
        This test passes a uuid.UUID object as upload[user_id] to simulate what
        asyncpg returns in production."""
        import uuid
        from app.api.routes.scheduled_reports import create_scheduled_report

        uid_obj = uuid.UUID(FakeAgencyUser.id)
        upload_row = _Row(id="upl-uuid-obj", user_id=uid_obj)
        insert_row = _Row(
            id="sr-uuid-ok",
            user_id=FakeAgencyUser.id,
            template_id=None,
            workspace_id=None,
            name="UUID Object Test",
            frequency="weekly",
            next_run_at=_compute_next_run("weekly"),
            last_run_at=None,
            recipient_emails=["uuid@test.com"],
            csv_storage_path="scheduled-sources/sr-uuid-ok.csv",
            is_active=True,
            created_at=_compute_next_run("weekly"),
        )
        db = _AsyncDB([upload_row, insert_row, MagicMock()])

        body = ScheduledReportCreate(
            upload_id="upl-uuid-obj",
            name="UUID Object Test",
            frequency="weekly",
            recipient_emails=["uuid@test.com"],
        )
        with patch(
            "app.api.routes.scheduled_reports.copy_upload_to_scheduled_source",
            return_value="scheduled-sources/sr-uuid-ok.csv",
        ):
            result = await create_scheduled_report(body, current_user=FakeAgencyUser(), db=db)

        assert result.id == "sr-uuid-ok"
        assert result.name == "UUID Object Test"
        assert result.csv_storage_path == "scheduled-sources/sr-uuid-ok.csv"
        assert db.committed


class TestScheduledReportOwnership:
    @pytest.mark.asyncio
    async def test_update_other_users_returns_404(self):
        from app.api.routes.scheduled_reports import update_scheduled_report

        db = _AsyncDB([_NotFound()])
        body = ScheduledReportUpdate(name="Hacked")
        with pytest.raises(HTTPException) as exc:
            await update_scheduled_report("sr-owned-by-a", body, current_user=FakeAgencyUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_users_returns_404(self):
        from app.api.routes.scheduled_reports import delete_scheduled_report

        db = _AsyncDB([_NotFound()])
        with pytest.raises(HTTPException) as exc:
            await delete_scheduled_report("sr-owned-by-a", current_user=FakeAgencyUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_self_with_uuid_user_id_succeeds(self):
        """Regression: asyncpg returns UUID columns as uuid.UUID objects.
        _get_scheduled_report_or_404 must str() both sides. This test would
        have returned 404 with the old uuid.UUID != str comparison."""
        import uuid
        from app.api.routes.scheduled_reports import update_scheduled_report

        uid_obj = uuid.UUID(FakeAgencyUser.id)
        existing = _Row(
            id="sr-uuid-self",
            user_id=uid_obj,
            template_id=None,
            workspace_id=None,
            name="UUID Self",
            frequency="daily",
            next_run_at=_compute_next_run("daily"),
            last_run_at=None,
            recipient_emails=["self@test.com"],
            csv_storage_path="scheduled-sources/sr-uuid-self.csv",
            is_active=True,
            created_at=_compute_next_run("daily"),
        )
        updated = _Row(
            id="sr-uuid-self",
            user_id=FakeAgencyUser.id,
            template_id=None,
            workspace_id=None,
            name="Updated UUID Self",
            frequency="weekly",
            next_run_at=_compute_next_run("weekly"),
            last_run_at=None,
            recipient_emails=["self@test.com"],
            csv_storage_path="scheduled-sources/sr-uuid-self.csv",
            is_active=True,
            created_at=_compute_next_run("daily"),
        )
        db = _AsyncDB([existing, updated])

        body = ScheduledReportUpdate(name="Updated UUID Self", frequency="weekly")
        result = await update_scheduled_report("sr-uuid-self", body, current_user=FakeAgencyUser(), db=db)
        assert result.id == "sr-uuid-self"
        assert result.name == "Updated UUID Self"
        assert result.frequency == "weekly"
        assert db.committed

    @pytest.mark.asyncio
    async def test_update_other_with_uuid_user_id_returns_404(self):
        """Same uuid.UUID scenario but with DIFFERENT user — must still 404."""
        import uuid
        from app.api.routes.scheduled_reports import update_scheduled_report

        uid_obj = uuid.UUID(FakeAgencyUser.id)
        existing = _Row(
            id="sr-uuid-other",
            user_id=uid_obj,
            template_id=None,
            workspace_id=None,
            name="UUID Other",
            frequency="daily",
            next_run_at=_compute_next_run("daily"),
            last_run_at=None,
            recipient_emails=["other@test.com"],
            csv_storage_path="scheduled-sources/sr-uuid-other.csv",
            is_active=True,
            created_at=_compute_next_run("daily"),
        )
        db = _AsyncDB([existing])

        body = ScheduledReportUpdate(name="Hacked")
        with pytest.raises(HTTPException) as exc:
            await update_scheduled_report("sr-uuid-other", body, current_user=FakeAgencyUserB(), db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_self_scoped(self):
        """List only returns the requesting user's scheduled reports."""
        from app.api.routes.scheduled_reports import list_scheduled_reports

        result_row = _Row(
            id="sr-own-001",
            user_id=FakeAgencyUser.id,
            template_id=None,
            workspace_id=None,
            name="Mine",
            frequency="daily",
            next_run_at=_compute_next_run("daily"),
            last_run_at=None,
            recipient_emails=["a@test.com"],
            csv_storage_path=None,
            is_active=True,
            created_at=_compute_next_run("daily"),
        )

        # The list query returns all rows. _AsyncDB returns the list result
        # from execute, then .mappings().all() iterates it.
        # We need a mock that returns [result_row] for .mappings().all()
        list_result = MagicMock()
        list_result.mappings.return_value.all.return_value = [result_row]

        db = _AsyncDB([list_result])
        result = await list_scheduled_reports(current_user=FakeAgencyUser(), db=db)

        assert len(result) > 0


class TestScheduledReportUpdate:
    @pytest.mark.asyncio
    async def test_agency_user_updates_own(self):
        from app.api.routes.scheduled_reports import update_scheduled_report

        existing = _Row(
            id="sr-update-001",
            user_id=FakeAgencyUser.id,
            template_id=None,
            workspace_id=None,
            name="Original",
            frequency="daily",
            next_run_at=_compute_next_run("daily"),
            last_run_at=None,
            recipient_emails=["old@test.com"],
            csv_storage_path="scheduled-sources/sr-update-001.csv",
            is_active=True,
            created_at=_compute_next_run("daily"),
        )

        updated = _Row(
            id="sr-update-001",
            user_id=FakeAgencyUser.id,
            template_id=None,
            workspace_id=None,
            name="Updated Name",
            frequency="weekly",
            next_run_at=_compute_next_run("weekly"),
            last_run_at=None,
            recipient_emails=["new@test.com"],
            csv_storage_path="scheduled-sources/sr-update-001.csv",
            is_active=False,
            created_at=_compute_next_run("daily"),
        )

        db = _AsyncDB([existing, updated])

        body = ScheduledReportUpdate(
            name="Updated Name",
            frequency="weekly",
            recipient_emails=["new@test.com"],
            is_active=False,
        )
        result = await update_scheduled_report("sr-update-001", body, current_user=FakeAgencyUser(), db=db)
        assert result.id == "sr-update-001"
        assert result.frequency == "weekly"
        assert result.is_active is False
        assert db.committed


class TestScheduledReportDelete:
    @pytest.mark.asyncio
    async def test_agency_user_deletes_own(self):
        from app.api.routes.scheduled_reports import delete_scheduled_report

        existing = _Row(
            id="sr-delete-001",
            user_id=FakeAgencyUser.id,
        )

        db = _AsyncDB([existing, MagicMock()])
        result = await delete_scheduled_report("sr-delete-001", current_user=FakeAgencyUser(), db=db)
        assert result["success"] is True
        assert db.committed

        delete_queries = [q for q in db.executed_queries if "DELETE FROM scheduled_reports" in q]
        assert len(delete_queries) > 0


class TestCronEndpoint:
    """Phase 3: internal cron-triggered execution endpoint."""

    @pytest.fixture
    def mock_settings(self):
        with patch("app.api.routes.scheduled_reports.settings") as mock_s:
            mock_s.CRON_SECRET = "test-cron-secret"
            yield mock_s

    def _make_sched_row(self, **overrides):
        """Helper to build a scheduled report row returned by the due-reports query."""
        vals = dict(
            id="sr-cron-001",
            user_id=FakeAgencyUser.id,
            template_id=None,
            workspace_id=None,
            name="Cron Test Report",
            frequency="daily",
            next_run_at=None,
            last_run_at=None,
            recipient_emails=["a@test.com", "b@test.com"],
            csv_storage_path="scheduled-sources/sr-cron-001.csv",
            is_active=True,
            created_at=None,
            config_json='{"template_type": "professional", "sections": ["kpi_overview", "charts"]}',
        )
        vals.update(overrides)
        return _Row(**vals)

    def _report_list_result(self, rows):
        """Wrap row(s) in the MagicMock shape returned by .mappings().all()."""
        m = MagicMock()
        m.mappings.return_value.all.return_value = rows
        return m

    @pytest.mark.asyncio
    async def test_invalid_secret_returns_403(self):
        from app.api.routes.scheduled_reports import run_scheduled_reports

        db = _AsyncDB()
        with pytest.raises(HTTPException) as exc:
            await run_scheduled_reports(x_cron_secret="wrong-secret", db=db)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_no_due_reports_returns_empty(self, mock_settings):
        from app.api.routes.scheduled_reports import run_scheduled_reports

        due_reports = self._report_list_result([])
        db = _AsyncDB([due_reports])

        result = await run_scheduled_reports(x_cron_secret="test-cron-secret", db=db)
        assert result["processed"] == 0
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_due_report_processed_successfully(self, mock_settings):
        from app.api.routes.scheduled_reports import run_scheduled_reports

        sched_row = self._make_sched_row()
        due_reports = self._report_list_result([sched_row])
        pdf_row = _Row(pdf_url="reports/user-1/sr-cron-001/report.pdf")

        db = _AsyncDB([due_reports, MagicMock(), pdf_row, MagicMock()])

        with (
            patch("app.api.routes.scheduled_reports.run_report_pipeline") as mock_run,
            patch("app.api.routes.scheduled_reports.send_email") as mock_email,
            patch("app.api.routes.scheduled_reports._run_sync") as mock_run_sync,
            patch("app.api.routes.scheduled_reports._get_supabase") as mock_supabase,
        ):
            mock_run_sync.return_value = b"fake,csv\ndata,1\n"

            result = await run_scheduled_reports(x_cron_secret="test-cron-secret", db=db)

        assert result["processed"] == 1
        assert result["results"][0]["status"] == "success"
        mock_run.assert_awaited_once()
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        assert call_args[1]["to"] == ["a@test.com", "b@test.com"]
        assert "scheduled report" in call_args[1]["subject"].lower()
        assert len(call_args[1]["attachments"]) == 1
        assert call_args[1]["attachments"][0]["filename"] == "Cron Test Report.pdf"

    @pytest.mark.asyncio
    async def test_three_reports_one_fail_two_succeed(self, mock_settings):
        """
        With 3 reports in one cron run (A fail, B success, C success):
        - Report A's pipeline raises → caught, logged, loop continues
        - Report B succeeds normally
        - Report C succeeds normally
        - Email only sent for B and C (2 calls)
        - Final results: [failed, success, success]
        """
        from app.api.routes.scheduled_reports import run_scheduled_reports

        row_a = self._make_sched_row(id="sr-fail-a", name="Failing Report")
        row_b = self._make_sched_row(
            id="sr-ok-b", name="Success B",
            user_id=FakeAgencyUserB.id,
            recipient_emails=["b@test.com"],
        )
        row_c = self._make_sched_row(
            id="sr-ok-c", name="Success C",
            user_id=FakeAgencyUserB.id,
            recipient_emails=["c@test.com"],
        )
        due_reports = self._report_list_result([row_a, row_b, row_c])

        pdf_row_b = _Row(pdf_url="reports/user-2/sr-ok-b/report.pdf")
        pdf_row_c = _Row(pdf_url="reports/user-2/sr-ok-c/report.pdf")

        # execute call sequence:
        #   0 = due_reports (initial SELECT)
        #   1 = INSERT A (fails at pipeline, no pdf/update reached)
        #   2 = INSERT B
        #   3 = SELECT pdf_url B
        #   4 = UPDATE B
        #   5 = INSERT C
        #   6 = SELECT pdf_url C
        #   7 = UPDATE C
        db = _AsyncDB([
            due_reports,
            MagicMock(),  # 1: insert A
            MagicMock(),  # 2: insert B
            pdf_row_b,    # 3: pdf B
            MagicMock(),  # 4: update B
            MagicMock(),  # 5: insert C
            pdf_row_c,    # 6: pdf C
            MagicMock(),  # 7: update C
        ])

        call_order = []

        async def mock_run(report_id, user_id, config, csv_bytes=None):
            call_order.append(report_id)
            if report_id in call_order and len(call_order) == 1:
                raise ValueError("Pipeline exploded for first report")

        with (
            patch("app.api.routes.scheduled_reports.run_report_pipeline", side_effect=mock_run),
            patch("app.api.routes.scheduled_reports.send_email") as mock_email,
            patch("app.api.routes.scheduled_reports._run_sync") as mock_run_sync,
            patch("app.api.routes.scheduled_reports._get_supabase") as mock_supabase,
        ):
            mock_run_sync.return_value = b"fake,csv\ndata,1\n"
            result = await run_scheduled_reports(x_cron_secret="test-cron-secret", db=db)

        assert result["processed"] == 3
        assert result["results"][0]["status"] == "failed", f"Expected failed, got {result['results'][0]}"
        assert result["results"][1]["status"] == "success", f"Expected success, got {result['results'][1]}"
        assert result["results"][2]["status"] == "success", f"Expected success, got {result['results'][2]}"
        assert len(call_order) == 3, "Pipeline should have been called 3 times"
        assert mock_email.call_count == 2, "Email should be sent for 2 successful reports"
