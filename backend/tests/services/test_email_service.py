import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import base64
from unittest.mock import patch, ANY

import pytest


class TestSendEmail:
    def test_sends_basic_html_email(self):
        from app.services.email_service import send_email

        with patch("app.services.email_service.settings.RESEND_API_KEY", "test_key"):
            with patch("app.services.email_service.settings.FROM_EMAIL", "hello@naxely.com"):
                with patch("resend.Emails.send") as mock_send:
                    result = send_email(
                        to="user@test.com",
                        subject="Test subject",
                        html="<p>Hello</p>",
                    )

        assert result is True
        mock_send.assert_called_once_with({
            "from": "hello@naxely.com",
            "to": "user@test.com",
            "subject": "Test subject",
            "html": "<p>Hello</p>",
        })

    def test_sends_email_with_pdf_attachment(self):
        from app.services.email_service import send_email

        pdf_content = b"%PDF-1.4 test pdf content"
        pdf_b64 = base64.b64encode(pdf_content).decode()

        with patch("app.services.email_service.settings.RESEND_API_KEY", "test_key"):
            with patch("app.services.email_service.settings.FROM_EMAIL", "hello@naxely.com"):
                with patch("resend.Emails.send") as mock_send:
                    result = send_email(
                        to="user@test.com",
                        subject="Your scheduled report",
                        html="<p>Report attached.</p>",
                        attachments=[{
                            "filename": "report.pdf",
                            "content": pdf_b64,
                        }],
                    )

        assert result is True
        mock_send.assert_called_once_with({
            "from": "hello@naxely.com",
            "to": "user@test.com",
            "subject": "Your scheduled report",
            "html": "<p>Report attached.</p>",
            "attachments": [{"filename": "report.pdf", "content": pdf_b64}],
        })

    def test_sends_plain_text_email(self):
        from app.services.email_service import send_email

        with patch("app.services.email_service.settings.RESEND_API_KEY", "test_key"):
            with patch("app.services.email_service.settings.FROM_EMAIL", "hello@naxely.com"):
                with patch("resend.Emails.send") as mock_send:
                    result = send_email(
                        to="user@test.com",
                        subject="Plain text",
                        text="Hello world",
                    )

        assert result is True
        mock_send.assert_called_once_with({
            "from": "hello@naxely.com",
            "to": "user@test.com",
            "subject": "Plain text",
            "text": "Hello world",
        })

    def test_skips_when_api_key_missing(self):
        from app.services.email_service import send_email

        with patch("app.services.email_service.settings.RESEND_API_KEY", ""):
            with patch("resend.Emails.send") as mock_send:
                result = send_email(
                    to="user@test.com",
                    subject="Test",
                    html="<p>Hi</p>",
                )

        assert result is False
        mock_send.assert_not_called()

    def test_failure_returns_false(self):
        from app.services.email_service import send_email

        with patch("app.services.email_service.settings.RESEND_API_KEY", "test_key"):
            with patch("app.services.email_service.settings.FROM_EMAIL", "hello@naxely.com"):
                with patch("resend.Emails.send") as mock_send:
                    mock_send.side_effect = Exception("Resend down")
                    result = send_email(
                        to="user@test.com",
                        subject="Test",
                        html="<p>Hi</p>",
                    )

        assert result is False

    def test_sends_to_multiple_recipients(self):
        from app.services.email_service import send_email

        with patch("app.services.email_service.settings.RESEND_API_KEY", "test_key"):
            with patch("app.services.email_service.settings.FROM_EMAIL", "hello@naxely.com"):
                with patch("resend.Emails.send") as mock_send:
                    result = send_email(
                        to=["a@test.com", "b@test.com"],
                        subject="Multi",
                        html="<p>Hi</p>",
                    )

        assert result is True
        mock_send.assert_called_once_with({
            "from": "hello@naxely.com",
            "to": ["a@test.com", "b@test.com"],
            "subject": "Multi",
            "html": "<p>Hi</p>",
        })

    def test_regression_matches_payments_inline_payload_shape(self):
        """Regression: send_email() with html-only must match the exact payload
        shape that the inline payments.py code used to produce."""
        from app.services.email_service import send_email

        with patch("app.services.email_service.settings.RESEND_API_KEY", "test_key"):
            with patch("app.services.email_service.settings.FROM_EMAIL", "hello@naxely.com"):
                with patch("resend.Emails.send") as mock_send:
                    send_email(
                        to="user@example.com",
                        subject="Payment failed — Naxely",
                        html=(
                            "<p>Your most recent payment for Naxely failed.</p>"
                            "<p>Please update your billing information at "
                            "<a href='http://localhost:5173/settings/billing'>"
                            "http://localhost:5173/settings/billing</a> "
                            "to avoid any disruption to your subscription.</p>"
                        ),
                    )

        called_params = mock_send.call_args[0][0]
        assert called_params["from"] == "hello@naxely.com"
        assert called_params["to"] == "user@example.com"
        assert called_params["subject"] == "Payment failed — Naxely"
        assert "payment for Naxely failed" in called_params["html"]
        assert "attachments" not in called_params
