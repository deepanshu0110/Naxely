import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, patch
from standardwebhooks import Webhook
from starlette.requests import Request


# Valid base64 webhook secret — decodes to b"testwebhookKey123"
TEST_WH_SECRET = "dGVzdHdlYmhvb2tLZXkxMjM="
_wh = Webhook(TEST_WH_SECRET)


def _sign(payload: dict, webhook_id: str = "wh_default", webhook_timestamp: str | None = None) -> str:
    body = json.dumps(payload)
    if webhook_timestamp is None:
        ts = datetime.now(timezone.utc)
    else:
        ts = datetime.fromtimestamp(float(webhook_timestamp), tz=timezone.utc)
    return _wh.sign(msg_id=webhook_id, timestamp=ts, data=body)


def _make_request(payload: dict) -> Request:
    body_bytes = json.dumps(payload).encode()
    wh_id = "wh_default"
    now_ts = datetime.now(timezone.utc)
    wh_ts = str(int(now_ts.timestamp()))
    sig = _wh.sign(msg_id=wh_id, timestamp=now_ts, data=json.dumps(payload))
    headers = [
        (b"webhook-id", wh_id.encode()),
        (b"webhook-timestamp", wh_ts.encode()),
        (b"webhook-signature", sig.encode()),
        (b"content-type", b"application/json"),
    ]

    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/payments/webhook",
        "headers": headers,
        "query_string": b"",
        "client": ("127.0.0.1", 8000),
        "scheme": "http",
        "server": ("test", 80),
        "root_path": "",
    }
    return Request(scope, receive=receive)


class _AsyncDB:
    def __init__(self, results=None):
        self.results = results or []
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


class _NotFound:
    def mappings(self):
        return self
    def first(self):
        return None


class _Found:
    def mappings(self):
        return self
    def first(self):
        return MagicMock()


class _Row:
    def __init__(self, **kw):
        self._kw = kw
    def mappings(self):
        return self
    def first(self):
        return self
    def __getitem__(self, k):
        return self._kw.get(k)


class TestRealHmacSignatureChain:
    @pytest.mark.asyncio
    async def test_real_signed_payload_full_chain(self):
        from app.api.routes.payments import dodo_webhook

        wh_id = "wh_real_chain_001"
        now_ts = datetime.now(timezone.utc)
        wh_ts = str(int(now_ts.timestamp()))
        payload = {
            "type": "subscription.active",
            "customer_id": "user-hmac-test",
            "product_id": "pro_prod_id",
            "subscription_id": "sub_hmac_001",
            "current_period_end": "2026-07-01T00:00:00Z",
        }
        body_str = json.dumps(payload)
        real_sig = _wh.sign(msg_id=wh_id, timestamp=now_ts, data=body_str)

        headers = [
            (b"webhook-id", wh_id.encode()),
            (b"webhook-timestamp", wh_ts.encode()),
            (b"webhook-signature", real_sig.encode()),
            (b"content-type", b"application/json"),
        ]

        async def receive():
            return {"type": "http.request", "body": body_str.encode(), "more_body": False}

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/payments/webhook",
            "headers": headers,
            "query_string": b"",
            "client": ("10.0.0.1", 8000),
            "scheme": "http",
            "server": ("test", 80),
            "root_path": "",
        }
        request = Request(scope, receive=receive)

        db = _AsyncDB([_NotFound(), MagicMock(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "pro_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        tier_queries = [q for q in db.executed_queries if "tier = :tier" in q]
        assert len(tier_queries) > 0
        assert db.committed

    @pytest.mark.asyncio
    async def test_wrong_secret_rejects(self):
        from app.api.routes.payments import dodo_webhook
        from fastapi import HTTPException

        wrong_wh = Webhook(b"wrong_secret")
        wh_id = "wh_bad_sig_001"
        now_ts = datetime.now(timezone.utc)
        wh_ts = str(int(now_ts.timestamp()))
        payload = {
            "type": "subscription.active",
        }
        body_str = json.dumps(payload)
        wrong_sig = wrong_wh.sign(msg_id=wh_id, timestamp=now_ts, data=body_str)

        headers = [
            (b"webhook-id", wh_id.encode()),
            (b"webhook-timestamp", wh_ts.encode()),
            (b"webhook-signature", wrong_sig.encode()),
            (b"content-type", b"application/json"),
        ]

        async def receive():
            return {"type": "http.request", "body": body_str.encode(), "more_body": False}

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/payments/webhook",
            "headers": headers,
            "query_string": b"",
            "client": ("10.0.0.2", 8000),
            "scheme": "http",
            "server": ("test", 80),
            "root_path": "",
        }
        request = Request(scope, receive=receive)

        db = _AsyncDB([])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with pytest.raises(HTTPException) as exc_info:
                await dodo_webhook(request=request, db=db)
            assert exc_info.value.status_code == 400
            assert "signature" in str(exc_info.value.detail).lower()


class TestWebhookEventCoverage:
    @pytest.mark.asyncio
    async def test_cancellation_downgrades_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.cancelled",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        downgrade_queries = [q for q in db.executed_queries if "tier = 'free'" in q]
        assert len(downgrade_queries) > 0
        assert db.committed

    @pytest.mark.asyncio
    async def test_subscription_failed_downgrades_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.failed",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        downgrade_queries = [q for q in db.executed_queries if "tier = 'free'" in q]
        assert len(downgrade_queries) > 0

    @pytest.mark.asyncio
    async def test_subscription_on_hold_downgrades_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.on_hold",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        downgrade_queries = [q for q in db.executed_queries if "tier = 'free'" in q]
        assert len(downgrade_queries) > 0
        # dodo_subscription_id must survive — on_hold is recoverable
        null_sub_queries = [q for q in db.executed_queries if "dodo_subscription_id = NULL" in q]
        assert len(null_sub_queries) == 0
        assert db.committed

    @pytest.mark.asyncio
    async def test_refund_succeeded_downgrades_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "refund.succeeded",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        downgrade_queries = [q for q in db.executed_queries if "tier = 'free'" in q]
        assert len(downgrade_queries) > 0

    @pytest.mark.asyncio
    async def test_dispute_opened_downgrades_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "dispute.opened",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        downgrade_queries = [q for q in db.executed_queries if "tier = 'free'" in q]
        assert len(downgrade_queries) > 0

    @pytest.mark.asyncio
    async def test_subscription_active_updates_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.active",
            "customer_id": "user-123",
            "product_id": "pro_prod_id",
            "subscription_id": "sub_active_001",
            "current_period_end": "2026-07-01T00:00:00Z",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "pro_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        tier_queries = [q for q in db.executed_queries if "tier = :tier" in q]
        assert len(tier_queries) > 0
        assert db.committed

    @pytest.mark.asyncio
    async def test_plan_changed_updates_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.plan_changed",
            "customer_id": "user-123",
            "product_id": "agency_prod_id",
            "subscription_id": "sub_plan_001",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "agency_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        tier_queries = [q for q in db.executed_queries if "tier = :tier" in q]
        assert len(tier_queries) > 0

    @pytest.mark.asyncio
    async def test_already_processed_returns_early(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "payment.succeeded",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_Found()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "already_processed"

        insert_queries = [q for q in db.executed_queries if "INSERT INTO payment_events" in q]
        assert len(insert_queries) == 0

    @pytest.mark.asyncio
    async def test_integrity_error_returns_already_processed(self):
        from app.api.routes.payments import dodo_webhook
        from sqlalchemy.exc import IntegrityError

        payload = {
            "type": "payment.succeeded",
            "customer_id": "user-123",
        }
        request = _make_request(payload)

        db = _AsyncDB([_NotFound(), MagicMock()])

        call_n = [0]
        original_execute = db.execute
        async def raising_on_insert(query, params=None):
            idx = call_n[0]
            call_n[0] += 1
            if "INSERT INTO payment_events" in str(query):
                raise IntegrityError("duplicate key", {}, None)
            return await original_execute(query, params)
        db.execute = raising_on_insert

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "already_processed"
        assert db.rolled_back

    @pytest.mark.asyncio
    async def test_unhandled_event_still_commits(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "payment.processing",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        assert db.committed


class TestEmailFailureIsolation:
    @pytest.mark.asyncio
    async def test_email_failure_does_not_rollback(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "payment.failed",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock(), MagicMock()])

        user_email_row = MagicMock()
        user_email_row.__getitem__.return_value = "user@test.com"
        email_result = MagicMock()
        email_result.mappings.return_value.first.return_value = user_email_row

        original_execute = db.execute
        call_index = [0]
        async def tracking_execute(query, params=None):
            idx = call_index[0]
            call_index[0] += 1
            if idx == 2:
                return email_result
            return await original_execute(query, params)
        db.execute = tracking_execute

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.RESEND_API_KEY", "test_resend_key"):
                with patch("app.api.routes.payments.settings.FROM_EMAIL", "hello@databrief.io"):
                    with patch("resend.Emails.send") as mock_send:
                        mock_send.side_effect = Exception("Resend network error")
                        resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        assert db.committed

    @pytest.mark.asyncio
    async def test_retry_after_email_failure_returns_already_processed(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "payment.failed",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_Found()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "already_processed"

        email_queries = [q for q in db.executed_queries if "SELECT email FROM users" in q]
        assert len(email_queries) == 0

    @pytest.mark.asyncio
    async def test_no_resend_key_skips_email(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "payment.failed",
            "customer_id": "user-123",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock()])

        user_email_row = MagicMock()
        user_email_row.__getitem__.return_value = "user@test.com"
        email_result = MagicMock()
        email_result.mappings.return_value.first.return_value = user_email_row

        original_execute = db.execute
        call_index = [0]
        async def tracking_execute(query, params=None):
            idx = call_index[0]
            call_index[0] += 1
            if idx == 2:
                return email_result
            return await original_execute(query, params)
        db.execute = tracking_execute

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.RESEND_API_KEY", ""):
                with patch("resend.Emails.send") as mock_send:
                    resp = await dodo_webhook(request=request, db=db)

        mock_send.assert_not_called()

        assert resp["data"]["status"] == "processed"
        assert db.committed


class TestWebhookUserResolution:
    @pytest.mark.asyncio
    async def test_metadata_user_id_under_data_resolves(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.created",
            "customer_id": "cus_dodo_unknown",
            "data": {
                "metadata": {"user_id": "user-resolved-from-data"},
                "product_id": "pro_prod_id",
            },
            "subscription_id": "sub_meta_001",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "pro_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        tier_queries = [q for q in db.executed_queries if "WHERE id = :uid" in q and "tier" in q]
        assert len(tier_queries) > 0
        assert db.committed

    @pytest.mark.asyncio
    async def test_metadata_user_id_top_level_resolves(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.created",
            "customer_id": "cus_dodo_unknown",
            "metadata": {"user_id": "user-resolved-top"},
            "data": {"product_id": "pro_prod_id"},
            "subscription_id": "sub_meta_002",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "pro_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        tier_queries = [q for q in db.executed_queries if "WHERE id = :uid" in q and "tier" in q]
        assert len(tier_queries) > 0

    @pytest.mark.asyncio
    async def test_fallback_by_dodo_customer_id(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.created",
            "customer_id": "cus_known_001",
            "data": {"product_id": "pro_prod_id"},
            "subscription_id": "sub_fallback_001",
        }
        request = _make_request(payload)

        existing_result = _NotFound()
        found_by_customer = _Row(id="user-found-by-customer-id")

        db = _AsyncDB([existing_result, MagicMock(), found_by_customer, MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "pro_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        # Should have done a lookup by dodo_customer_id
        customer_lookups = [q for q in db.executed_queries if "dodo_customer_id = :dci" in q]
        assert len(customer_lookups) > 0

    @pytest.mark.asyncio
    async def test_no_user_resolved_graceful(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "subscription.created",
            "customer_id": "cus_completely_unknown",
            "data": {"product_id": "pro_prod_id"},
            "subscription_id": "sub_nouser_001",
        }
        request = _make_request(payload)

        existing_result = _NotFound()
        customer_lookup_result = _NotFound()

        db = _AsyncDB([existing_result, MagicMock(), customer_lookup_result])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "pro_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        assert db.committed

    @pytest.mark.asyncio
    async def test_dodo_customer_id_captured_on_subscription_created(self):
        from app.api.routes.payments import dodo_webhook

        class CustomerCaptureDB:
            def __init__(self):
                self.call_count = 0
                self.executed_queries = []
                self.committed = False

            async def execute(self, query, params=None):
                self.executed_queries.append(str(query))
                self.call_count += 1
                if self.call_count == 1:
                    return _NotFound()
                if self.call_count == 2:
                    return MagicMock()
                return MagicMock()

            async def commit(self):
                self.committed = True

        payload = {
            "type": "subscription.created",
            "customer_id": "cus_to_capture",
            "metadata": {"user_id": "user-capture-test"},
            "data": {"product_id": "pro_prod_id"},
            "subscription_id": "sub_capture_001",
        }
        request = _make_request(payload)
        db = CustomerCaptureDB()

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_PRO_PRODUCT_ID", "pro_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        # Should have captured dodo_customer_id
        capture_queries = [q for q in db.executed_queries if "dodo_customer_id = :dci" in q]
        assert len(capture_queries) > 0

    @pytest.mark.asyncio
    async def test_dunning_recovered_restores_tier(self):
        from app.api.routes.payments import dodo_webhook

        payload = {
            "type": "dunning.recovered",
            "metadata": {"user_id": "user-dunning-recovered"},
            "data": {"product_id": "agency_prod_id"},
            "subscription_id": "sub_dunning_001",
        }
        request = _make_request(payload)
        db = _AsyncDB([_NotFound(), MagicMock(), MagicMock()])

        with patch("app.api.routes.payments.settings.DODO_WEBHOOK_SECRET", TEST_WH_SECRET):
            with patch("app.api.routes.payments.settings.DODO_AGENCY_PRODUCT_ID", "agency_prod_id"):
                resp = await dodo_webhook(request=request, db=db)

        assert resp["data"]["status"] == "processed"
        tier_queries = [q for q in db.executed_queries if "tier = :tier" in q]
        assert len(tier_queries) > 0
        assert db.committed
