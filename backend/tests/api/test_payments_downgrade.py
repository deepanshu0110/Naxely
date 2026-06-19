import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from starlette.requests import Request as StarletteRequest


_req_counter = 0


def _make_request() -> StarletteRequest:
    global _req_counter
    _req_counter += 1
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/payments/downgrade",
        "headers": [(b"authorization", b"Bearer test")],
        "query_string": b"",
        "client": (f"127.0.0.{_req_counter}", 8000),
        "scheme": "http",
        "server": ("test", 80),
        "root_path": "",
    }
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    return StarletteRequest(scope, receive=receive)


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


class FakeSubscription:
    scheduled_change = None
    cancel_at_next_billing_date = False
    next_billing_date = None


class TestDowngradeFree:
    @pytest.mark.asyncio
    async def test_free_user_rejected(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="free")

        with patch("app.api.routes.payments.get_current_user", return_value=FakeUser()):
            with pytest.raises(Exception) as exc_info:
                await downgrade_subscription(
                    request=_make_request(), body=body,
                    current_user=FakeUser(),
                    db=MagicMock(),
                )

        assert "No active subscription found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_pro_user_downgrade_to_free(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="free")
        future = datetime(2026, 7, 18, tzinfo=timezone.utc)

        captured_kwargs = {}

        async def fake_update(**kwargs):
            captured_kwargs.update(kwargs)

        db = MagicMock()
        db.execute = AsyncMock(return_value=_mock_db_result(_mock_db_row(future)))

        fake_sub = FakeSubscription()

        with patch("app.api.routes.payments.dodo.subscriptions.update",
                   new=AsyncMock(side_effect=fake_update)):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=fake_sub)):
                result = await downgrade_subscription(
                    request=_make_request(), body=body,
                    current_user=FakeAgencySubscriber(),
                    db=db,
                )

        assert captured_kwargs["subscription_id"] == "sub_agency_001"
        assert captured_kwargs["cancel_at_next_billing_date"] is True
        assert result["success"] is True
        assert result["data"]["planned_tier"] == "free"
        assert "Free plan" in result["data"]["message"]

    @pytest.mark.asyncio
    async def test_agency_user_downgrade_to_free(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="free")
        future = datetime(2026, 7, 18, tzinfo=timezone.utc)

        captured_kwargs = {}

        async def fake_update(**kwargs):
            captured_kwargs.update(kwargs)

        db = MagicMock()
        db.execute = AsyncMock(return_value=_mock_db_result(_mock_db_row(future)))

        fake_sub = FakeSubscription()

        with patch("app.api.routes.payments.dodo.subscriptions.update",
                   new=AsyncMock(side_effect=fake_update)):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=fake_sub)):
                result = await downgrade_subscription(
                    request=_make_request(), body=body,
                    current_user=FakeAgencySubscriber(),
                    db=db,
                )

        assert captured_kwargs["subscription_id"] == "sub_agency_001"
        assert captured_kwargs["cancel_at_next_billing_date"] is True
        assert result["data"]["planned_tier"] == "free"
        assert "Free plan" in result["data"]["message"]


class TestDowngradeAgencyToPro:
    @pytest.mark.asyncio
    async def test_pro_user_rejected(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="pro")
        fake_sub = FakeSubscription()

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=fake_sub)):
                with pytest.raises(Exception) as exc_info:
                    await downgrade_subscription(
                        request=_make_request(), body=body,
                        current_user=FakeProSubscriber(),
                        db=MagicMock(),
                    )

        assert "not subscribed to the Agency plan" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_free_user_rejected(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="pro")

        with pytest.raises(Exception) as exc_info:
            await downgrade_subscription(
                request=_make_request(), body=body,
                current_user=FakeUser(),
                db=MagicMock(),
            )

        assert "No active subscription found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_agency_to_pro_schedules_at_next_billing(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="pro")
        future = datetime(2026, 7, 18, tzinfo=timezone.utc)

        captured_kwargs = {}

        async def fake_change_plan(**kwargs):
            captured_kwargs.update(kwargs)

        fake_sub = MagicMock()
        fake_sub.next_billing_date = future
        fake_sub.scheduled_change = None
        fake_sub.cancel_at_next_billing_date = False

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.change_plan",
                       new=AsyncMock(side_effect=fake_change_plan)):
                with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                           new=AsyncMock(return_value=fake_sub)):
                    result = await downgrade_subscription(
                        request=_make_request(), body=body,
                        current_user=FakeAgencySubscriber(),
                        db=MagicMock(),
                    )

        assert captured_kwargs["subscription_id"] == "sub_agency_001"
        assert captured_kwargs["product_id"] == "prod_pro"
        assert captured_kwargs["quantity"] == 1
        assert captured_kwargs["proration_billing_mode"] == "full_immediately"
        assert captured_kwargs["effective_at"] == "next_billing_date"
        assert result["success"] is True
        assert result["data"]["planned_tier"] == "pro"
        assert "Pro" in result["data"]["message"]


class TestDowngradeErrors:
    @pytest.mark.asyncio
    async def test_no_subscription_rejected(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="free")

        with pytest.raises(Exception) as exc_info:
            await downgrade_subscription(
                request=_make_request(), body=body,
                current_user=FakeUser(),
                db=MagicMock(),
            )

        assert "No active subscription found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_downgrade_api_error(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="pro")
        fake_sub = FakeSubscription()

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=fake_sub)):
                with patch("app.api.routes.payments.dodo.subscriptions.change_plan",
                           new=AsyncMock(side_effect=Exception("API error"))):
                    with pytest.raises(Exception) as exc_info:
                        await downgrade_subscription(
                            request=_make_request(), body=body,
                            current_user=FakeAgencySubscriber(),
                            db=MagicMock(),
                        )

        assert "Failed to schedule downgrade" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_downgrade_free_api_error(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="free")
        fake_sub = FakeSubscription()

        with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                   new=AsyncMock(return_value=fake_sub)):
            with patch("app.api.routes.payments.dodo.subscriptions.update",
                       new=AsyncMock(side_effect=Exception("API error"))):
                with pytest.raises(Exception) as exc_info:
                    await downgrade_subscription(
                        request=_make_request(), body=body,
                        current_user=FakeAgencySubscriber(),
                        db=MagicMock(),
                    )

        assert "Failed to schedule downgrade" in str(exc_info.value)


class TestPreCheck:
    @pytest.mark.asyncio
    async def test_rejects_existing_scheduled_change(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="pro")
        fake_change = MagicMock()
        fake_change.effective_at = datetime(2026, 7, 18, tzinfo=timezone.utc)
        fake_sub = MagicMock()
        fake_sub.scheduled_change = fake_change
        fake_sub.cancel_at_next_billing_date = False

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=fake_sub)):
                with pytest.raises(Exception) as exc_info:
                    await downgrade_subscription(
                        request=_make_request(), body=body,
                        current_user=FakeAgencySubscriber(),
                        db=MagicMock(),
                    )

        assert "PENDING_SCHEDULED_CHANGE" in str(exc_info.value)
        assert "already have a pending plan change" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rejects_existing_cancellation(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest

        body = DowngradeRequest(plan="pro")
        fake_sub = MagicMock()
        fake_sub.scheduled_change = None
        fake_sub.cancel_at_next_billing_date = True

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=fake_sub)):
                with pytest.raises(Exception) as exc_info:
                    await downgrade_subscription(
                        request=_make_request(), body=body,
                        current_user=FakeAgencySubscriber(),
                        db=MagicMock(),
                    )

        assert "PENDING_CANCELLATION" in str(exc_info.value)
        assert "already scheduled for cancellation" in str(exc_info.value)


class TestDodoErrorSurfacing:
    @pytest.mark.asyncio
    async def test_dodo_409_returns_real_message(self):
        from app.api.routes.payments import downgrade_subscription, DowngradeRequest
        from dodopayments import ConflictError

        body = DowngradeRequest(plan="pro")
        fake_sub = FakeSubscription()

        conflict = ConflictError(
            message="Conflict Error",
            response=MagicMock(status_code=409),
            body={"code": "SCHEDULED_PLAN_CHANGE_EXISTS", "message": "A scheduled plan change already exists."},
        )

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.subscriptions.retrieve",
                       new=AsyncMock(return_value=fake_sub)):
                with patch("app.api.routes.payments.dodo.subscriptions.change_plan",
                           new=AsyncMock(side_effect=conflict)):
                    with pytest.raises(Exception) as exc_info:
                        await downgrade_subscription(
                            request=_make_request(), body=body,
                            current_user=FakeAgencySubscriber(),
                            db=MagicMock(),
                        )

        error_str = str(exc_info.value)
        assert "SCHEDULED_PLAN_CHANGE_EXISTS" in error_str
        assert "A scheduled plan change already exists" in error_str
