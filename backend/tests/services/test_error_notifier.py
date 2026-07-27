import pytest
import os
from unittest.mock import patch, MagicMock
import logging


class TestNotifyTelegramError:
    """Direct tests for notify_telegram_error itself."""

    def test_noop_when_env_vars_missing(self):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", ""):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", ""):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client:
                    notify_telegram_error(Exception("boom"), {"stage": "test"})
                    mock_client.assert_not_called()

    def test_noop_when_bot_token_missing(self):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", ""):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", "123"):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client:
                    notify_telegram_error(Exception("boom"), {"stage": "test"})
                    mock_client.assert_not_called()

    def test_noop_when_chat_id_missing(self):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", "bot:abc"):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", ""):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client:
                    notify_telegram_error(Exception("boom"), {"stage": "test"})
                    mock_client.assert_not_called()

    def test_sends_telegram_message_when_env_set(self):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", "bot:abc"):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", "-123"):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client_cls:
                    mock_ctx = MagicMock()
                    mock_client_cls.return_value.__enter__.return_value = mock_ctx
                    mock_ctx.post.return_value = mock_resp

                    notify_telegram_error(
                        Exception("test error"),
                        {"stage": "test_stage", "user_id": "u1", "user_email": "a@b.com"},
                    )

                    mock_ctx.post.assert_called_once()
                    call_kwargs = mock_ctx.post.call_args[1]
                    assert "json" in call_kwargs
                    assert call_kwargs["json"]["chat_id"] == "-123"
                    assert "test error" in call_kwargs["json"]["text"]
                    assert "test\\\\_stage" in call_kwargs["json"]["text"] or "test\\_stage" in call_kwargs["json"]["text"]

    def test_logs_warning_on_telegram_http_failure(self, caplog):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", "bot:abc"):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", "-123"):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client_cls:
                    mock_ctx = MagicMock()
                    mock_client_cls.return_value.__enter__.return_value = mock_ctx
                    mock_ctx.post.side_effect = Exception("http failure")

                    with caplog.at_level(logging.WARNING):
                        notify_telegram_error(Exception("boom"), {"stage": "test"})

                    assert "Failed to send Telegram alert" in caplog.text

    def test_never_propagates(self):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", "bot:abc"):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", "-123"):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client_cls:
                    mock_ctx = MagicMock()
                    mock_client_cls.return_value.__enter__.return_value = mock_ctx
                    mock_ctx.post.side_effect = RuntimeError("crash")

                    notify_telegram_error(Exception("boom"), {"stage": "test"})

    def test_truncates_long_error(self):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        long_msg = "x" * 2000
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", "bot:abc"):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", "-123"):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client_cls:
                    mock_ctx = MagicMock()
                    mock_client_cls.return_value.__enter__.return_value = mock_ctx
                    mock_ctx.post.return_value = mock_resp

                    notify_telegram_error(Exception(long_msg), {"stage": "test"})

                    sent_text = mock_ctx.post.call_args[1]["json"]["text"]
                    assert len(sent_text) < 1000

    def test_escapes_markdown_special_chars(self):
        from app.utils.error_notifier import notify_telegram_error, _warned_telegram_missing
        _warned_telegram_missing = False

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        with patch("app.core.config.settings.TELEGRAM_BOT_TOKEN", "bot:abc"):
            with patch("app.core.config.settings.TELEGRAM_CHAT_ID", "-123"):
                with patch("app.utils.error_notifier.httpx.Client") as mock_client_cls:
                    mock_ctx = MagicMock()
                    mock_client_cls.return_value.__enter__.return_value = mock_ctx
                    mock_ctx.post.return_value = mock_resp

                    notify_telegram_error(
                        Exception("error with *bold* and _italic_"),
                        {"stage": "test"},
                    )

                    sent_text = mock_ctx.post.call_args[1]["json"]["text"]
                    assert "\\*bold\\*" in sent_text
                    assert "\\_italic\\_" in sent_text


class TestNotifyInCallOpenaiCompat:
    """Verify notify_telegram_error fires on 500/504 branches in call_openai_compat."""

    def test_notify_on_timeout_504(self):
        from app.services.ai_service import call_openai_compat
        from app.services.ai_service import APITimeoutError

        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = APITimeoutError("timeout")

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_openai_compat("prompt", "system", "key")
                mock_notify.assert_called_once()

    def test_notify_on_generic_exception(self):
        from app.services.ai_service import call_openai_compat

        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = RuntimeError("network failure")

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                result = call_openai_compat("prompt", "system", "key")
                assert result is None
                mock_notify.assert_called_once()

    def test_no_notify_on_auth_400(self):
        import httpx
        from app.services.ai_service import call_openai_compat
        from openai import AuthenticationError as OpenAIAuthError

        httpx_resp = httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com/v1"))
        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = OpenAIAuthError(
                "401 Unauthorized", response=httpx_resp, body={}
            )

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(ValueError):
                    call_openai_compat("prompt", "system", "key")
                mock_notify.assert_not_called()

    def test_no_notify_on_rate_limit_429(self):
        import httpx
        from app.services.ai_service import call_openai_compat
        from openai import RateLimitError as OpenAIRateLimitError

        httpx_resp = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1"))
        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = OpenAIRateLimitError(
                "429 rate limit", response=httpx_resp, body={}
            )

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_openai_compat("prompt", "system", "key")
                mock_notify.assert_not_called()


class TestNotifyInCallClaude:
    """Verify notify_telegram_error fires on 500/504 branches in call_claude."""

    def test_notify_on_timeout_504(self):
        from app.services.ai_service import call_claude
        from app.services.ai_service import AnthropicTimeoutError

        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = AnthropicTimeoutError("timeout")

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_claude("prompt", "system", "key")
                mock_notify.assert_called_once()

    def test_notify_on_generic_500(self):
        from app.services.ai_service import call_claude

        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = RuntimeError("crash")

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_claude("prompt", "system", "key")
                mock_notify.assert_called_once()

    def test_notify_on_empty_result_500(self):
        from app.services.ai_service import call_claude

        mock_resp = MagicMock()
        mock_resp.content = []

        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_resp

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_claude("prompt", "system", "key")
                mock_notify.assert_called_once()

    def test_no_notify_on_auth_400(self):
        import httpx
        from app.services.ai_service import call_claude
        from anthropic import AuthenticationError as AnthropicAuthError

        httpx_resp = httpx.Response(401, request=httpx.Request("POST", "https://api.anthropic.com/v1"))
        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = AnthropicAuthError(
                "401 Unauthorized", response=httpx_resp, body={}
            )

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_claude("prompt", "system", "key")
                mock_notify.assert_not_called()

    def test_no_notify_on_rate_limit_429(self):
        import httpx
        from app.services.ai_service import call_claude
        from anthropic import RateLimitError as AnthropicRateLimitError

        httpx_resp = httpx.Response(429, request=httpx.Request("POST", "https://api.anthropic.com/v1"))
        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = AnthropicRateLimitError(
                "429 rate limit", response=httpx_resp, body={}
            )

            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_claude("prompt", "system", "key")
                mock_notify.assert_not_called()


class TestNotifyInCallGemini:
    """Verify notify_telegram_error fires on 500/504 branches in call_gemini."""

    def test_notify_on_empty_candidates_500(self):
        from app.services.ai_service import call_gemini

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"candidates": []}

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_gemini("prompt", "system", "key")
                mock_notify.assert_called_once()

    def test_notify_on_empty_text_500(self):
        from app.services.ai_service import call_gemini

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": ""}]}, "finishReason": "STOP"}]
        }

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_gemini("prompt", "system", "key")
                mock_notify.assert_called_once()

    def test_notify_on_request_exception_500(self):
        from app.services.ai_service import call_gemini
        import requests

        with patch("app.services.ai_service.requests.post", side_effect=requests.RequestException("connection failed")):
            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_gemini("prompt", "system", "key")
                mock_notify.assert_called_once()

    def test_notify_on_retry_exhausted_504(self):
        from app.services.ai_service import call_gemini

        resp_503 = MagicMock()
        resp_503.status_code = 503

        with patch("app.services.ai_service.requests.post", return_value=resp_503):
            with patch("app.services.ai_service.time.sleep"):
                with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                    with pytest.raises(Exception):
                        call_gemini("prompt", "system", "key")
                    mock_notify.assert_called_once()

    def test_no_notify_on_429(self):
        from app.services.ai_service import call_gemini

        resp = MagicMock()
        resp.status_code = 429

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_gemini("prompt", "system", "key")
                mock_notify.assert_not_called()

    def test_no_notify_on_403(self):
        from app.services.ai_service import call_gemini

        resp = MagicMock()
        resp.status_code = 403

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with patch("app.services.ai_service.notify_telegram_error") as mock_notify:
                with pytest.raises(Exception):
                    call_gemini("prompt", "system", "key")
                mock_notify.assert_not_called()
