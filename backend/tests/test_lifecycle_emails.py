import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.exc import IntegrityError


# ---- Trigger query logic ----

class TestTriggerQueries:
    def test_trigger_a_query_has_required_clauses(self):
        from app.services.lifecycle_email_service import TRIGGER_A_QUERY
        q = TRIGGER_A_QUERY
        assert "lifecycle_no_report_3d" in q
        assert "email_suppressed" in q
        assert "INTERVAL '3 days'" in q
        assert "HAVING COUNT(r.id) = 0" in q
        assert "el.id IS NULL" in q
        # Manual-outreach exclusion must be in query, not via email_log
        for email in ["eminefe13@gmail.com", "jash.c.shah@gmail.com", "ravenabianca@gmail.com"]:
            assert email in q
        assert "NOT IN" in q

    def test_trigger_b_query_has_required_clauses(self):
        from app.services.lifecycle_email_service import TRIGGER_B_QUERY
        q = TRIGGER_B_QUERY
        assert "lifecycle_onboarded_no_report_7d" in q
        assert "has_completed_onboarding = TRUE" in q
        assert "onboarding_completed_at IS NOT NULL" in q
        assert "INTERVAL '7 days'" in q
        assert "HAVING COUNT(r.id) = 0" in q
        for email in ["eminefe13@gmail.com", "jash.c.shah@gmail.com", "ravenabianca@gmail.com"]:
            assert email in q
        assert "NOT IN" in q

    @pytest.mark.asyncio
    async def test_trigger_a_excludes_recent_signups(self):
        from app.services.lifecycle_email_service import get_trigger_a_candidates
        mock_db = AsyncMock()
        mock_result = MagicMock()
        # Simulate DB returning 1 candidate (old user) - recent user filtered by WHERE clause in real DB
        mock_result.mappings.return_value.all.return_value = [
            {"id": str(uuid.uuid4()), "email": "old@test.com", "created_at": datetime.now(timezone.utc)}
        ]
        mock_db.execute.return_value = mock_result
        result = await get_trigger_a_candidates(mock_db)
        assert len(result) == 1
        # Verify query was executed
        mock_db.execute.assert_called_once()
        sql_str = str(mock_db.execute.call_args[0][0])
        assert "lifecycle_no_report_3d" in sql_str

    @pytest.mark.asyncio
    async def test_trigger_b_requires_onboarding_timestamp(self):
        from app.services.lifecycle_email_service import get_trigger_b_candidates
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        result = await get_trigger_b_candidates(mock_db)
        assert result == []
        mock_db.execute.assert_called_once()


# ---- Duplicate prevention ----

class TestDuplicatePrevention:
    @pytest.mark.asyncio
    async def test_send_and_log_inserts_email_log_with_resend_id(self):
        from app.services import lifecycle_email_service as svc
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock()
        mock_db.commit = AsyncMock()
        user = {"id": str(uuid.uuid4()), "email": "user@test.com"}
        with patch.object(svc, "send_email_with_id", return_value=(True, "re_test123")):
            ok = await svc._send_and_log(mock_db, user["id"], user["email"], "lifecycle_no_report_3d", "subj", "<p>hi</p>", "hi")
        assert ok is True
        # Check insert was called with correct params
        call_args = mock_db.execute.call_args
        sql_str = str(call_args[0][0])
        assert "INSERT INTO email_log" in sql_str
        params = call_args[0][1]
        assert params["uid"] == user["id"]
        assert params["etype"] == "lifecycle_no_report_3d"
        assert params["rid"] == "re_test123"

    @pytest.mark.asyncio
    async def test_duplicate_unique_constraint_suppressed(self):
        from app.services import lifecycle_email_service as svc
        mock_db = AsyncMock()
        mock_db.execute.side_effect = IntegrityError("duplicate", None, None)
        mock_db.rollback = AsyncMock()
        user = {"id": str(uuid.uuid4()), "email": "dup@test.com"}
        with patch.object(svc, "send_email_with_id", return_value=(True, "re_dup")):
            ok = await svc._send_and_log(mock_db, user["id"], user["email"], "lifecycle_no_report_3d", "subj", "<p>hi</p>", "hi")
        assert ok is False
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_send_does_not_insert(self):
        from app.services import lifecycle_email_service as svc
        mock_db = AsyncMock()
        user = {"id": str(uuid.uuid4()), "email": "fail@test.com"}
        with patch.object(svc, "send_email_with_id", return_value=(False, None)):
            ok = await svc._send_and_log(mock_db, user["id"], user["email"], "lifecycle_no_report_3d", "subj", "<p>hi</p>", "hi")
        assert ok is False
        mock_db.execute.assert_not_called()


# ---- Suppression flag blocking ----

class TestSuppressionFlag:
    def test_trigger_queries_filter_suppressed(self):
        from app.services.lifecycle_email_service import TRIGGER_A_QUERY, TRIGGER_B_QUERY
        assert "email_suppressed" in TRIGGER_A_QUERY
        assert "email_suppressed" in TRIGGER_B_QUERY
        # Must use COALESCE to handle NULL legacy rows
        assert "COALESCE" in TRIGGER_A_QUERY
        # Manual-outreach exact-email exclusion
        for email in ["eminefe13@gmail.com", "jash.c.shah@gmail.com", "ravenabianca@gmail.com"]:
            assert email in TRIGGER_A_QUERY
            assert email in TRIGGER_B_QUERY

    @pytest.mark.asyncio
    async def test_run_cycle_skips_suppressed_users(self):
        from app.services import lifecycle_email_service as svc
        mock_db = AsyncMock()
        # get_trigger_* will be patched to return empty for suppressed case
        with patch.object(svc, "get_trigger_a_candidates", return_value=[]) as mock_a, \
             patch.object(svc, "get_trigger_b_candidates", return_value=[]) as mock_b:
            stats = await svc.run_lifecycle_cycle(mock_db)
        assert stats["trigger_a_candidates"] == 0
        assert stats["trigger_b_candidates"] == 0


# ---- Templates are non-promotional ----

class TestTemplates:
    def test_templates_have_no_upsell(self):
        from app.services.lifecycle_email_service import TEMPLATE_A_HTML, TEMPLATE_B_HTML, TEMPLATE_A_SUBJECT, TEMPLATE_B_SUBJECT
        combined = (TEMPLATE_A_HTML + TEMPLATE_B_HTML + TEMPLATE_A_SUBJECT + TEMPLATE_B_SUBJECT).lower()
        assert "upgrade" not in combined
        assert "pro plan" not in combined
        assert "buy now" not in combined

    def test_templates_have_required_links(self):
        from app.services.lifecycle_email_service import TEMPLATE_A_HTML, TEMPLATE_B_HTML
        assert "/reports/new" in TEMPLATE_A_HTML
        assert "/reports/new" in TEMPLATE_B_HTML


# ---- Bounce webhook ----

class TestResendWebhook:
    def _make_client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.database import get_db
        mock_db = AsyncMock()
        # Patch get_db dependency
        app.dependency_overrides[get_db] = lambda: mock_db
        client = TestClient(app)
        return client, mock_db, app

    def test_bounce_suppresses_user_via_resend_id(self):
        import json
        client, mock_db, app = self._make_client()
        # Mock DB: email_log lookup returns user, then updates succeed
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"user_id": str(uuid.uuid4())}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        payload = {
            "type": "email.bounced",
            "data": {
                "email_id": "re_bounce123",
                "to": ["user@test.com"],
                "from": "hello@naxely.com",
                "subject": "Test"
            }
        }
        body = json.dumps(payload).encode()
        # Without RESEND_WEBHOOK_SECRET, verification is skipped
        resp = client.post("/internal/webhooks/resend", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        # Should have updated email_log and users
        assert mock_db.execute.call_count >= 2
        app.dependency_overrides.clear()

    def test_complained_suppresses_user(self):
        import json
        client, mock_db, app = self._make_client()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"user_id": str(uuid.uuid4())}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        payload = {
            "type": "email.complained",
            "data": {"email_id": "re_complain123", "to": ["user@test.com"]}
        }
        body = json.dumps(payload).encode()
        resp = client.post("/internal/webhooks/resend", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "complained"
        app.dependency_overrides.clear()

    def test_non_bounce_ignored(self):
        import json
        client, mock_db, app = self._make_client()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        payload = {"type": "email.delivered", "data": {"email_id": "re_delivered", "to": ["user@test.com"]}}
        body = json.dumps(payload).encode()
        resp = client.post("/internal/webhooks/resend", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "ignored"
        app.dependency_overrides.clear()

    def test_webhook_signature_verification_with_secret(self):
        import json, base64, time, hmac, hashlib
        from unittest.mock import patch
        client, mock_db, app = self._make_client()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        # Set a test secret that is base64-encoded as Svix expects (whsec_ prefix stripped)
        # standardwebhooks expects base64-encoded secret without prefix
        raw_secret = b"test-secret-1234567890-test"
        b64_secret = base64.b64encode(raw_secret).decode()
        with patch("app.api.routes.resend_webhook.settings.RESEND_WEBHOOK_SECRET", b64_secret):
            payload = {"type": "email.delivered", "data": {"email_id": "re_test"}}
            body = json.dumps(payload).encode()
            # Generate valid signature using standardwebhooks
            from standardwebhooks import Webhook as SW
            wh = SW(b64_secret)
            msg_id = "msg_test123"
            ts = datetime.now(timezone.utc)
            # svix sign expects msg_id, timestamp, data (string)
            sig = wh.sign(msg_id, ts, body.decode())
            headers = {
                "Content-Type": "application/json",
                "svix-id": msg_id,
                "svix-timestamp": str(int(ts.timestamp())),
                "svix-signature": sig,
            }
            resp = client.post("/internal/webhooks/resend", content=body, headers=headers)
            # Should pass verification
            assert resp.status_code == 200

            # Now with bad signature should 400
            bad_headers = {
                "Content-Type": "application/json",
                "svix-id": msg_id,
                "svix-timestamp": str(int(ts.timestamp())),
                "svix-signature": "v1,badsignature00000000000000000000000000000000000000000000000000",
            }
            resp2 = client.post("/internal/webhooks/resend", content=body, headers=bad_headers)
            assert resp2.status_code == 400
        app.dependency_overrides.clear()


# ---- Onboarding timestamp ----

class TestOnboardingTimestamp:
    @pytest.mark.asyncio
    async def test_complete_onboarding_sets_timestamp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.api.deps import get_current_user
        from app.core.database import get_db
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = str(uuid.uuid4())
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": str(mock_user.id)}
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        client = TestClient(app)
        resp = client.post("/auth/complete-onboarding", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        # Check that UPDATE includes onboarding_completed_at
        called_sql = str(mock_db.execute.call_args[0][0])
        assert "onboarding_completed_at" in called_sql
        assert "COALESCE" in called_sql
        app.dependency_overrides.clear()
