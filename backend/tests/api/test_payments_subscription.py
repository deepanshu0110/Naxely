import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException


class FakeUser:
    id = "user-abc-123"
    email = "test@example.com"
    full_name = "Test User"
    tier = "free"
    dodo_subscription_id = None


class FakeProSubscriber:
    id = "user-pro-456"
    email = "pro@example.com"
    full_name = "Pro User"
    tier = "pro"
    dodo_subscription_id = "sub_pro_001"
    dodo_customer_id = "cust_pro_001"


class FakeAgencySubscriber:
    id = "user-agency-789"
    email = "agency@example.com"
    full_name = "Agency User"
    tier = "agency"
    dodo_subscription_id = "sub_agency_001"
    dodo_customer_id = "cust_agency_001"


def _mock_db_row(expires_at: datetime | None = None):
    row = MagicMock()
    row.get.return_value = expires_at
    row.__getitem__.side_effect = lambda k: expires_at if k == "tier_expires_at" else None
    return row


def _mock_db_result(row):
    m = MagicMock()
    m.mappings.return_value.first.return_value = row
    return m


def _fake_sub(**kwargs):
    sub = MagicMock()
    sub.scheduled_change = kwargs.get("scheduled_change")
    sub.cancel_at_next_billing_date = kwargs.get("cancel_at_next_billing_date", False)
    sub.subscription_id = kwargs.get("subscription_id", "sub_agency_001")
    sub.status = kwargs.get("status", "active")
    sub.next_billing_date = kwargs.get("next_billing_date", datetime(2026, 7, 18, tzinfo=timezone.utc))
    return sub


# ── GET /payments/subscription ─────────────────────────────────────────────────

class TestGetSubscriptionState:

    @pytest.mark.asyncio
    async def test_no_subscription_returns_has_false(self):
        from app.api.routes.payments import get_subscription_state

        result = await get_subscription_state(current_user=FakeUser())
        assert result["success"] is True
        assert result["data"]["has_subscription"] is False

    @pytest.mark.asyncio
    async def test_active_subscription_no_scheduled_change(self):
        from app.api.routes.payments import get_subscription_state

        sub = _fake_sub()
        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(return_value=sub)):
            result = await get_subscription_state(current_user=FakeAgencySubscriber())

        data = result["data"]
        assert data["has_subscription"] is True
        assert data["subscription_id"] == "sub_agency_001"
        assert data["status"] == "active"
        assert data["cancel_at_next_billing_date"] is False
        assert data["scheduled_change"] is None

    @pytest.mark.asyncio
    async def test_scheduled_plan_change_to_pro(self):
        from app.api.routes.payments import get_subscription_state

        change = MagicMock()
        change.id = "change_001"
        change.product_id = "prod_pro"
        change.effective_at = datetime(2026, 7, 18, tzinfo=timezone.utc)
        sub = _fake_sub(scheduled_change=change)

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=sub)):
                result = await get_subscription_state(current_user=FakeAgencySubscriber())

        scheduled = result["data"]["scheduled_change"]
        assert scheduled["id"] == "change_001"
        assert scheduled["planned_tier"] == "pro"
        assert scheduled["effective_at"] == "2026-07-18T00:00:00+00:00"

    @pytest.mark.asyncio
    async def test_scheduled_plan_change_to_agency(self):
        from app.api.routes.payments import get_subscription_state

        change = MagicMock()
        change.id = "change_002"
        change.product_id = "some-other-product"
        change.effective_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
        sub = _fake_sub(scheduled_change=change)

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=sub)):
                result = await get_subscription_state(current_user=FakeAgencySubscriber())

        assert result["data"]["scheduled_change"]["planned_tier"] == "agency"

    @pytest.mark.asyncio
    async def test_retrieve_failure_502(self):
        from app.api.routes.payments import get_subscription_state

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(side_effect=Exception("dodo down"))):
            with pytest.raises(HTTPException) as exc:
                await get_subscription_state(current_user=FakeAgencySubscriber())

        assert exc.value.status_code == 502
        assert "Failed to retrieve subscription state" in str(exc.value.detail)


# ── POST /payments/cancel-scheduled-change ─────────────────────────────────────

class TestCancelScheduledChange:

    @pytest.mark.asyncio
    async def test_no_subscription_400(self):
        from app.api.routes.payments import cancel_scheduled_change

        with pytest.raises(HTTPException) as exc:
            await cancel_scheduled_change(current_user=FakeUser())
        assert exc.value.status_code == 400
        assert "No active subscription found" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_retrieve_failure_502(self):
        from app.api.routes.payments import cancel_scheduled_change

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(side_effect=Exception("dodo down"))):
            with pytest.raises(HTTPException) as exc:
                await cancel_scheduled_change(current_user=FakeAgencySubscriber())
        assert exc.value.status_code == 502

    @pytest.mark.asyncio
    async def test_cancels_plan_change(self):
        from app.api.routes.payments import cancel_scheduled_change

        change = MagicMock()
        change.effective_at = datetime(2026, 7, 18, tzinfo=timezone.utc)
        sub = _fake_sub(scheduled_change=change)

        captured = {}

        async def fake_cancel_change_plan(**kwargs):
            captured.update(kwargs)

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(return_value=sub)):
            with patch("app.api.routes.payments.dodo.subscriptions.cancel_change_plan",
                       new=AsyncMock(side_effect=fake_cancel_change_plan)):
                result = await cancel_scheduled_change(current_user=FakeAgencySubscriber())

        assert captured["subscription_id"] == "sub_agency_001"
        assert result["success"] is True
        assert result["data"] == {"cancelled": True, "type": "plan_change"}

    @pytest.mark.asyncio
    async def test_cancel_change_plan_failure_502(self):
        from app.api.routes.payments import cancel_scheduled_change

        change = MagicMock()
        change.effective_at = datetime(2026, 7, 18, tzinfo=timezone.utc)
        sub = _fake_sub(scheduled_change=change)

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(return_value=sub)):
            with patch("app.api.routes.payments.dodo.subscriptions.cancel_change_plan",
                       new=AsyncMock(side_effect=Exception("dodo error"))):
                with pytest.raises(HTTPException) as exc:
                    await cancel_scheduled_change(current_user=FakeAgencySubscriber())
        assert exc.value.status_code == 502
        assert "Failed to cancel scheduled downgrade" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_unschedules_cancellation(self):
        from app.api.routes.payments import cancel_scheduled_change

        sub = _fake_sub(scheduled_change=None, cancel_at_next_billing_date=True)
        captured = {}

        async def fake_update(**kwargs):
            captured.update(kwargs)

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(return_value=sub)):
            with patch("app.api.routes.payments.dodo.subscriptions.update",
                       new=AsyncMock(side_effect=fake_update)):
                result = await cancel_scheduled_change(current_user=FakeAgencySubscriber())

        assert captured["subscription_id"] == "sub_agency_001"
        assert captured["cancel_at_next_billing_date"] is False
        assert result["success"] is True
        assert result["data"] == {"cancelled": True, "type": "cancellation"}

    @pytest.mark.asyncio
    async def test_unschedule_failure_502(self):
        from app.api.routes.payments import cancel_scheduled_change

        sub = _fake_sub(scheduled_change=None, cancel_at_next_billing_date=True)

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(return_value=sub)):
            with patch("app.api.routes.payments.dodo.subscriptions.update",
                       new=AsyncMock(side_effect=Exception("dodo error"))):
                with pytest.raises(HTTPException) as exc:
                    await cancel_scheduled_change(current_user=FakeAgencySubscriber())
        assert exc.value.status_code == 502

    @pytest.mark.asyncio
    async def test_nothing_scheduled_400(self):
        from app.api.routes.payments import cancel_scheduled_change

        sub = _fake_sub(scheduled_change=None, cancel_at_next_billing_date=False)

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(return_value=sub)):
            with pytest.raises(HTTPException) as exc:
                await cancel_scheduled_change(current_user=FakeAgencySubscriber())
        assert exc.value.status_code == 400
        assert "No scheduled change found" in str(exc.value.detail)


# ── POST /payments/cancel ──────────────────────────────────────────────────────

class TestCancelSubscription:

    @pytest.mark.asyncio
    async def test_no_subscription_400(self):
        from app.api.routes.payments import cancel_subscription

        with pytest.raises(HTTPException) as exc:
            await cancel_subscription(current_user=FakeUser(), db=MagicMock())
        assert exc.value.status_code == 400
        assert "No active subscription found" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_dodo_update_failure_502(self):
        from app.api.routes.payments import cancel_subscription

        with patch("app.api.routes.payments.dodo.subscriptions.update",
                   new=AsyncMock(side_effect=Exception("dodo down"))):
            with pytest.raises(HTTPException) as exc:
                await cancel_subscription(current_user=FakeAgencySubscriber(), db=MagicMock())
        assert exc.value.status_code == 502
        assert "Failed to cancel subscription with Dodo" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_cancel_with_known_expiry(self):
        from app.api.routes.payments import cancel_subscription

        future = datetime(2026, 7, 18, tzinfo=timezone.utc)
        db = MagicMock()
        db.execute = AsyncMock(return_value=_mock_db_result(_mock_db_row(future)))

        captured = {}

        async def fake_update(**kwargs):
            captured.update(kwargs)

        with patch("app.api.routes.payments.dodo.subscriptions.update",
                   new=AsyncMock(side_effect=fake_update)):
            result = await cancel_subscription(current_user=FakeAgencySubscriber(), db=db)

        assert captured["subscription_id"] == "sub_agency_001"
        assert captured["cancel_at_next_billing_date"] is True
        assert result["success"] is True
        assert result["data"]["cancelled"] is True
        assert result["data"]["access_until"] == "2026-07-18T00:00:00+00:00"
        assert "Agency access continues until July 18, 2026" in result["data"]["message"]

    @pytest.mark.asyncio
    async def test_cancel_without_expiry_uses_now(self):
        from app.api.routes.payments import cancel_subscription

        db = MagicMock()
        db.execute = AsyncMock(return_value=_mock_db_result(_mock_db_row(None)))

        with patch("app.api.routes.payments.dodo.subscriptions.update",
                   new=AsyncMock(return_value=None)):
            result = await cancel_subscription(current_user=FakeProSubscriber(), db=db)

        assert result["success"] is True
        assert result["data"]["cancelled"] is True
        assert "Pro access continues until" in result["data"]["message"]