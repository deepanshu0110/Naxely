import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image


class TestChartService:
    def test_generate_sync_returns_png_paths(self):
        from app.services.chart_service import generate_sync, cleanup_charts

        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=20, freq="D"),
            "Revenue": np.random.randint(1000, 5000, 20),
            "Clicks": np.random.randint(100, 500, 20),
            "Conversions": np.random.randint(10, 50, 20),
            "Region": ["North", "South"] * 10,
        })
        config = {"metric_columns": ["Revenue", "Clicks", "Conversions"]}
        report_id = "test-chart-smoke"
        paths = generate_sync(df, report_id, config)

        assert len(paths) > 0
        for p, col_name in paths:
            assert Path(p).exists()
            img = Image.open(p)
            assert img.width > 0
            assert img.height > 0
            assert isinstance(col_name, str)

        cleanup_charts(report_id)

    def test_generate_with_date_column(self):
        from app.services.chart_service import generate_sync, cleanup_charts

        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=15, freq="D"),
            "Revenue": np.random.randint(1000, 5000, 15),
        })
        config = {"metric_columns": ["Revenue"], "date_column": "Date"}
        report_id = "test-date-chart"
        paths = generate_sync(df, report_id, config)
        assert len(paths) == 1
        p, col_name = paths[0]
        assert Path(p).exists()
        assert col_name == "Revenue"
        cleanup_charts(report_id)

    def test_select_chart_type_pie(self):
        from app.services.chart_service import select_chart_type
        df = pd.DataFrame({
            "Category": ["A", "B", "C"],
            "Share": [50.0, 30.0, 20.0],
        })
        # New logic: no date, no dimension_columns passed -> histogram
        result = select_chart_type(df, "Share", None, None)
        assert result == "histogram"

    def test_select_chart_type_bar(self):
        from app.services.chart_service import select_chart_type
        df = pd.DataFrame({
            "Category": ["X", "Y", "Z"],
            "Count": [10, 20, 30],
        })
        # New logic: dimension column present -> bar
        result = select_chart_type(df, "Count", None, ["Category"])
        assert result == "bar"

    def test_select_chart_type_histogram(self):
        from app.services.chart_service import select_chart_type
        df = pd.DataFrame({
            "Values": np.random.normal(50, 10, 100),
        })
        result = select_chart_type(df, "Values")
        assert result in ("histogram", "bar")