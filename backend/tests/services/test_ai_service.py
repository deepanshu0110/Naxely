import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestAnomalyDetection:
    def test_detect_anomalies_returns_list(self):
        from app.services.ai_service import detect_anomalies

        df = pd.DataFrame({
            "Values": [10, 12, 11, 13, 10, 100, 12, 11, 13, 12],
        })
        result = detect_anomalies(df)
        assert isinstance(result, list)

    def test_detect_anomalies_normal_data(self):
        from app.services.ai_service import detect_anomalies

        np.random.seed(42)
        df = pd.DataFrame({
            "Values": np.random.normal(50, 5, 100),
        })
        result = detect_anomalies(df)
        assert len(result) <= 5

    def test_detect_anomalies_with_outlier(self):
        from app.services.ai_service import detect_anomalies

        df = pd.DataFrame({
            "Values": [10, 12, 11, 13, 10, 100, 12, 11, 13, 12],
        })
        result = detect_anomalies(df)
        if result:
            anomaly = result[0]
            assert "column" in anomaly
            assert "value" in anomaly
            assert "z_score" in anomaly
            assert "message" in anomaly

    def test_detect_anomalies_small_dataset(self):
        from app.services.ai_service import detect_anomalies

        df = pd.DataFrame({"A": [1, 2]})
        result = detect_anomalies(df)
        assert result == []

    def test_detect_anomalies_non_numeric(self):
        from app.services.ai_service import detect_anomalies

        df = pd.DataFrame({"A": ["x", "y", "z"]})
        result = detect_anomalies(df)
        assert result == []

    def test_detect_anomalies_empty_df(self):
        from app.services.ai_service import detect_anomalies

        df = pd.DataFrame()
        result = detect_anomalies(df)
        assert result == []


class TestTrendDetection:
    def test_detect_trends_returns_list(self):
        from app.services.ai_service import detect_trends

        df = pd.DataFrame({
            "Revenue": [100, 200, 300, 400, 500],
        })
        result = detect_trends(df)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_detect_trends_increasing(self):
        from app.services.ai_service import detect_trends

        df = pd.DataFrame({
            "Revenue": [100, 200, 300, 400, 500],
        })
        result = detect_trends(df)
        assert result[0]["trend"] == "increasing"
        assert result[0]["pct_change"] > 0

    def test_detect_trends_decreasing(self):
        from app.services.ai_service import detect_trends

        df = pd.DataFrame({
            "Revenue": [500, 400, 300, 200, 100],
        })
        result = detect_trends(df)
        assert result[0]["trend"] == "decreasing"

    def test_detect_trends_flat(self):
        from app.services.ai_service import detect_trends

        df = pd.DataFrame({
            "Revenue": [100, 100, 101, 100, 100],
        })
        result = detect_trends(df)
        assert result[0]["trend"] == "flat"

    def test_detect_trends_non_numeric_skipped(self):
        from app.services.ai_service import detect_trends

        df = pd.DataFrame({
            "Category": ["A", "B", "C", "D", "E"],
        })
        result = detect_trends(df)
        assert result == []

    def test_detect_trends_small_data(self):
        from app.services.ai_service import detect_trends

        df = pd.DataFrame({"A": [1]})
        result = detect_trends(df)
        assert result == []


class TestGeminiRetry:
    def test_requests_post_called_once_on_success(self, monkeypatch):
        from app.services.ai_service import call_gemini

        calls = []

        def recording_post(*args, **kwargs):
            calls.append(1)
            raise Exception("API reachable")

        monkeypatch.setattr("app.services.ai_service.requests.post", recording_post)

        with pytest.raises(Exception):
            call_gemini("prompt", "system", "fake-key")
        assert len(calls) == 1, f"Expected 1 POST call, got {len(calls)}"

    def test_requests_post_called_three_times_on_all_503(self, monkeypatch):
        from app.services.ai_service import call_gemini

        calls = []

        def mock_503_post(*args, **kwargs):
            calls.append(1)
            resp = type("FakeResp", (), {
                "status_code": 503,
                "raise_for_status": lambda self: None,
                "json": lambda self: {},
            })()
            return resp

        monkeypatch.setattr("app.services.ai_service.requests.post", mock_503_post)
        monkeypatch.setattr("app.services.ai_service.time.sleep", lambda s: None)

        with pytest.raises(Exception):
            call_gemini("prompt", "system", "fake-key")
        assert len(calls) == 3, f"Expected 3 POST calls on all-503, got {len(calls)}"

    def test_timeout_retries_and_succeeds_on_attempt_2(self, monkeypatch):
        import requests
        from app.services.ai_service import call_gemini

        call_count = 0

        def timeout_then_ok(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise requests.Timeout("timed out")
            resp = type("FakeResp", (), {
                "status_code": 200,
                "raise_for_status": lambda self: None,
                "json": lambda self: {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]},
            })()
            return resp

        monkeypatch.setattr("app.services.ai_service.requests.post", timeout_then_ok)
        monkeypatch.setattr("app.services.ai_service.time.sleep", lambda s: None)

        result = call_gemini("prompt", "system", "fake-key")
        assert result == "ok"
        assert call_count == 2

    def test_no_retry_on_non_503_errors(self, monkeypatch):
        from app.services.ai_service import call_gemini

        calls = []

        def mock_400_post(*args, **kwargs):
            calls.append(1)
            resp = type("FakeResp", (), {
                "status_code": 400,
                "raise_for_status": lambda self: None,
                "json": lambda self: {},
                "text": "bad request",
            })()
            return resp

        monkeypatch.setattr("app.services.ai_service.requests.post", mock_400_post)

        with pytest.raises(Exception):
            call_gemini("prompt", "system", "fake-key")
        assert len(calls) == 1, f"Expected 1 POST call on 400 (no retry), got {len(calls)}"

    def test_gemini_url_redacted_in_log_on_error(self, monkeypatch):
        import io
        import logging
        import requests
        from app.services.ai_service import call_gemini

        captured = io.StringIO()
        handler = logging.StreamHandler(captured)
        handler.setLevel(logging.ERROR)
        logger = logging.getLogger("app.services.ai_service")
        logger.addHandler(handler)
        original_level = logger.level
        logger.setLevel(logging.ERROR)

        try:
            def error_post(*args, **kwargs):
                resp = type("FakeResp", (), {
                    "status_code": 500,
                    "raise_for_status": lambda self: None,
                    "text": "internal error",
                })()
                raise requests.RequestException("boom", response=resp)

            monkeypatch.setattr("app.services.ai_service.requests.post", error_post)

            with pytest.raises(Exception):
                call_gemini("prompt", "system", "my-secret-key")

            log_output = captured.getvalue()
            assert "***REDACTED***" in log_output, "Expected key to be redacted in log"
            assert "my-secret-key" not in log_output, "Raw key leaked into log"
        finally:
            logger.removeHandler(handler)
            logger.setLevel(original_level)


class TestBuildColumnStats:
    def test_build_column_stats_structure(self):
        from app.services.ai_service import _build_column_stats

        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "Revenue": [1000, 2000, 1500, 3000, 2500, 1800, 2200, 3500, 2800, 4000],
            "Region": ["North", "South"] * 5,
        })
        stats = _build_column_stats(df)
        assert "columns" in stats
        assert "date_column" in stats
        assert "date_range" in stats
        assert stats["date_column"] == "Date"

    def test_build_column_stats_metric_entry(self):
        from app.services.ai_service import _build_column_stats

        df = pd.DataFrame({
            "Revenue": [100, 200, 300],
        })
        stats = _build_column_stats(df)
        rev = [c for c in stats["columns"] if c["name"] == "Revenue"][0]
        assert rev["type"] == "metric"
        assert rev["mean"] is not None
        assert rev["min"] is not None
        assert rev["max"] is not None


class TestDeepSeekValidation:
    def test_deepseek_valid_key_passes_validation(self):
        from app.services.ai_service import validate_api_key
        with patch("app.services.ai_service.call_openai_compat") as mock_call:
            mock_call.return_value = {"choices": [{"message": {"content": "ok"}}]}
            result = validate_api_key(provider="deepseek", api_key="sk-abc123validkey")
        assert result["valid"] is True

    def test_deepseek_400_from_api_treated_as_valid_key(self):
        from app.services.ai_service import validate_api_key
        with patch("app.services.ai_service.call_openai_compat") as mock_call:
            mock_call.side_effect = Exception("400 Bad Request")
            result = validate_api_key(provider="deepseek", api_key="sk-abc123validkey")
        assert result["valid"] is True
        assert "message" in result

    def test_deepseek_401_treated_as_invalid_key(self):
        from app.services.ai_service import validate_api_key
        with patch("app.services.ai_service.call_openai_compat") as mock_call:
            mock_call.side_effect = Exception("401 Unauthorized")
            result = validate_api_key(provider="deepseek", api_key="sk-wrongkey")
        assert result["valid"] is False

    def test_deepseek_uses_correct_model_for_validation(self):
        from app.services.ai_service import validate_api_key
        with patch("app.services.ai_service.call_openai_compat") as mock_call:
            mock_call.return_value = {"choices": [{"message": {"content": "ok"}}]}
            validate_api_key(provider="deepseek", api_key="sk-abc123")
        call_kwargs = mock_call.call_args
        assert "deepseek-chat" in str(call_kwargs)

    def test_deepseek_base_url_correct(self):
        from app.services.ai_service import validate_api_key
        with patch("app.services.ai_service.call_openai_compat") as mock_call:
            mock_call.return_value = {"choices": [{"message": {"content": "ok"}}]}
            validate_api_key(provider="deepseek", api_key="sk-abc123")
        call_kwargs = mock_call.call_args
        assert "api.deepseek.com" in str(call_kwargs)


class TestGetUserApiKey:
    def test_free_user_no_key_returns_none(self):
        from app.services.ai_service import get_user_api_key
        from unittest.mock import MagicMock
        user = MagicMock()
        user.subscription_tier = "free"
        user.tier = "free"
        user.encrypted_api_key = None
        user.api_key_iv = None
        provider, key, base_url = get_user_api_key(user)
        assert provider is None
        assert key is None

    def test_free_user_with_key_gets_byok(self):
        from app.services.ai_service import get_user_api_key
        from unittest.mock import MagicMock, patch
        user = MagicMock()
        user.subscription_tier = "free"
        user.tier = "free"
        user.encrypted_api_key = b"encrypted"
        user.api_key_iv = b"iv"
        user.ai_provider = "groq"
        with patch("app.services.ai_service.decrypt_api_key", return_value="gsk_testkey"):
            provider, key, base_url = get_user_api_key(user)
        assert provider == "groq"
        assert key == "gsk_testkey"

    def test_pro_user_no_key_returns_none(self):
        """Pro user with no stored key now gets (None, None, None) — no server fallback."""
        from app.services.ai_service import get_user_api_key
        from unittest.mock import MagicMock
        user = MagicMock()
        user.subscription_tier = "pro"
        user.tier = "pro"
        user.encrypted_api_key = None
        user.api_key_iv = None
        provider, key, base_url = get_user_api_key(user)
        assert provider is None
        assert key is None

    def test_gemini_byok_decrypted_not_server_key(self):
        """Gemini user with stored key gets decrypted key, not settings.GEMINI_API_KEY."""
        from app.services.ai_service import get_user_api_key
        from unittest.mock import MagicMock, patch
        user = MagicMock()
        user.subscription_tier = "free"
        user.tier = "free"
        user.encrypted_api_key = b"encrypted_gemini"
        user.api_key_iv = b"iv_gemini"
        user.ai_provider = "gemini"
        with patch("app.services.ai_service.decrypt_api_key", return_value="AQ.test_real_key_abc123"):
            provider, key, base_url = get_user_api_key(user)
        assert provider == "gemini"
        assert key == "AQ.test_real_key_abc123"
        assert key != "", "Must not return empty server-side key"


# ── Fix 2: Insight Card Dedup Tests ────────────────────────────────────────────

class TestDedupInsightsByKpi:
    def test_dedup_insights_removes_duplicate_kpi(self):
        from app.services.ai_service import _dedup_insights_by_kpi

        cards = [
            {"kpi": "Units Sold", "priority": "high",   "number": "105",   "reason": "a", "action": "b", "sentiment": "positive"},
            {"kpi": "Revenue",    "priority": "high",   "number": "14609", "reason": "c", "action": "d", "sentiment": "positive"},
            {"kpi": "Units Sold", "priority": "medium", "number": "75.24", "reason": "e", "action": "f", "sentiment": "neutral"},
            {"kpi": "Units Sold", "priority": "medium", "number": "149",   "reason": "g", "action": "h", "sentiment": "positive"},
        ]
        result = _dedup_insights_by_kpi(cards)
        kpis = [c["kpi"] for c in result]

        assert kpis.count("Units Sold") == 1, "Duplicate Units Sold cards not removed"
        assert kpis.count("Revenue") == 1
        assert len(result) == 2

    def test_dedup_insights_keeps_first_occurrence(self):
        from app.services.ai_service import _dedup_insights_by_kpi

        cards = [
            {"kpi": "Revenue", "priority": "high",   "number": "14609", "reason": "a", "action": "b", "sentiment": "positive"},
            {"kpi": "Revenue", "priority": "low",    "number": "12572", "reason": "c", "action": "d", "sentiment": "neutral"},
        ]
        result = _dedup_insights_by_kpi(cards)
        assert len(result) == 1
        assert result[0]["priority"] == "high"  # first card (highest priority) kept


class TestDedupInsightsByColumn:
    """Dedup should prefer the 'column' field over 'kpi' when available."""

    def test_dedup_same_column_different_kpi_labels(self):
        """Same column 'Units Sold' with different kpi labels → only one kept."""
        from app.services.ai_service import _dedup_insights_by_kpi

        cards = [
            {"kpi": "Units Sold",         "column": "Units Sold", "number": "105",   "reason": "a", "action": "b", "sentiment": "positive", "priority": "high"},
            {"kpi": "Units Sold Average",  "column": "Units Sold", "number": "75.24", "reason": "c", "action": "d", "sentiment": "neutral", "priority": "medium"},
            {"kpi": "Units Sold Max",      "column": "Units Sold", "number": "149",   "reason": "e", "action": "f", "sentiment": "positive", "priority": "low"},
        ]
        result = _dedup_insights_by_kpi(cards)
        assert len(result) == 1, (
            f"Expected 1 card (same column 'Units Sold'), got {len(result)}"
        )
        assert result[0]["kpi"] == "Units Sold", (
            "First (highest-priority) card should be kept"
        )

    def test_dedup_different_columns_all_kept(self):
        """Genuinely different source columns → all kept, not over-merged."""
        from app.services.ai_service import _dedup_insights_by_kpi

        cards = [
            {"kpi": "Revenue",          "column": "Revenue",          "number": "14609", "reason": "a", "action": "b", "sentiment": "positive", "priority": "high"},
            {"kpi": "Units Sold",       "column": "Units Sold",       "number": "105",   "reason": "c", "action": "d", "sentiment": "positive", "priority": "high"},
            {"kpi": "Customer Satis.",  "column": "Satisfaction",     "number": "4.5",   "reason": "e", "action": "f", "sentiment": "positive", "priority": "medium"},
        ]
        result = _dedup_insights_by_kpi(cards)
        assert len(result) == 3, (
            f"Expected all 3 distinct columns kept, got {len(result)}"
        )

    def test_dedup_different_column_names_not_merged(self):
        """'Total Revenue' vs 'Revenue Growth' are different columns → not merged."""
        from app.services.ai_service import _dedup_insights_by_kpi

        cards = [
            {"kpi": "Total Revenue",    "column": "Total Revenue",    "number": "50000", "reason": "a", "action": "b", "sentiment": "positive", "priority": "high"},
            {"kpi": "Revenue Growth",   "column": "Revenue Growth",   "number": "12.5%", "reason": "c", "action": "d", "sentiment": "positive", "priority": "high"},
        ]
        result = _dedup_insights_by_kpi(cards)
        assert len(result) == 2, (
            f"Expected 2 distinct columns kept, got {len(result)} — "
            "Total Revenue and Revenue Growth must not be merged"
        )

    def test_dedup_fallback_to_kpi_when_column_missing(self):
        """Backward compat: insights without 'column' field still dedup by kpi."""
        from app.services.ai_service import _dedup_insights_by_kpi

        cards = [
            {"kpi": "Units Sold", "number": "105",   "reason": "a", "action": "b", "sentiment": "positive", "priority": "high"},
            {"kpi": "Units Sold", "number": "75.24", "reason": "c", "action": "d", "sentiment": "neutral", "priority": "medium"},
        ]
        result = _dedup_insights_by_kpi(cards)
        assert len(result) == 1, (
            "Missing 'column' should fall back to exact kpi match"
        )


# ── Executive Summary 4-Part Parser Tests ────────────────────────────────────

class TestParseSummarySections:
    """_parse_summary_sections should extract the 4 delimited parts."""

    WELL_FORMED = (
        "[LEAD]Revenue grew 33.9% over the period, reaching $9,494 in the latest reading.[/LEAD]\n"
        "[CONTEXT]Customer satisfaction held steady at 4.2/5.0 across all regions.[/CONTEXT]\n"
        "[IMPLICATION]The combination of rising revenue and stable satisfaction suggests pricing power is intact.[/IMPLICATION]\n"
        "[ACTION]Increase ad spend on the highest-margin product line to capitalize on momentum.[/ACTION]"
    )

    def test_parses_well_formed(self):
        from app.services.ai_service import _parse_summary_sections, SummaryResult
        result = _parse_summary_sections(self.WELL_FORMED)
        assert result is not None
        assert result.lead == "Revenue grew 33.9% over the period, reaching $9,494 in the latest reading."
        assert result.context == "Customer satisfaction held steady at 4.2/5.0 across all regions."
        assert result.implication == "The combination of rising revenue and stable satisfaction suggests pricing power is intact."
        assert result.action == "Increase ad spend on the highest-margin product line to capitalize on momentum."

    def test_parses_well_formed_full_text(self):
        from app.services.ai_service import _parse_summary_sections
        result = _parse_summary_sections(self.WELL_FORMED)
        assert result is not None
        assert "Revenue grew 33.9%" in result.full_text
        assert "Customer satisfaction" in result.full_text
        assert "pricing power" in result.full_text
        assert "Increase ad spend" in result.full_text

    def test_missing_one_tag_returns_what_it_has(self):
        from app.services.ai_service import _parse_summary_sections
        raw = (
            "[LEAD]Revenue grew 33.9%.[/LEAD]\n"
            "[IMPLICATION]This is a strong sign.[/IMPLICATION]\n"
            "[ACTION]Invest more.[/ACTION]\n"
        )
        result = _parse_summary_sections(raw)
        assert result is not None
        assert result.lead == "Revenue grew 33.9%."
        assert result.context == ""  # missing
        assert result.implication == "This is a strong sign."
        assert result.action == "Invest more."

    def test_no_delimiters_falls_back_to_full_text_as_lead(self):
        from app.services.ai_service import _parse_summary_sections
        raw = "Revenue grew 33.9% over the period. This is a positive sign for the business."
        result = _parse_summary_sections(raw)
        assert result is not None
        assert result.lead == raw
        assert result.context == ""
        assert result.implication == ""
        assert result.action == ""

    def test_empty_input_returns_none(self):
        from app.services.ai_service import _parse_summary_sections
        assert _parse_summary_sections("") is None
        assert _parse_summary_sections("   ") is None
        assert _parse_summary_sections(None) is None

    def test_handles_multiline_content(self):
        from app.services.ai_service import _parse_summary_sections
        raw = (
            "[LEAD]Revenue grew 33.9%\nover the period.[/LEAD]\n"
            "[CONTEXT]This is context\nspanning two lines.[/CONTEXT]\n"
            "[IMPLICATION]Important implication here.[/IMPLICATION]\n"
            "[ACTION]Do this action now.[/ACTION]"
        )
        result = _parse_summary_sections(raw)
        assert result is not None
        assert "33.9%" in result.lead
        assert "spanning two lines" in result.context


class TestSummaryResult:
    """SummaryResult dataclass behavior."""

    def test_full_text_concatenates_all_parts(self):
        from app.services.ai_service import SummaryResult
        sr = SummaryResult(
            lead="Lead here.",
            context="Context here.",
            implication="Implication here.",
            action="Action here.",
        )
        assert "Lead here." in sr.full_text
        assert "Context here." in sr.full_text
        assert "Implication here." in sr.full_text
        assert "Action here." in sr.full_text

    def test_bool_true_when_content_exists(self):
        from app.services.ai_service import SummaryResult
        assert bool(SummaryResult(lead="Something.")) is True

    def test_bool_false_when_empty(self):
        from app.services.ai_service import SummaryResult
        assert bool(SummaryResult()) is False

    def test_bool_false_when_whitespace_only(self):
        from app.services.ai_service import SummaryResult
        assert bool(SummaryResult(lead="   ")) is False


class TestGenerateSummaryStructured:
    """generate_summary should return SummaryResult with delimited output."""

    def test_returns_summary_result_when_ai_returns_delimited(self):
        from app.services.ai_service import generate_summary, SummaryResult
        import asyncio

        df = pd.DataFrame({"Revenue": [100, 200, 300], "Region": ["A", "B", "C"]})
        config = {"sections": ["executive_summary"]}

        mock_user = MagicMock()
        mock_user.ai_provider = "deepseek"
        mock_user.encrypted_api_key = "encrypted"
        mock_user.api_key_iv = "iv"

        delimited = (
            "[LEAD]Revenue grew 200.0% over the period.[/LEAD]\n"
            "[CONTEXT]Region A contributed the majority of growth.[/CONTEXT]\n"
            "[IMPLICATION]The company should focus on its strongest region.[/IMPLICATION]\n"
            "[ACTION]Double down on Region A marketing spend.[/ACTION]"
        )

        with patch("app.services.ai_service.get_user_api_key", return_value=("deepseek", "sk-test", None)):
            with patch("app.services.ai_service.call_openai_compat", return_value=delimited):
                summary = asyncio.run(generate_summary(df, config, mock_user))

        assert isinstance(summary, SummaryResult)
        assert "200.0%" in summary.lead
        assert summary.context != ""
        assert summary.implication != ""
        assert summary.action != ""

    def test_returns_summary_result_when_ai_returns_plain_text(self):
        """Fallback: no delimiters → full text becomes lead, rest empty."""
        from app.services.ai_service import generate_summary, SummaryResult
        import asyncio

        df = pd.DataFrame({"Revenue": [100, 200, 300], "Region": ["A", "B", "C"]})
        config = {"sections": ["executive_summary"]}

        mock_user = MagicMock()
        mock_user.ai_provider = "deepseek"
        mock_user.encrypted_api_key = "encrypted"
        mock_user.api_key_iv = "iv"

        plain_text = "Revenue grew 200.0% over the period. This is a strong result."

        with patch("app.services.ai_service.get_user_api_key", return_value=("deepseek", "sk-test", None)):
            with patch("app.services.ai_service.call_openai_compat", return_value=plain_text):
                summary = asyncio.run(generate_summary(df, config, mock_user))

        assert isinstance(summary, SummaryResult)
        assert summary.lead == plain_text
        assert summary.context == ""
        assert summary.implication == ""
        assert summary.action == ""

    def test_returns_none_when_ai_returns_none(self):
        from app.services.ai_service import generate_summary
        import asyncio

        df = pd.DataFrame({"Revenue": [100, 200, 300]})
        config = {"sections": ["executive_summary"]}

        mock_user = MagicMock()
        mock_user.ai_provider = "deepseek"
        mock_user.encrypted_api_key = "encrypted"
        mock_user.api_key_iv = "iv"

        with patch("app.services.ai_service.get_user_api_key", return_value=("deepseek", "sk-test", None)):
            with patch("app.services.ai_service.call_openai_compat", return_value=None):
                summary = asyncio.run(generate_summary(df, config, mock_user))

        assert summary is None


# ── _call_ai Dispatch Tests ────────────────────────────────────────────────────

class TestCallAiDispatch:
    """_call_ai should dispatch to the correct provider function."""

    def test_call_ai_claude(self):
        from app.services import ai_service as ai_service_mod
        with patch.object(ai_service_mod, "call_claude", return_value="resp") as mock:
            result = ai_service_mod._call_ai("claude", "p", "s", "k")
        assert result == "resp"
        mock.assert_called_once_with("p", "s", "k", 25)

    def test_call_ai_gemini(self):
        from app.services import ai_service as ai_service_mod
        with patch.object(ai_service_mod, "call_gemini", return_value="resp") as mock:
            result = ai_service_mod._call_ai("gemini", "p", "s", "k")
        assert result == "resp"
        mock.assert_called_once_with("p", "s", "k", 25)

    def test_call_ai_openai(self):
        from app.services import ai_service as ai_service_mod
        with patch.object(ai_service_mod, "call_openai_compat", return_value="resp") as mock:
            result = ai_service_mod._call_ai("openai", "p", "s", "k")
        assert result == "resp"
        mock.assert_called_once_with("p", "s", "k", 25,
            base_url="https://api.openai.com/v1", model="gpt-4o")

    def test_call_ai_groq(self):
        from app.services import ai_service as ai_service_mod
        with patch.object(ai_service_mod, "call_openai_compat", return_value="resp") as mock:
            result = ai_service_mod._call_ai("groq", "p", "s", "k")
        assert result == "resp"
        mock.assert_called_once_with("p", "s", "k", 25,
            base_url="https://api.groq.com/openai/v1", model="openai/gpt-oss-120b")

    def test_call_ai_deepseek(self):
        from app.services import ai_service as ai_service_mod
        with patch.object(ai_service_mod, "call_openai_compat", return_value="resp") as mock:
            result = ai_service_mod._call_ai("deepseek", "p", "s", "k")
        assert result == "resp"
        mock.assert_called_once_with("p", "s", "k", 25,
            base_url="https://api.deepseek.com/v1", model="deepseek-chat")

    def test_call_ai_mistral(self):
        from app.services import ai_service as ai_service_mod
        with patch.object(ai_service_mod, "call_openai_compat", return_value="resp") as mock:
            result = ai_service_mod._call_ai("mistral", "p", "s", "k")
        assert result == "resp"
        mock.assert_called_once_with("p", "s", "k", 25,
            base_url="https://api.mistral.ai/v1", model="mistral-large-latest")

    def test_call_ai_unknown_provider_falls_back(self):
        """Unknown provider calls call_openai (not call_openai_compat)."""
        from app.services import ai_service as ai_service_mod
        with patch.object(ai_service_mod, "call_openai", return_value="fallback") as mock:
            with patch.object(ai_service_mod, "call_openai_compat") as mock_compat:
                result = ai_service_mod._call_ai("unknown", "p", "s", "k")
        assert result == "fallback"
        mock.assert_called_once_with("p", "s", "k", 25)
        mock_compat.assert_not_called()


class TestCallOpenaiCompat:
    """call_openai_compat error handling."""

    def _make_mock_response(self, content="test content"):
        mock_msg = MagicMock()
        mock_msg.content = content
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        return mock_resp

    def test_openai_compat_success(self):
        from app.services.ai_service import call_openai_compat
        mock_resp = self._make_mock_response("hello world")
        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_resp
            result = call_openai_compat("prompt", "system", "key")
        assert result == "hello world"

    def test_openai_compat_auth_error(self):
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
            with pytest.raises(ValueError, match="Invalid API key"):
                call_openai_compat("prompt", "system", "key")

    def test_openai_compat_rate_limit(self):
        import httpx
        from app.services.ai_service import call_openai_compat
        from fastapi import HTTPException
        from openai import RateLimitError as OpenAIRateLimitError
        httpx_resp = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1"))
        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = OpenAIRateLimitError(
                "429 rate limit", response=httpx_resp, body={}
            )
            with pytest.raises(HTTPException) as exc:
                call_openai_compat("prompt", "system", "key")
        assert exc.value.status_code == 429

    def test_openai_compat_bad_request(self):
        import httpx
        from app.services.ai_service import call_openai_compat
        from openai import BadRequestError as OpenAIBadRequestError
        httpx_resp = httpx.Response(400, json={"error": {"message": "unsupported param"}},
                                     request=httpx.Request("POST", "https://api.openai.com/v1"))
        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = OpenAIBadRequestError(
                "bad request", response=httpx_resp, body=httpx_resp.json()
            )
            result = call_openai_compat("prompt", "system", "key")
        assert result is None

    def test_openai_compat_timeout(self):
        from app.services.ai_service import call_openai_compat
        from fastapi import HTTPException
        from openai import APITimeoutError
        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = APITimeoutError("timed out")
            with pytest.raises(HTTPException) as exc:
                call_openai_compat("prompt", "system", "key")
        assert exc.value.status_code == 504

    def test_openai_compat_other_error(self):
        from app.services.ai_service import call_openai_compat
        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = RuntimeError("unexpected")
            result = call_openai_compat("prompt", "system", "key")
        assert result is None


class TestCallClaude:
    """call_claude error handling."""

    def _make_mock_claude_response(self, text="claude response"):
        mock_content_block = MagicMock()
        mock_content_block.text = text
        mock_response = MagicMock()
        mock_response.content = [mock_content_block]
        return mock_response

    def test_claude_success(self):
        from app.services.ai_service import call_claude
        mock_resp = self._make_mock_claude_response("hello from claude")
        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_resp
            result = call_claude("prompt", "system", "key")
        assert result == "hello from claude"

    def test_claude_auth_error(self):
        import httpx
        from app.services.ai_service import call_claude
        from fastapi import HTTPException
        from anthropic import AuthenticationError as AnthropicAuthError
        httpx_resp = httpx.Response(401, request=httpx.Request("POST", "https://api.anthropic.com/v1"))
        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = AnthropicAuthError(
                "401 Unauthorized", response=httpx_resp, body={}
            )
            with pytest.raises(HTTPException) as exc:
                call_claude("prompt", "system", "key")
        assert exc.value.status_code == 400

    def test_claude_rate_limit(self):
        import httpx
        from app.services.ai_service import call_claude
        from fastapi import HTTPException
        from anthropic import RateLimitError as AnthropicRateLimitError
        httpx_resp = httpx.Response(429, request=httpx.Request("POST", "https://api.anthropic.com/v1"))
        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = AnthropicRateLimitError(
                "429 rate limit", response=httpx_resp, body={}
            )
            with pytest.raises(HTTPException) as exc:
                call_claude("prompt", "system", "key")
        assert exc.value.status_code == 429

    def test_claude_timeout(self):
        from app.services.ai_service import call_claude
        from fastapi import HTTPException
        from anthropic import APITimeoutError as AnthropicTimeoutError
        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = AnthropicTimeoutError("timed out")
            with pytest.raises(HTTPException) as exc:
                call_claude("prompt", "system", "key")
        assert exc.value.status_code == 504

    def test_claude_other_error(self):
        from app.services.ai_service import call_claude
        from fastapi import HTTPException
        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = RuntimeError("unknown")
            with pytest.raises(HTTPException) as exc:
                call_claude("prompt", "system", "key")
        assert exc.value.status_code == 500


class TestCallGemini:
    """call_gemini additional edge cases beyond retry behavior."""

    def _make_200_response(self, text="gemini text"):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": text}]},
                "finishReason": "STOP",
            }]
        }
        return resp

    def test_gemini_success(self):
        from app.services.ai_service import call_gemini
        resp = self._make_200_response("success")
        with patch("app.services.ai_service.requests.post", return_value=resp):
            result = call_gemini("prompt", "system", "key")
        assert result == "success"

    def test_gemini_503_retry_then_success(self):
        from app.services.ai_service import call_gemini

        resp_503 = MagicMock()
        resp_503.status_code = 503
        resp_200 = self._make_200_response("recovered")
        calls = [resp_503, resp_200]

        def side_effect(*args, **kwargs):
            return calls.pop(0)

        with patch("app.services.ai_service.requests.post", side_effect=side_effect):
            with patch("app.services.ai_service.time.sleep"):
                result = call_gemini("prompt", "system", "key")
        assert result == "recovered"

    def test_gemini_all_503_exhausted(self):
        from app.services.ai_service import call_gemini
        from fastapi import HTTPException

        resp_503 = MagicMock()
        resp_503.status_code = 503

        with patch("app.services.ai_service.requests.post", return_value=resp_503):
            with patch("app.services.ai_service.time.sleep"):
                with pytest.raises(HTTPException) as exc:
                    call_gemini("prompt", "system", "key")
        assert exc.value.status_code == 504

    def test_gemini_url_key_redacted_on_error(self):
        import io
        import logging
        import requests
        from app.services.ai_service import call_gemini
        from fastapi import HTTPException

        captured = io.StringIO()
        handler = logging.StreamHandler(captured)
        handler.setLevel(logging.ERROR)
        logger = logging.getLogger("app.services.ai_service")
        logger.addHandler(handler)
        original_level = logger.level
        logger.setLevel(logging.ERROR)

        try:
            with patch("app.services.ai_service.requests.post",
                       side_effect=requests.RequestException("boom")):
                with pytest.raises(HTTPException):
                    call_gemini("prompt", "system", "my-secret-api-key-12345")

            log_output = captured.getvalue()
            assert "***REDACTED***" in log_output
            assert "my-secret-api-key-12345" not in log_output
        finally:
            logger.removeHandler(handler)
            logger.setLevel(original_level)

    def test_gemini_empty_candidates(self):
        from app.services.ai_service import call_gemini
        from fastapi import HTTPException

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"candidates": []}

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with pytest.raises(HTTPException) as exc:
                call_gemini("prompt", "system", "key")
        assert exc.value.status_code == 500

    def test_gemini_429_rate_limit(self):
        from app.services.ai_service import call_gemini
        from fastapi import HTTPException

        resp = MagicMock()
        resp.status_code = 429

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with pytest.raises(HTTPException) as exc:
                call_gemini("prompt", "system", "key")
        assert exc.value.status_code == 429


class TestGenerateSummaryEdgeCases:
    """Edge cases for generate_summary."""

    def test_generate_summary_no_api_key(self):
        from app.services.ai_service import generate_summary
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()
        with patch("app.services.ai_service.get_user_api_key", return_value=(None, None, None)):
            result = asyncio.run(generate_summary(df, config, user))
        assert result is None

    def test_generate_summary_http_exception_in_get_key(self):
        from app.services.ai_service import generate_summary
        from fastapi import HTTPException
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()
        with patch("app.services.ai_service.get_user_api_key",
                   side_effect=HTTPException(status_code=400)):
            result = asyncio.run(generate_summary(df, config, user))
        assert result is None

    def test_generate_summary_empty_result(self):
        from app.services.ai_service import generate_summary
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()
        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._call_ai", return_value=""):
                result = asyncio.run(generate_summary(df, config, user))
        assert result is None


class TestGenerateRecommendations:
    """generate_recommendations edge cases."""

    def test_recommendations_no_api_key(self):
        from app.services.ai_service import generate_recommendations
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()
        with patch("app.services.ai_service.get_user_api_key", return_value=(None, None, None)):
            result = asyncio.run(generate_recommendations(df, config, user))
        assert result == []

    def test_recommendations_empty_json_returns_empty_list(self):
        from app.services.ai_service import generate_recommendations
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()
        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._call_ai", return_value="invalid json"):
                result = asyncio.run(generate_recommendations(df, config, user))
        assert result == []


class TestGenerateNraInsights:
    """generate_nra_insights edge cases."""

    def test_nra_insights_http_exception_passthrough(self):
        from app.services.ai_service import generate_nra_insights
        from fastapi import HTTPException
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()
        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._call_ai",
                       side_effect=HTTPException(status_code=429)):
                with pytest.raises(HTTPException) as exc:
                    asyncio.run(generate_nra_insights(df, config, user))
        assert exc.value.status_code == 429

    def test_nra_insights_invalid_json_returns_empty_list(self):
        from app.services.ai_service import generate_nra_insights
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()
        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._call_ai", return_value="not json at all"):
                result = asyncio.run(generate_nra_insights(df, config, user))
        assert result == []


class TestGetUserProviderConfig:
    def test_no_key_returns_none(self):
        from unittest.mock import MagicMock
        from app.services.ai_service import get_user_api_key

        user = MagicMock()
        user.ai_provider = None
        user.encrypted_api_key = None
        user.api_key_iv = None

        provider, api_key, _ = get_user_api_key(user)
        assert provider is None
        assert api_key is None

    def test_openai_provider_with_key(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import get_user_api_key

        user = MagicMock()
        user.ai_provider = "openai"
        user.encrypted_api_key = "encrypted-key-value"
        user.api_key_iv = "test-iv"

        with patch("app.services.ai_service.decrypt_api_key", return_value="sk-proj-decrypted"):
            provider, api_key, base_url = get_user_api_key(user)

        assert provider == "openai"
        assert api_key == "sk-proj-decrypted"


class TestCallOpenai:
    def test_call_openai_delegates_to_compat(self):
        from unittest.mock import patch
        from app.services.ai_service import call_openai

        with patch("app.services.ai_service.call_openai_compat") as mock_compat:
            mock_compat.return_value = "openai response"
            result = call_openai("user prompt", "system prompt", "sk-test")
            assert result == "openai response"

    def test_call_openai_none_key(self):
        from unittest.mock import patch
        from app.services.ai_service import call_openai

        with patch("app.services.ai_service.call_openai_compat") as mock_compat:
            mock_compat.return_value = "ok"
            call_openai("test", "sys", None)
            args, kwargs = mock_compat.call_args
            assert args[2] is None


class TestSanitizeKwargs:
    def test_deepseek_strips_unsupported(self):
        from app.services.ai_service import _sanitize_kwargs, DEEPSEEK_UNSUPPORTED_PARAMS
        result = _sanitize_kwargs(
            base_url="https://api.deepseek.com",
            kwargs={"temperature": 0.7, "presence_penalty": 0.1, "n": 3},
        )
        assert "presence_penalty" not in result
        assert "n" not in result
        assert result["temperature"] == 0.7

    def test_deepseek_preserves_temperature(self):
        from app.services.ai_service import _sanitize_kwargs
        result = _sanitize_kwargs(
            base_url="https://api.deepseek.com",
            kwargs={"temperature": 0.7, "max_tokens": 1000},
        )
        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 1000

    def test_non_deepseek_passthrough(self):
        from app.services.ai_service import _sanitize_kwargs
        result = _sanitize_kwargs(
            base_url="https://api.openai.com",
            kwargs={"temperature": 0.7, "top_p": 0.9},
        )
        assert result == {"temperature": 0.7, "top_p": 0.9}


class TestRoundStats:
    def test_rounds_float_values(self):
        from app.services.ai_service import _round_stats
        stats = {"mean": 10.5678, "std": 3.14159}
        result = _round_stats(stats)
        assert result["mean"] == 10.57
        assert result["std"] == 3.14

    def test_rounds_nested_dict_values(self):
        from app.services.ai_service import _round_stats
        stats = {"stats": {"mean": 1.2345, "std": 0.5678}}
        result = _round_stats(stats)
        assert result["stats"]["mean"] == 1.23

    def test_passes_non_float_values(self):
        from app.services.ai_service import _round_stats
        stats = {"name": "test", "count": 100}
        result = _round_stats(stats)
        assert result["name"] == "test"
        assert result["count"] == 100

    def test_passes_none_values(self):
        from app.services.ai_service import _round_stats
        stats = {"mean": None}
        result = _round_stats(stats)
        assert result["mean"] is None


class TestValidateApiKeyOtherProviders:
    def test_gemini_always_valid(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key
        result = validate_api_key("gemini", "any-key")
        assert result["valid"] is True

    def test_claude_valid(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_claude", return_value="OK"):
            result = validate_api_key("claude", "sk-ant-valid-key")
        assert result["valid"] is True

    def test_openai_compat_valid(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat", return_value="OK"):
            result = validate_api_key("openai", "sk-proj-valid-key")
        assert result["valid"] is True

    def test_groq_valid(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat", return_value="OK"):
            result = validate_api_key("groq", "gsk-valid-key")
        assert result["valid"] is True

    def test_unknown_provider_rejected(self):
        from app.services.ai_service import validate_api_key
        result = validate_api_key("unknown-provider", "some-key")
        assert result["valid"] is False
        assert "unknown provider" in result["message"].lower()

    def test_claude_http_exception_400_treated_as_valid(self):
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_claude", side_effect=HTTPException(400, "Invalid key")):
            result = validate_api_key("claude", "sk-ant-valid-key")
        assert result["valid"] is True

    def test_generic_exception_401_treated_as_invalid(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat", side_effect=Exception("Unauthorized")):
            result = validate_api_key("openai", "sk-proj-bad-key")
        assert result["valid"] is False

    def test_generic_exception_unknown_treated_as_valid(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat", side_effect=Exception("Some weird error")):
            result = validate_api_key("openai", "sk-proj-weird-key")
        assert result["valid"] is True


class TestGenerateRecommendationsHappyPath:
    @pytest.mark.asyncio
    async def test_recommendations_success_path(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import generate_recommendations

        df = MagicMock()
        config = {}
        user = MagicMock()

        valid_json = (
            '["Increase revenue by optimizing pricing strategy", '
            '"Reduce operational costs through automation", '
            '"Launch a customer loyalty program to boost retention", '
            '"Optimize supply chain to reduce delivery times", '
            '"Implement AI-driven customer support for faster resolution"]'
        )

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value={"columns": []}):
                with patch("app.services.ai_service._call_ai", return_value=valid_json):
                    result = await generate_recommendations(df, config, user)

        assert len(result) == 5
        assert all(isinstance(r, str) for r in result)

    @pytest.mark.asyncio
    async def test_recommendations_with_json_markdown_fence(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import generate_recommendations

        df = MagicMock()
        config = {}
        user = MagicMock()

        response_with_fence = (
            '```json\n'
            '["Increase revenue by optimizing pricing", '
            '"Reduce operational costs through automation"]\n'
            '```'
        )

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value={"columns": []}):
                with patch("app.services.ai_service._call_ai", return_value=response_with_fence):
                    result = await generate_recommendations(df, config, user)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_recommendations_non_list_json(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import generate_recommendations

        df = MagicMock()
        config = {}
        user = MagicMock()

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value={"columns": []}):
                with patch("app.services.ai_service._call_ai", return_value='{"key": "value"}'):
                    result = await generate_recommendations(df, config, user)

        assert result == []


class TestGenerateNraInsightsHappyPath:
    @pytest.mark.asyncio
    async def test_nra_insights_success_path(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import generate_nra_insights

        df = MagicMock()
        config = {}
        user = MagicMock()

        valid_insights = json.dumps([
            {"kpi": "Revenue", "column": "Revenue", "number": "$1.5M",
             "reason": "Seasonal demand increase", "action": "Increase inventory",
             "sentiment": "positive", "priority": "high"},
            {"kpi": "Cost", "column": "Cost", "number": "15%",
             "reason": "Supplier price hike", "action": "Negotiate new contracts",
             "sentiment": "negative", "priority": "medium"},
        ])

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value={"columns": []}):
                with patch("app.services.ai_service._call_ai", return_value=valid_insights):
                    with patch("app.services.ai_service._dedup_insights_by_kpi",
                               side_effect=lambda x: x):
                        result = await generate_nra_insights(df, config, user)

        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)
        assert all(item["kpi"] in ("Revenue", "Cost") for item in result)

    @pytest.mark.asyncio
    async def test_nra_insights_validates_insight_keys(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import generate_nra_insights

        df = MagicMock()
        config = {}
        user = MagicMock()

        missing_keys = json.dumps([
            {"kpi": "Revenue", "number": "$1.5M",
             "reason": "Seasonal demand", "action": "Increase inventory",
             "sentiment": "positive", "priority": "high"},
            {"kpi": "Cost", "column": "Cost",
             "sentiment": "negative", "priority": "low"},
        ])

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value={"columns": []}):
                with patch("app.services.ai_service._call_ai", return_value=missing_keys):
                    with patch("app.services.ai_service._dedup_insights_by_kpi",
                               side_effect=lambda x: x):
                        result = await generate_nra_insights(df, config, user)

        assert len(result) == 1
        assert result[0]["kpi"] == "Revenue"

    @pytest.mark.asyncio
    async def test_nra_insights_truncates_to_five(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import generate_nra_insights

        df = MagicMock()
        config = {}
        user = MagicMock()

        many_insights = json.dumps([
            {"kpi": f"Metric{i}", "column": f"Col{i}", "number": f"{i}%",
             "reason": f"Reason {i}", "action": f"Action {i}",
             "sentiment": "neutral", "priority": "low"}
            for i in range(10)
        ])

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value={"columns": []}):
                with patch("app.services.ai_service._call_ai", return_value=many_insights):
                    with patch("app.services.ai_service._dedup_insights_by_kpi",
                               side_effect=lambda x: x):
                        result = await generate_nra_insights(df, config, user)

        assert len(result) <= 5


class TestCallOpenaiReturnsEmpty:
    """call_openai returns "" when call_openai_compat returns None."""

    def test_call_openai_returns_empty_when_compat_returns_none(self):
        from unittest.mock import patch
        from app.services.ai_service import call_openai

        with patch("app.services.ai_service.call_openai_compat", return_value=None):
            result = call_openai("prompt", "system", "key")
        assert result == ""


class TestCallOpenaiCompatResultNone:
    """call_openai_compat returns None when API response content is None."""

    def test_openai_compat_result_none_after_finally(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import call_openai_compat

        mock_msg = MagicMock()
        mock_msg.content = None
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        with patch("app.services.ai_service.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_resp
            result = call_openai_compat("prompt", "system", "key")
        assert result is None

    def test_openai_compat_del_client_exception_swallowed(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import call_openai_compat

        mock_msg = MagicMock()
        mock_msg.content = "text"
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        class ClientWithFailingDel:
            def __init__(self):
                self.chat = MagicMock()
                self.chat.completions = MagicMock()
                self.chat.completions.create = MagicMock(return_value=mock_resp)
            def __del__(self):
                raise RuntimeError("del failed")

        with patch("app.services.ai_service.OpenAI", return_value=ClientWithFailingDel()):
            result = call_openai_compat("prompt", "system", "key")
        assert result == "text"


class TestValidateApiKeyHttpExceptionDetail:
    """validate_api_key exception detail parsing."""

    def test_http_exception_invalid_api_key_detail(self):
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat",
                   side_effect=HTTPException(400, detail="Invalid API key")):
            result = validate_api_key("openai", "sk-test")
        assert result["valid"] is False
        assert "Invalid API key" in result["message"]

    def test_http_exception_400_detail_returns_valid_with_warning(self):
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat",
                   side_effect=HTTPException(400, detail="400 Bad Request")):
            result = validate_api_key("openai", "sk-test")
        assert result["valid"] is True
        assert "400" in result["message"]

    def test_http_exception_unauthorized_detail(self):
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat",
                   side_effect=HTTPException(401, detail="Unauthorized")):
            result = validate_api_key("openai", "sk-test")
        assert result["valid"] is False
        assert "Invalid API key" in result["message"]

    def test_value_error_401(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat",
                   side_effect=ValueError("401 Unauthorized")):
            result = validate_api_key("openai", "sk-test")
        assert result["valid"] is False
        assert "Invalid API key" in result["message"]

    def test_value_error_other(self):
        from unittest.mock import patch
        from app.services.ai_service import validate_api_key

        with patch("app.services.ai_service.call_openai_compat",
                   side_effect=ValueError("Other error")):
            result = validate_api_key("openai", "sk-test")
        assert result["valid"] is True


class TestCallClaudeEmptyResult:
    """call_claude raises HTTPException 500 when result content is falsy."""

    def test_claude_empty_content_raises_500(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import call_claude
        from fastapi import HTTPException

        mock_content_block = MagicMock()
        mock_content_block.text = ""
        mock_response = MagicMock()
        mock_response.content = [mock_content_block]

        with patch("app.services.ai_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response
            with pytest.raises(HTTPException) as exc:
                call_claude("prompt", "system", "key")
        assert exc.value.status_code == 500


class TestCallGemini403:
    """call_gemini raises HTTP 400 for 403 or 401 status."""

    def test_gemini_403_raises_400(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import call_gemini
        from fastapi import HTTPException

        resp = MagicMock()
        resp.status_code = 403

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with pytest.raises(HTTPException) as exc:
                call_gemini("prompt", "system", "key")
        assert exc.value.status_code == 400

    def test_gemini_401_raises_400(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import call_gemini
        from fastapi import HTTPException

        resp = MagicMock()
        resp.status_code = 401

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with pytest.raises(HTTPException) as exc:
                call_gemini("prompt", "system", "key")
        assert exc.value.status_code == 400


class TestCallGeminiEmptyResult:
    """call_gemini raises HTTP 500 when content parts are empty."""

    def test_gemini_empty_text_raises_500(self):
        from unittest.mock import patch, MagicMock
        from app.services.ai_service import call_gemini
        from fastapi import HTTPException

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": ""}]},
                "finishReason": "STOP",
            }]
        }

        with patch("app.services.ai_service.requests.post", return_value=resp):
            with pytest.raises(HTTPException) as exc:
                call_gemini("prompt", "system", "key")
        assert exc.value.status_code == 500


class TestCallAiFallbackNone:
    """_call_ai with unknown provider falls through to call_openai returning "" when result is None."""

    def test_call_ai_unknown_provider_returns_empty(self):
        from unittest.mock import patch
        from app.services import ai_service as ai_service_mod

        with patch.object(ai_service_mod, "call_openai", return_value=None) as mock_openai:
            with patch.object(ai_service_mod, "call_openai_compat") as mock_compat:
                result = ai_service_mod._call_ai("unknown", "p", "s", "k")
        assert result == ""
        mock_openai.assert_called_once_with("p", "s", "k", 25)
        mock_compat.assert_not_called()


class TestFmtVal:
    """_fmt_val nested function formatting of different value types."""

    def test_fmt_val_formats_correctly(self):
        from app.services.ai_service import generate_summary
        from unittest.mock import MagicMock, patch
        import pandas as pd
        import asyncio

        df = pd.DataFrame({"dummy": [1, 2, 3]})
        config = {}
        user = MagicMock()

        captured_prompt = [None]

        def mock_call_ai(provider, prompt, system, api_key, timeout=25):
            captured_prompt[0] = prompt
            return "[LEAD]t[/LEAD][CONTEXT]t[/CONTEXT][IMPLICATION]t[/IMPLICATION][ACTION]t[/ACTION]"

        col_stats = {
            "columns": [
                {"name": "TestCol", "type": "metric",
                 "mean": None, "latest_value": float(5.0),
                 "trend_pct_change": float(0.0),
                 "min": 1, "max": 10, "null_count": 0, "row_count": 3},
                {"name": "IntFloat", "type": "metric",
                 "mean": float(5.0), "latest_value": float(10.0),
                 "trend_pct_change": float(100.0),
                 "min": 1, "max": 10, "null_count": 0, "row_count": 3},
                {"name": "FloatCol", "type": "metric",
                 "mean": float(2.5), "latest_value": float(3.5),
                 "trend_pct_change": float(40.0),
                 "min": 1, "max": 10, "null_count": 0, "row_count": 3},
            ],
            "date_column": None,
            "date_range": {"from": "Jan", "to": "Mar"},
        }

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value=col_stats):
                with patch("app.services.ai_service._call_ai", side_effect=mock_call_ai):
                    asyncio.run(generate_summary(df, config, user))

        prompt = captured_prompt[0]
        assert "mean=N/A" in prompt
        assert "IntFloat: mean=5, latest=10" in prompt
        assert "FloatCol: mean=2.50, latest=3.50" in prompt


class TestGenerateRecommendationsHttpException:
    """generate_recommendations returns [] when get_user_api_key raises HTTPException."""

    def test_recommendations_http_exception_returns_empty(self):
        from app.services.ai_service import generate_recommendations
        from fastapi import HTTPException
        from unittest.mock import MagicMock, patch
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()

        with patch("app.services.ai_service.get_user_api_key",
                   side_effect=HTTPException(status_code=400)):
            result = asyncio.run(generate_recommendations(df, config, user))
        assert result == []


class TestGenerateNraInsightsHttpException:
    """generate_nra_insights returns [] when get_user_api_key raises HTTPException."""

    def test_nra_insights_http_exception_returns_empty(self):
        from app.services.ai_service import generate_nra_insights
        from fastapi import HTTPException
        from unittest.mock import MagicMock, patch
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()

        with patch("app.services.ai_service.get_user_api_key",
                   side_effect=HTTPException(status_code=400)):
            result = asyncio.run(generate_nra_insights(df, config, user))
        assert result == []


class TestGenerateNraInsightsApiKeyNone:
    """generate_nra_insights returns [] when api_key is None."""

    def test_nra_insights_api_key_none_returns_empty(self):
        from app.services.ai_service import generate_nra_insights
        from unittest.mock import MagicMock, patch
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()

        with patch("app.services.ai_service.get_user_api_key", return_value=(None, None, None)):
            result = asyncio.run(generate_nra_insights(df, config, user))
        assert result == []


class TestGenerateNraInsightsNonList:
    """generate_nra_insights returns [] when parsed JSON is not a list."""

    def test_nra_insights_non_list_json_returns_empty(self):
        from app.services.ai_service import generate_nra_insights
        from unittest.mock import MagicMock, patch
        import asyncio

        df = MagicMock()
        config = {}
        user = MagicMock()

        with patch("app.services.ai_service.get_user_api_key", return_value=("openai", "sk-test", None)):
            with patch("app.services.ai_service._build_column_stats", return_value={"columns": []}):
                with patch("app.services.ai_service._call_ai", return_value='{"key": "value"}'):
                    result = asyncio.run(generate_nra_insights(df, config, user))
        assert result == []


class TestDetectAnomaliesStdZero:
    """detect_anomalies skips column with std == 0."""

    def test_detect_anomalies_std_zero_skipped(self):
        from app.services.ai_service import detect_anomalies
        import pandas as pd

        df = pd.DataFrame({
            "Constant": [5, 5, 5, 5, 5],
            "Values": [10, 12, 11, 100, 13],
        })
        result = detect_anomalies(df)
        for anomaly in result:
            assert anomaly["column"] != "Constant"


class TestDetectAnomaliesValueError:
    """detect_anomalies handles ValueError in val_key conversion."""

    def test_detect_anomalies_value_error_handled(self):
        from app.services import ai_service as ai_service_mod
        from app.services.ai_service import detect_anomalies
        import pandas as pd

        df = pd.DataFrame({
            "Values": [10, 12, 11, 13, 10, 100, 12, 11, 13, 12],
        })

        original_round = round
        def mock_round(x, ndigits=0):
            if ndigits == 4:
                raise ValueError("bad")
            return original_round(x, ndigits)

        with patch.object(ai_service_mod, "round", mock_round, create=True):
            result = detect_anomalies(df)
        assert isinstance(result, list)


class TestDetectTrendsZeroFirstValue:
    """detect_trends returns pct_change 0.0 when first_value is 0."""

    def test_detect_trends_zero_first_value(self):
        from app.services.ai_service import detect_trends
        import pandas as pd

        df = pd.DataFrame({
            "Revenue": [0, 100, 200, 300],
        })
        result = detect_trends(df)
        assert result[0]["pct_change"] == 0.0
