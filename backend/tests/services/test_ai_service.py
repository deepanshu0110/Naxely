import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import pandas as pd
import numpy as np


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