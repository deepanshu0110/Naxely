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