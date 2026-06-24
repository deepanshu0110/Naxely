import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestDeepSeekErrorHandling:

    def test_deepseek_400_returns_none_not_raise(self):
        from app.services.ai_service import call_openai_compat
        from openai import BadRequestError as OpenAIBadRequestError

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"message": "Invalid parameter", "type": "invalid_request_error"}
        }
        mock_response.text = '{"error": {"message": "Invalid parameter"}}'

        def failing_create(*a, **kw):
            raise OpenAIBadRequestError("400", response=mock_response, body=mock_response.json())

        with patch("app.services.ai_service.OpenAI") as MockOpenAI:
            instance = MockOpenAI.return_value
            instance.chat.completions.create = failing_create
            result = call_openai_compat(
                prompt="hi", system="", api_key="sk-validkey123456789012",
                base_url="https://api.deepseek.com/v1", model="deepseek-chat",
            )

        assert result is None

    def test_deepseek_400_sets_ai_skipped_in_pipeline(self):
        from app.services.ai_service import generate_summary
        import pandas as pd

        df = pd.DataFrame({"Revenue": [100, 200, 300], "Region": ["A", "B", "C"]})
        config = {"sections": ["executive_summary"]}

        mock_user = MagicMock()
        mock_user.ai_provider = "deepseek"
        mock_user.encrypted_api_key = "encrypted"
        mock_user.api_key_iv = "iv"

        with patch("app.services.ai_service.get_user_api_key", return_value=("deepseek", "sk-test", None)):
            with patch("app.services.ai_service.call_openai_compat", return_value=None):
                summary = asyncio.run(generate_summary(df, config, mock_user))

        assert summary is None

    def test_deepseek_401_raises_value_error(self):
        from app.services.ai_service import call_openai_compat
        from openai import AuthenticationError as OpenAIAuthError

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        mock_response.text = '{"error": {"message": "Invalid API key"}}'

        def failing_create(*a, **kw):
            raise OpenAIAuthError("401", response=mock_response, body=mock_response.json())

        with patch("app.services.ai_service.OpenAI") as MockOpenAI:
            instance = MockOpenAI.return_value
            instance.chat.completions.create = failing_create
            with pytest.raises(ValueError) as exc_info:
                call_openai_compat(
                    prompt="hi", system="", api_key="sk-wrongkey",
                    base_url="https://api.deepseek.com/v1", model="deepseek-chat",
                )
        assert "Invalid API key" in str(exc_info.value)

    def test_deepseek_uses_correct_model_and_base_url(self):
        from app.services.ai_service import call_openai_compat

        captured_kwargs = {}

        def capture_create(*a, **kw):
            captured_kwargs.update(kw)
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message.content = "ok"
            return mock_resp

        with patch("app.services.ai_service.OpenAI") as MockOpenAI:
            instance = MockOpenAI.return_value
            instance.chat.completions.create = capture_create
            call_openai_compat(
                prompt="hi", system="", api_key="sk-validkey",
                base_url="https://api.deepseek.com/v1", model="deepseek-chat",
            )

        call_kwargs = MockOpenAI.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("base_url") == "https://api.deepseek.com/v1"
        assert captured_kwargs.get("model") == "deepseek-chat"

    def test_deepseek_api_key_save_rejects_invalid_format(self):
        import re
        from app.api.routes.settings import VALID_KEY_PATTERNS

        pattern = VALID_KEY_PATTERNS["deepseek"]
        valid_keys = [
            "sk-abc123def456ghi789jkl012",
            "abcdefghijklmnopqrstuvwxyz",
            "ABC123_-abc123_-abc123_-abc",
        ]
        invalid_keys = [
            "short",
            "",
            "invalid chars!",
        ]

        for key in valid_keys:
            assert re.match(pattern, key), f"Valid key rejected: {key}"
        for key in invalid_keys:
            assert not re.match(pattern, key), f"Invalid key accepted: {key}"

    def test_deepseek_error_message_is_descriptive(self):
        from app.services.ai_service import call_openai_compat
        from openai import BadRequestError as OpenAIBadRequestError

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"message": "Unsupported parameter: logprobs"}
        }
        mock_response.text = '{"error": {"message": "Unsupported parameter: logprobs"}}'

        def failing_create(*a, **kw):
            raise OpenAIBadRequestError("400", response=mock_response, body=mock_response.json())

        with patch("app.services.ai_service.OpenAI") as MockOpenAI:
            instance = MockOpenAI.return_value
            instance.chat.completions.create = failing_create
            result = call_openai_compat(
                prompt="test", system="", api_key="sk-validkey",
                base_url="https://api.deepseek.com/v1", model="deepseek-chat",
            )

        assert result is None
