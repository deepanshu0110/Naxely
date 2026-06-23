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

    # ── Shared fixtures ──────────────────────────────────────────────────

    @staticmethod
    def _full_df():
        """Matches naxely_scheduled_report_test.csv structure"""
        return pd.DataFrame({
            "Date": pd.date_range("2025-11-01", periods=20),
            "Region": ["North","South","East","West","West"]*4,
            "Service": ["Training","Audit","Consulting","Dashboard Build","Audit"]*4,
            "Hours Billed": [5 + i % 14 for i in range(20)],
            "Revenue": [2000 + i*150 for i in range(20)],
        })

    @staticmethod
    def _config():
        return {"date_column": "Date", "metric_columns": ["Revenue", "Hours Billed"]}

    # ── Chart type selection ─────────────────────────────────────────────

    def test_select_chart_type_line_new(self):
        df = self._full_df()
        df["Date"] = pd.to_datetime(df["Date"])
        assert chart_service.select_chart_type("Date", "Revenue", df) == "line"

    def test_select_chart_type_bar_new(self):
        df = self._full_df()
        assert chart_service.select_chart_type("Region", "Revenue", df) == "bar"

    def test_select_chart_type_scatter_new(self):
        df = self._full_df()
        assert chart_service.select_chart_type("Hours Billed", "Revenue", df) == "scatter"

    def test_select_chart_type_histogram_new(self):
        df = pd.DataFrame({"Revenue": [1000,2000,3000,1500,2500,3500]})
        assert chart_service.select_chart_type("Revenue", "Revenue", df) == "histogram"

    # ── New chart types ──────────────────────────────────────────────────

    def test_area_chart_renders(self):
        df = self._full_df()
        df["Date"] = pd.to_datetime(df["Date"])
        path = chart_service._generate_single_chart(
            df, "Date", "Revenue", "area", "test-area", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-area")

    def test_donut_chart_renders(self):
        df = self._full_df()
        path = chart_service._generate_single_chart(
            df, "Region", "Revenue", "donut", "test-donut", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-donut")

    def test_lollipop_chart_renders(self):
        df = self._full_df()
        path = chart_service._generate_single_chart(
            df, "Service", "Revenue", "lollipop", "test-lollipop", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-lollipop")

    def test_box_chart_renders(self):
        df = self._full_df()
        path = chart_service._generate_single_chart(
            df, "Region", "Revenue", "box", "test-box", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-box")

    def test_heatmap_chart_renders(self):
        df = self._full_df()
        path = chart_service._generate_single_chart(
            df, "Region", "Service", "heatmap", "test-heatmap", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-heatmap")

    def test_grouped_bar_chart_renders(self):
        df = self._full_df()
        path = chart_service._generate_single_chart(
            df, "Region", "Revenue", "grouped_bar", "test-gbar", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-gbar")

    def test_stacked_bar_chart_renders(self):
        df = self._full_df()
        path = chart_service._generate_single_chart(
            df, "Region", "Revenue", "stacked_bar", "test-sbar", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-sbar")

    def test_combo_chart_renders(self):
        df = self._full_df()
        df["Date"] = pd.to_datetime(df["Date"])
        path = chart_service._generate_single_chart(
            df, "Date", "Revenue", "combo", "test-combo", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-combo")

    def test_waterfall_chart_renders(self):
        df = pd.DataFrame({
            "Stage": ["Q1","Q2","Q3","Q4","Total"],
            "Revenue": [1000.0, 500.0, -200.0, 800.0, 2100.0]
        })
        path = chart_service._generate_single_chart(
            df, "Stage", "Revenue", "waterfall", "test-waterfall", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-waterfall")

    def test_funnel_chart_renders(self):
        df = pd.DataFrame({
            "Stage": ["Leads","Qualified","Proposal","Closed"],
            "Count": [1000.0, 600.0, 200.0, 80.0]
        })
        path = chart_service._generate_single_chart(
            df, "Stage", "Count", "funnel", "test-funnel", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-funnel")

    def test_bullet_chart_renders(self):
        df = pd.DataFrame({
            "Metric": ["Revenue"],
            "Value": [75000.0],
            "Target": [100000.0]
        })
        path = chart_service._generate_single_chart(
            df, "Metric", "Value", "bullet", "test-bullet", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-bullet")

    def test_treemap_chart_renders(self):
        df = pd.DataFrame({
            "Service": ["Training","Audit","Consulting","Dashboard Build"],
            "Revenue": [50000.0, 30000.0, 45000.0, 20000.0]
        })
        path = chart_service._generate_single_chart(
            df, "Service", "Revenue", "treemap", "test-treemap", "#0D7377"
        )
        assert path is not None and os.path.isfile(path)
        chart_service.cleanup_charts("test-treemap")

    # ── AI spec passthrough ──────────────────────────────────────────────

    def test_generate_sync_accepts_chart_specs(self):
        """When chart_specs passed in, use them instead of auto-selecting"""
        df = self._full_df()
        df["Date"] = pd.to_datetime(df["Date"])
        specs = [
            {"x": "Date", "y": "Revenue", "type": "line", "title": "Revenue Over Time"},
            {"x": "Region", "y": "Revenue", "type": "bar", "title": "Revenue by Region"},
        ]
        paths = chart_service.generate_sync(
            df, "test-specs", self._config(), "#0D7377", chart_specs=specs
        )
        assert len(paths) == 2
        assert any("line" in p[0] for p in paths)
        assert any("bar" in p[0] for p in paths)
        chart_service.cleanup_charts("test-specs")

    def test_generate_sync_falls_back_without_specs(self):
        """No chart_specs → rule-based selection still works"""
        df = self._full_df()
        df["Date"] = pd.to_datetime(df["Date"])
        paths = chart_service.generate_sync(df, "test-fallback", self._config(), "#0D7377")
        assert 1 <= len(paths) <= 3
        for path, metric in paths:
            assert os.path.isfile(path)
        chart_service.cleanup_charts("test-fallback")

    def test_max_three_charts_enforced(self):
        df = self._full_df()
        df["Date"] = pd.to_datetime(df["Date"])
        paths = chart_service.generate_sync(df, "test-max3", self._config(), "#0D7377")
        assert len(paths) <= 3
        chart_service.cleanup_charts("test-max3")