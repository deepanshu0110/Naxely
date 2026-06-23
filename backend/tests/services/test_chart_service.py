import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image

import app.services.chart_service as chart_service


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

    def test_select_chart_type_line(self):
        from app.services.chart_service import select_chart_type
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=5),
            "Revenue": [100, 200, 300, 400, 500],
        })
        result = select_chart_type("Date", "Revenue", df)
        assert result == "line"

    def test_select_chart_type_bar(self):
        from app.services.chart_service import select_chart_type
        df = pd.DataFrame({
            "Category": ["X", "Y", "Z"],
            "Count": [10, 20, 30],
        })
        result = select_chart_type("Category", "Count", df)
        assert result == "bar"

    def test_select_chart_type_scatter(self):
        from app.services.chart_service import select_chart_type
        df = pd.DataFrame({
            "Height": [150, 160, 170, 180, 190],
            "Weight": [50, 60, 70, 80, 90],
        })
        result = select_chart_type("Height", "Weight", df)
        assert result == "scatter"

    def test_date_column_produces_line_chart(self):
        """Date + numeric → line chart, not histogram or bar"""
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=10),
            "Revenue": [100, 200, 150, 300, 250, 400, 350, 500, 450, 600]
        })
        config = {"date_column": "Date", "metric_columns": ["Revenue"]}
        paths = chart_service.generate_sync(df, "test-line", config, "#0D7377")
        assert len(paths) >= 1
        assert any("line" in p[0] for p in paths), "Expected line chart for date+numeric"
        chart_service.cleanup_charts("test-line")

    def test_categorical_produces_bar_chart(self):
        """Categorical + numeric → horizontal bar chart"""
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=8),
            "Region": ["North","South","East","West","North","South","East","West"],
            "Revenue": [1000, 2000, 1500, 3000, 1100, 2100, 1600, 3100]
        })
        config = {"date_column": "Date", "metric_columns": ["Revenue"]}
        paths = chart_service.generate_sync(df, "test-bar", config, "#0D7377")
        assert len(paths) >= 1
        assert any("bar" in p[0] for p in paths), "Expected bar chart for categorical+numeric"
        chart_service.cleanup_charts("test-bar")

    def test_max_three_charts_regardless_of_columns(self):
        """Never generates more than 3 charts even with many columns"""
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=10),
            "Region": ["North","South"]*5,
            "Service": ["Audit","Training"]*5,
            "Revenue": range(1000, 11000, 1000),
            "Hours": range(5, 15),
            "Cost": range(200, 1200, 100),
        })
        config = {"date_column": "Date", "metric_columns": ["Revenue", "Hours", "Cost"]}
        paths = chart_service.generate_sync(df, "test-max", config, "#0D7377")
        assert len(paths) <= 3, f"Expected max 3 charts, got {len(paths)}"
        chart_service.cleanup_charts("test-max")

    def test_brand_color_is_used(self):
        """brand_color_hex is passed and used — chart file is generated"""
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=5),
            "Revenue": [100, 200, 300, 400, 500]
        })
        config = {"date_column": "Date", "metric_columns": ["Revenue"]}
        paths = chart_service.generate_sync(df, "test-color", config, "#FF0000")
        assert len(paths) >= 1
        assert os.path.isfile(paths[0][0])
        chart_service.cleanup_charts("test-color")

    def test_all_chart_paths_are_valid_files(self):
        """Every returned path must point to a real PNG file"""
        df = pd.DataFrame({
            "Date": pd.date_range("2025-11-01", periods=30),
            "Region": ["North","South","East","West","West"]*6,
            "Service": ["Training","Audit","Consulting","Dashboard Build","Audit"]*6,
            "Hours Billed": [10]*30,
            "Revenue": [3000 + i*50 for i in range(30)]
        })
        config = {"date_column": "Date", "metric_columns": ["Revenue", "Hours Billed"]}
        paths = chart_service.generate_sync(df, "test-valid", config, "#0D7377")
        for path, metric in paths:
            assert os.path.isfile(path), f"Chart file missing: {path}"
            assert path.endswith(".png"), f"Expected PNG, got: {path}"
        chart_service.cleanup_charts("test-valid")