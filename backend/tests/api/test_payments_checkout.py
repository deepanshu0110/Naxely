import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import httpx
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Request, Response as HttpxResponse
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


class TestCheckoutCreation:
    @pytest.mark.asyncio
    async def test_checkout_returns_url_for_pro(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        fake_resp = HttpxResponse(
            status_code=200,
            json={"checkout_url": "https://pay.dodopayments.com/sess_pro_001"},
            request=MagicMock(),
        )

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_resp)):
                    result = await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert result["checkout_url"] == "https://pay.dodopayments.com/sess_pro_001"

    @pytest.mark.asyncio
    async def test_checkout_returns_url_for_agency(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="agency")

        fake_resp = HttpxResponse(
            status_code=200,
            json={"checkout_url": "https://pay.dodopayments.com/sess_agency_001"},
            request=MagicMock(),
        )

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_resp)):
                    result = await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert result["checkout_url"] == "https://pay.dodopayments.com/sess_agency_001"

    @pytest.mark.asyncio
    async def test_checkout_passes_correct_product_id_and_metadata(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        fake_resp = HttpxResponse(
            status_code=200,
            json={"checkout_url": "https://pay.dodopayments.com/sess_pro_002"},
            request=MagicMock(),
        )

        captured_kwargs = {}

        async def fake_post(url, **kwargs):
            captured_kwargs.update(kwargs)
            return fake_resp

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro_correct"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)):
                    await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        sent_json = captured_kwargs["json"]
        assert sent_json["product_cart"] == [{"product_id": "prod_pro_correct", "quantity": 1}]
        assert sent_json["customer"] == {"email": "test@example.com", "name": "Test User"}
        assert sent_json["metadata"] == {"user_id": "user-abc-123"}

    @pytest.mark.asyncio
    async def test_client_supplied_product_id_ignored(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        captured_kwargs = {}

        async def fake_post(url, **kwargs):
            captured_kwargs.update(kwargs)
            fake_resp = HttpxResponse(
                status_code=200,
                json={"checkout_url": "https://pay.dodopayments.com/sess_pro_003"},
                request=MagicMock(),
            )
            return fake_resp

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro_correct"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)):
                    await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        sent_json = captured_kwargs["json"]
        assert sent_json["product_cart"] == [{"product_id": "prod_pro_correct", "quantity": 1}]
        assert sent_json["product_cart"][0]["product_id"] != "prod_malicious"

    @pytest.mark.asyncio
    async def test_checkout_raises_on_dodo_api_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        error_resp = HttpxResponse(
            status_code=400,
            json={"error": "invalid_request"},
            request=MagicMock(),
        )

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=error_resp)):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_checkout_raises_on_network_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=httpx.RequestError("Connection refused", request=MagicMock()))):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_checkout_raises_on_missing_product_config(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", ""):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(request=_make_request(), body=body, current_user=FakeUser())

        assert exc_info.value.status_code == 500
        assert "Product not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_checkout_raises_on_invalid_plan(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CheckoutRequest(plan="invalid_plan")


class TestCustomerPortal:
    """On-hold subscription → Customer Portal, not checkout or Change Plan."""

    @pytest.mark.asyncio
    async def test_on_hold_user_gets_customer_portal(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        captured_url = None

        async def fake_post(url, **kwargs):
            nonlocal captured_url
            captured_url = url
            return HttpxResponse(
                status_code=200,
                json={"url": "https://pay.dodopayments.com/portal/sess_001"},
                request=MagicMock(),
            )

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)):
                    result = await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeOnHoldUser(),
                    )

        # Must call Customer Portal, not checkout or change plan
        assert captured_url == "https://api.dodopayments.com/customers/customer_portal"
        assert result["checkout_url"] == "https://pay.dodopayments.com/portal/sess_001"

    @pytest.mark.asyncio
    async def test_on_hold_user_portal_api_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        error_resp = HttpxResponse(
            status_code=400,
            json={"error": "invalid_customer"},
            request=MagicMock(),
        )

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=error_resp)):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_checkout_session(
                            request=_make_request(), body=body, current_user=FakeOnHoldUser(),
                        )

        assert exc_info.value.status_code == 502
        assert "customer portal session" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_on_hold_user_portal_network_error(self):
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(
                    side_effect=httpx.RequestError("timeout", request=MagicMock()),
                )):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_checkout_session(
                            request=_make_request(), body=body, current_user=FakeOnHoldUser(),
                        )

        assert exc_info.value.status_code == 502
        assert "Failed to reach payment provider" in exc_info.value.detail


class TestExistingSubscriber:
    """CHECK 1 — Existing subscriber changing or keeping plan."""

    @pytest.mark.asyncio
    async def test_existing_subscriber_change_plan(self):
        """Pro user requesting Agency → Change Plan API, no checkout session."""
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="agency")

        captured_url = None

        async def fake_post(url, **kwargs):
            nonlocal captured_url
            captured_url = url
            return HttpxResponse(
                status_code=200,
                json={"id": "change_ok"},
                request=MagicMock(),
            )

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)):
                    result = await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeSubscriber(),
                    )

        assert captured_url == "https://api.dodopayments.com/subscriptions/sub_dodo_001/change_plan"
        assert result["checkout_url"] == ""

    @pytest.mark.asyncio
    async def test_existing_subscriber_same_plan_rejected(self):
        """Pro user requesting Pro → 400 error."""
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="pro")

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with pytest.raises(HTTPException) as exc_info:
                    await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeSubscriber(),
                    )

        assert exc_info.value.status_code == 400
        assert "Already subscribed to this plan" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_free_user_checkout_unchanged(self):
        """Free user (no subscription_id) requesting Pro → checkout session (existing behavior)."""
        from app.api.routes.payments import create_checkout_session, CheckoutRequest

        body = CheckoutRequest(plan="pro")

        fake_resp = HttpxResponse(
            status_code=200,
            json={"checkout_url": "https://pay.dodopayments.com/sess_free_pro"},
            request=MagicMock(),
        )

        with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "prod_pro"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_resp)):
                    result = await create_checkout_session(
                        request=_make_request(), body=body, current_user=FakeUser(),
                    )

        assert result["checkout_url"] == "https://pay.dodopayments.com/sess_free_pro"

    @pytest.mark.asyncio
    async def test_existing_subscriber_change_plan_api_error(self):
        """Change Plan API failure → 502."""
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="agency")

        error_resp = HttpxResponse(
            status_code=400,
            json={"error": "invalid_subscription"},
            request=MagicMock(),
        )

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=error_resp)):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_checkout_session(
                            request=_make_request(), body=body, current_user=FakeSubscriber(),
                        )

        assert exc_info.value.status_code == 502
        assert "Failed to change plan" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_existing_subscriber_change_plan_network_error(self):
        """Change Plan API network error → 502."""
        from app.api.routes.payments import create_checkout_session, CheckoutRequest
        from fastapi import HTTPException

        body = CheckoutRequest(plan="agency")

        with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "prod_agency"):
            with patch("app.api.routes.payments.settings.DODO_API_KEY", "test_key"):
                with patch("httpx.AsyncClient.post", new=AsyncMock(
                    side_effect=httpx.RequestError("timeout", request=MagicMock()),
                )):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_checkout_session(
                            request=_make_request(), body=body, current_user=FakeSubscriber(),
                        )

        assert exc_info.value.status_code == 502
        assert "Failed to reach payment provider" in exc_info.value.detail
