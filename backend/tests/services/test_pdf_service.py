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
        """Agency-tier PDF footer must NOT contain 'Naxely'; Pro-tier must still contain it."""
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

        # Agency tier with company name — footer should say company name, not Naxely
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
        assert 'Naxely' not in wl_text, "White-label PDF should not contain 'Naxely' in footer"
        assert 'AgencyCo' in wl_text, "White-label PDF should contain company name in footer"
        try:
            os.unlink(wl_path)
        except OSError:
            pass

        # Pro tier — footer must still contain Naxely
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
        assert 'Naxely' in pro_text, "Pro-tier PDF should contain 'Naxely' in footer"
        try:
            os.unlink(pro_path)
        except OSError:
            pass

        # Free tier — footer must also contain Naxely
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
        assert 'Naxely' in free_text, "Free-tier PDF should contain 'Naxely' in footer"
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


class TestKpiCardArrowDirection:
    """Arrow drawn on KPI cards must derive direction/color from trend_pct, not trend field."""

    def _extract_trend_text(self, pdf_path: str) -> list[str]:
        """Extract all text fragments containing trend markers from rendered PDF."""
        import fitz
        texts = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                texts.extend(page.get_text().split('\n'))
        return [t.strip() for t in texts if '% recent' in t]

    def test_negative_trend_pct_produces_down_arrow(self):
        import tempfile
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.lib.pagesizes import A4
        from app.services.pdf_service import _KPIRow

        tmp = tempfile.mktemp(suffix='.pdf')
        try:
            doc = SimpleDocTemplate(tmp, pagesize=A4)
            card = _KPIRow(
                [{"name": "Units Sold", "value": "1,500", "trend": "increasing", "trend_pct": -35.7}],
                400, "#D97A34",
            )
            doc.build([card])

            trends = self._extract_trend_text(tmp)
            assert any('-' in t for t in trends), (
                f"Expected minus sign for negative trend_pct, found: {trends}"
            )
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def test_positive_trend_pct_produces_up_arrow(self):
        import tempfile
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.lib.pagesizes import A4
        from app.services.pdf_service import _KPIRow

        tmp = tempfile.mktemp(suffix='.pdf')
        try:
            doc = SimpleDocTemplate(tmp, pagesize=A4)
            card = _KPIRow(
                [{"name": "Revenue", "value": "$50K", "trend": "increasing", "trend_pct": 12.5}],
                400, "#D97A34",
            )
            doc.build([card])

            trends = self._extract_trend_text(tmp)
            assert any('+' in t for t in trends), (
                f"Expected plus sign for positive trend_pct, found: {trends}"
            )
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def test_full_pipeline_trend_pct_sign_matches_label(self):
        """End-to-end: build_sync with known data must produce trend_pct labels
        whose sign matches the arrow direction in the rendered PDF."""
        import tempfile, fitz
        from app.services.pdf_service import build_sync, _compute_kpi_data
        from app.services.chart_service import generate_sync, cleanup_charts

        # Revenue: clearly decreasing series
        df = pd.DataFrame({
            "Revenue": [5000, 4800, 4600, 4400, 4200],
            "Profit": [100, 300, 500, 700, 900],
        })
        config = {
            "metric_columns": ["Revenue", "Profit"],
            "title": "Arrow Test",
            "sections": ["key_metrics"],
            "report_id": "test-arrow-pipeline",
        }
        chart_config = {"metric_columns": []}
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}

        kpis = _compute_kpi_data(df, config, ai_content, "#D97A34")
        rev_kpi = next(k for k in kpis if "Revenue" in k["name"])
        profit_kpi = next(k for k in kpis if "Profit" in k["name"])
        assert rev_kpi["trend_pct"] < 0, f"Revenue trend_pct should be negative, got {rev_kpi['trend_pct']}"
        assert profit_kpi["trend_pct"] >= 0, f"Profit trend_pct should be >=0, got {profit_kpi['trend_pct']}"

        pdf_path = build_sync(
            df, [], ai_content,
            {**config, "metric_columns": ["Revenue", "Profit"]},
            {"brand_color": "#D97A34", "tier": "pro", "logo_url": None, "company_name": "Test"},
        )
        try:
            trends = self._extract_trend_text(pdf_path)
            assert any('-' in t for t in trends), f"Expected '-' for negative trend, got {trends}"
            assert any('+' in t for t in trends), f"Expected '+' for positive trend, got {trends}"
        finally:
            try:
                os.unlink(pdf_path)
            except OSError:
                pass
            try:
                cleanup_charts("test-arrow-pipeline")
            except Exception:
                pass


class TestKpiCurrencyCleanPath:
    """Regression: _compute_kpi_data's fallback path must handle currency-formatted strings,
    and both the normalization-first and direct-fallback paths must agree."""

    def test_fallback_handles_currency_strings(self):
        """_compute_kpi_data without _precomputed_kpis must correctly sum
        currency-formatted Revenue values, not silently drop them."""
        from app.services.pdf_service import _compute_kpi_data

        df = pd.DataFrame({
            "Revenue": ["$9,770.44", "$666.80", "5000", "$1,234.56", "3000"],
            "Units Sold": [100, 200, 150, 175, 125],
        })
        config = {"metric_columns": ["Revenue", "Units Sold"]}
        ai_content = {"insights": [], "summary": None, "anomalies": [], "trends": []}

        kpis = _compute_kpi_data(df, config, ai_content, "#6366F1")
        rev_kpi = next(k for k in kpis if "Revenue" in k["name"])

        total = 9770.44 + 666.80 + 5000 + 1234.56 + 3000
        assert rev_kpi["value"] == "19.7K", (
            f"Expected '19.7K' (${total:,.2f}), got '{rev_kpi['value']}'"
        )

    def test_messy_csv_revenue_kpi_440772(self):
        """Full pipeline regression: edge_case_messy_formatting.csv Revenue
        sum 440,772.96 → KPI tile reads '440.8K' (short-hand format).
        This value must not drift after any refactor."""
        import os
        from app.services.data_service import parse_csv, normalize_for_aggregation, detect_column_types
        from app.services.pdf_service import _compute_kpi_data

        csv_path = os.path.join(
            os.path.dirname(__file__), '..', 'fixtures', 'edge_case_messy_formatting.csv',
        )
        with open(csv_path, 'rb') as f:
            raw = parse_csv(f.read())

        # Full pipeline: detect types → normalize → KPIs
        col_meta = detect_column_types(raw)
        column_types = {}
        for m in col_meta:
            col_name = m.get("display_name") or m["original_name"]
            column_types[col_name] = m.get("suggested_type", "dimension")
        df_norm = normalize_for_aggregation(raw, column_types)

        revenue_sum = df_norm["Revenue"].sum()
        assert revenue_sum == pytest.approx(440772.96, rel=1e-3), (
            f"Revenue sum drifted: {revenue_sum} vs expected 440772.96"
        )

        config = {"metric_columns": ["Revenue"]}
        ai_content = {"insights": [], "summary": None, "anomalies": [], "trends": []}
        kpis = _compute_kpi_data(df_norm, config, ai_content, "#6366F1")
        rev_kpi = next(k for k in kpis if "Revenue" in k["name"])
        assert rev_kpi["value"] == "440.8K", (
            f"Revenue KPI tile value: expected '440.8K', got '{rev_kpi['value']}'"
        )

    def test_normalize_and_fallback_agree(self):
        """Both code paths — normalization-first and direct-fallback — must
        produce identical KPI values on the same currency-formatted input."""
        from app.services.pdf_service import _compute_kpi_data
        from app.services.data_service import normalize_for_aggregation

        raw = pd.DataFrame({
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "Revenue": ["$9,770.44", "$666.80", "5000", "$1,234.56", "3000"],
            "Units Sold": [100, 200, 150, 175, 125],
        })
        column_types = {"Date": "date", "Revenue": "metric", "Units Sold": "metric"}
        ai_content = {"insights": [], "summary": None, "anomalies": [], "trends": []}
        config = {"metric_columns": ["Revenue", "Units Sold"]}

        # Path A: normalize first, then compute KPIs (report_service flow)
        df_norm = normalize_for_aggregation(raw, column_types)
        kpis_a = _compute_kpi_data(df_norm, config, ai_content, "#6366F1")

        # Path B: direct fallback on raw df (build_sync fallback flow)
        kpis_b = _compute_kpi_data(raw, config, ai_content, "#6366F1")

        assert len(kpis_a) == len(kpis_b)
        for a, b in zip(kpis_a, kpis_b):
            assert a["name"] == b["name"], (
                f"Name mismatch: '{a['name']}' vs '{b['name']}'"
            )
            assert a["value"] == b["value"], (
                f"Value mismatch for {a['name']}: "
                f"normalize-first='{a['value']}' fallback='{b['value']}'"
            )