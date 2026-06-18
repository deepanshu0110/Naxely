import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from app.services.chart_service import generate_sync, cleanup_charts


class TestPdfService:
    def test_build_sync_creates_pdf(self):
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "Revenue": [1000, 1200, 1100, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
            "Clicks": [100, 110, 105, 120, 130, 125, 140, 150, 145, 160],
        })
        config = {
            "metric_columns": ["Revenue", "Clicks"],
            "title": "Test Report",
            "sections": ["key_metrics", "charts", "data_table"],
        }
        chart_config = {"metric_columns": ["Revenue", "Clicks"]}
        report_id = "test-pdf-smoke"

        chart_paths = generate_sync(df, report_id, chart_config)

        ai_content = {
            "summary": None,
            "insights": [],
            "anomalies": [],
            "trends": [{"column": "Revenue", "trend": "increasing", "pct_change": 90.0}],
        }
        user_data = {
            "brand_color": "#6366F1",
            "tier": "pro",
            "logo_url": None,
            "company_name": "Test Corp",
        }
        pdf_config = dict(config)
        pdf_config["report_id"] = report_id

        pdf_path = build_sync(df, chart_paths, ai_content, pdf_config, user_data)
        assert pdf_path is not None
        assert Path(pdf_path).exists()
        assert os.path.getsize(pdf_path) > 1000

        cleanup_charts(report_id)
        try:
            os.unlink(pdf_path)
        except OSError:
            pass

    def test_build_sync_free_tier(self):
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Metric": [10, 20, 30],
            "Value": [100, 200, 300],
        })
        config = {
            "metric_columns": ["Value"],
            "title": "Free Tier Test",
            "sections": ["key_metrics"],
            "report_id": "test-pdf-free",
        }
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {
            "brand_color": "#6366F1",
            "tier": "free",
            "logo_url": None,
            "company_name": None,
        }
        pdf_path = build_sync(df, [], ai_content, config, user_data)
        assert Path(pdf_path).exists()
        assert os.path.getsize(pdf_path) > 500

        try:
            os.unlink(pdf_path)
        except OSError:
            pass

    def test_build_sync_white_label_footer(self):
        """Agency-tier PDF footer must NOT contain 'Databrief'; Pro-tier must still contain it."""
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Metric": [10, 20, 30],
            "Value": [100, 200, 300],
        })
        base_config = {
            "metric_columns": ["Value"],
            "title": "White Label Test",
            "sections": ["key_metrics"],
        }
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}

        # Agency tier with company name — footer should say company name, not Databrief
        wl_config = dict(base_config)
        wl_config["report_id"] = "test-pdf-wl"
        wl_user_data = {
            "brand_color": "#6366F1",
            "tier": "agency",
            "logo_url": None,
            "company_name": "AgencyCo",
        }
        wl_path = build_sync(df, [], ai_content, wl_config, wl_user_data)
        wl_doc = fitz.open(wl_path)
        wl_text = ""
        for page in wl_doc:
            wl_text += page.get_text()
        wl_doc.close()
        assert 'Databrief' not in wl_text, "White-label PDF should not contain 'Databrief' in footer"
        assert 'AgencyCo' in wl_text, "White-label PDF should contain company name in footer"
        try:
            os.unlink(wl_path)
        except OSError:
            pass

        # Pro tier — footer must still contain Databrief
        pro_config = dict(base_config)
        pro_config["report_id"] = "test-pdf-pro-footer"
        pro_user_data = {
            "brand_color": "#6366F1",
            "tier": "pro",
            "logo_url": None,
            "company_name": "TestCo",
        }
        pro_path = build_sync(df, [], ai_content, pro_config, pro_user_data)
        pro_doc = fitz.open(pro_path)
        pro_text = ""
        for page in pro_doc:
            pro_text += page.get_text()
        pro_doc.close()
        assert 'Databrief' in pro_text, "Pro-tier PDF should contain 'Databrief' in footer"
        try:
            os.unlink(pro_path)
        except OSError:
            pass

        # Free tier — footer must also contain Databrief
        free_config = dict(base_config)
        free_config["report_id"] = "test-pdf-free-footer"
        free_user_data = {
            "brand_color": "#6366F1",
            "tier": "free",
            "logo_url": None,
            "company_name": None,
        }
        free_path = build_sync(df, [], ai_content, free_config, free_user_data)
        free_doc = fitz.open(free_path)
        free_text = ""
        for page in free_doc:
            free_text += page.get_text()
        free_doc.close()
        assert 'Databrief' in free_text, "Free-tier PDF should contain 'Databrief' in footer"
        try:
            os.unlink(free_path)
        except OSError:
            pass


class TestKpiTrendDeterminism:
    def test_trend_is_deterministic_across_calls(self):
        from app.services.pdf_service import _compute_kpi_data

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300, 5400, 5500, 5600, 5700, 5800, 5900],
            "Units Sold": [300, 290, 285, 280, 275, 270, 265, 260, 255, 250],
            "Clicks": [1000, 1020, 980, 1010, 990, 1005, 1015, 995, 1005, 1010],
        })
        config = {"metric_columns": ["Revenue", "Units Sold", "Clicks"]}
        ai_content = {"insights": [], "summary": None, "anomalies": [], "trends": []}

        result1 = _compute_kpi_data(df, config, ai_content, "#6366F1")
        result2 = _compute_kpi_data(df, config, ai_content, "#6366F1")

        for kpi1, kpi2 in zip(result1, result2):
            assert kpi1["name"] == kpi2["name"]
            assert kpi1["trend"] == kpi2["trend"], (
                f"Trend mismatch for {kpi1['name']}: "
                f"run1={kpi1['trend']} run2={kpi2['trend']} — "
                f"must be deterministic"
            )