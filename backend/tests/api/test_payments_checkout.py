import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.requests import Request as StarletteRequest


_req_counter = 0


def _make_request() -> StarletteRequest:
    global _req_counter
    _req_counter += 1
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/payments/checkout",
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


class FakeSubscriber:
    id = "user-sub-456"
    email = "subscriber@example.com"
    full_name = "Sub User"
    tier = "pro"
    dodo_subscription_id = "sub_dodo_001"
    dodo_customer_id = "cust_dodo_001"


class FakeOnHoldUser:
    id = "user-onhold-789"
    email = "onhold@example.com"
    full_name = "On Hold User"
    tier = "free"
    dodo_subscription_id = "sub_onhold_001"
    dodo_customer_id = "cust_onhold_001"


def _mock_session(checkout_url: str = "https://pay.dodopayments.com/sess_001"):
    m = MagicMock()
    m.checkout_url = checkout_url
    return m


def _mock_portal(link: str = "https://pay.dodopayments.com/portal/sess_001"):
    m = MagicMock()
    m.link = link
    return m


class TestCheckoutCreation:
    @pytest.mark.asyncio
    async def test_checkout_returns_url_for_pro(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.checkout_sessions.create",
                       new=AsyncMock(return_value=_mock_session("https://pay.dodopayments.com/sess_pro_001"))):
                result = await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert result["checkout_url"] == "https://pay.dodopayments.com/sess_pro_001"

    @pytest.mark.asyncio
    async def test_checkout_returns_url_for_agency(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="agency")

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.dodo.checkout_sessions.create",
                       new=AsyncMock(return_value=_mock_session("https://pay.dodopayments.com/sess_agency_001"))):
                result = await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert result["checkout_url"] == "https://pay.dodopayments.com/sess_agency_001"

    @pytest.mark.asyncio
    async def test_checkout_passes_correct_product_id_and_metadata(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        captured_kwargs = {}

        async def fake_create(**kwargs):
            captured_kwargs.update(kwargs)
            return _mock_session("https://pay.dodopayments.com/sess_pro_002")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro_correct"):
            with patch("app.api.routes.payments.dodo.checkout_sessions.create",
                       new=AsyncMock(side_effect=fake_create)):
                await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert captured_kwargs["product_cart"] == [{"product_id": "prod_pro_correct", "quantity": 1}]
        assert captured_kwargs["customer"] == {"email": "test@example.com", "name": "Test User"}
        assert captured_kwargs["metadata"] == {"user_id": "user-abc-123"}

    @pytest.mark.asyncio
    async def test_client_supplied_product_id_ignored(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        captured_kwargs = {}

        async def fake_create(**kwargs):
            captured_kwargs.update(kwargs)
            return _mock_session("https://pay.dodopayments.com/sess_pro_003")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro_correct"):
            with patch("app.api.routes.payments.dodo.checkout_sessions.create",
                       new=AsyncMock(side_effect=fake_create)):
                await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        sent_cart = captured_kwargs["product_cart"]
        assert sent_cart == [{"product_id": "prod_pro_correct", "quantity": 1}]
        assert sent_cart[0]["product_id"] != "prod_malicious"

    @pytest.mark.asyncio
    async def test_checkout_raises_on_dodo_api_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.checkout_sessions.create",
                       new=AsyncMock(side_effect=Exception("API error"))):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_checkout_raises_on_network_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.checkout_sessions.create",
                       new=AsyncMock(side_effect=Exception("Connection timeout"))):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_checkout_raises_on_missing_product_config(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", ""):
            with pytest.raises(HTTPException) as exc_info:
                await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert exc_info.value.status_code == 500
        assert "Product not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_checkout_raises_on_invalid_plan(self):
        from app.api.routes.payments import CheckoutRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CheckoutRequest(plan="invalid_plan")


class TestCustomerPortal:
    @pytest.mark.asyncio
    async def test_on_hold_user_gets_customer_portal(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        captured_kwargs = {}

        async def fake_portal(**kwargs):
            captured_kwargs.update(kwargs)
            return _mock_portal("https://pay.dodopayments.com/portal/sess_001")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.FRONTEND_BASE_URL", "http://localhost:5173"):
                with patch("app.api.routes.payments.dodo.customers.customer_portal.create",
                           new=AsyncMock(side_effect=fake_portal)):
                    result = await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeOnHoldUser(),
                    )

        assert captured_kwargs["customer_id"] == "cust_onhold_001"
        assert captured_kwargs["return_url"] == "http://localhost:5173/settings?tab=billing"
        assert result["checkout_url"] == "https://pay.dodopayments.com/portal/sess_001"

    @pytest.mark.asyncio
    async def test_on_hold_user_portal_api_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.customers.customer_portal.create",
                       new=AsyncMock(side_effect=Exception("API error"))):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeOnHoldUser(),
                    )

        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_on_hold_user_portal_network_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.customers.customer_portal.create",
                       new=AsyncMock(side_effect=Exception("Connection timeout"))):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeOnHoldUser(),
                    )

        assert exc_info.value.status_code == 502


class TestExistingSubscriber:
    @pytest.mark.asyncio
    async def test_existing_subscriber_change_plan(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="agency")

        captured_kwargs = {}

        async def fake_change_plan(**kwargs):
            captured_kwargs.update(kwargs)

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.dodo.subscriptions.change_plan",
                       new=AsyncMock(side_effect=fake_change_plan)):
                result = await create_checkout_session(
                    request=_make_request(), body=body, current_user=FakeSubscriber(),
                )

        assert captured_kwargs["subscription_id"] == "sub_dodo_001"
        assert captured_kwargs["product_id"] == "prod_agency"
        assert result["checkout_url"] == ""

    @pytest.mark.asyncio
    async def test_existing_subscriber_same_plan_rejected(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with pytest.raises(HTTPException) as exc_info:
                await create_checkout_session(
                    request=_make_request(), body=body, current_user=FakeSubscriber(),
                )

        assert exc_info.value.status_code == 400
        assert "Already subscribed to this plan" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_free_user_checkout_unchanged(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.dodo.checkout_sessions.create",
                       new=AsyncMock(return_value=_mock_session("https://pay.dodopayments.com/sess_free_pro"))):
                result = await create_checkout_session(
                    request=_make_request(), body=body, current_user=FakeUser(),
                )

        assert result["checkout_url"] == "https://pay.dodopayments.com/sess_free_pro"

    @pytest.mark.asyncio
    async def test_existing_subscriber_change_plan_api_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="agency")

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.dodo.subscriptions.change_plan",
                       new=AsyncMock(side_effect=Exception("API error"))):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeSubscriber(),
                    )

        assert exc_info.value.status_code == 502
        assert "Failed to change plan" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_existing_subscriber_change_plan_network_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="agency")

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.dodo.subscriptions.change_plan",
                       new=AsyncMock(side_effect=Exception("Connection timeout"))):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeSubscriber(),
                    )

        assert exc_info.value.status_code == 502
        assert "Failed to change plan" in exc_info.value.detail
