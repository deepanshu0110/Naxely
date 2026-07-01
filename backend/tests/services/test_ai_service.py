import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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