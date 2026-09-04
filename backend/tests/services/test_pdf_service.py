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
            "sections": ["kpi_overview", "charts", "data_table"],
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
            "sections": ["kpi_overview"],
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
            "sections": ["kpi_overview"],
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
        """Extract all text fragments containing the trend marker from a PDF."""
        import fitz
        texts = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                texts.extend(page.get_text().split('\n'))
        return [t.strip() for t in texts if '%' in t]

    def test_negative_trend_pct_produces_down_arrow(self):
        import tempfile
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.lib.pagesizes import A4
        from app.services.pdf_service import _KPIRow

        tmp = tempfile.mktemp(suffix='.pdf')
        try:
            doc = SimpleDocTemplate(tmp, pagesize=A4)
            card = _KPIRow(
                {"name": "Units Sold", "value": "1,500", "trend": "increasing", "trend_pct": -35.7},
                1, 400, "#D97A34",
            )
            doc.build([card])

            trends = self._extract_trend_text(tmp)
            assert any('\u2193' in t for t in trends), (
                f"Expected down arrow for negative trend_pct, found: {trends}"
            )
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
                {"name": "Revenue", "value": "$50K", "trend": "increasing", "trend_pct": 12.5},
                1, 400, "#D97A34",
            )
            doc.build([card])

            trends = self._extract_trend_text(tmp)
            assert any('\u2191' in t for t in trends), (
                f"Expected up arrow for positive trend_pct, found: {trends}"
            )
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
            "sections": ["kpi_overview"],
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
        assert rev_kpi["value"] == "$19.7K", (
            f"Expected '$19.7K' (${total:,.2f}), got '{rev_kpi['value']}'"
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
        assert rev_kpi["value"] == "$440.8K", (
            f"Revenue KPI tile value: expected '$440.8K', got '{rev_kpi['value']}'"
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

    def test_rate_column_with_high_values_is_currency(self):
        from app.services.pdf_service import _is_currency_col, _is_percentage_col
        series = pd.Series([100.0, 150.0, 200.0, 175.0, 125.0])
        assert _is_currency_col("Rate", series), "Rate with values >5 should be currency"
        assert not _is_percentage_col("Rate", series), "Rate with values >5 should NOT be percentage"

    def test_rate_column_with_low_values_is_percentage(self):
        from app.services.pdf_service import _is_currency_col, _is_percentage_col
        series = pd.Series([0.5, 0.75, 0.8, 0.6, 0.9])
        assert _is_percentage_col("Rate", series), "Rate with values <5 should be percentage"
        assert _is_currency_col("Rate", series) is False, (
            "Rate with values <5 should NOT be currency (max<5 threshold)"
        )

    def test_conversion_rate_column_is_percentage(self):
        from app.services.pdf_service import _is_currency_col, _is_percentage_col
        series = pd.Series([0.3, 0.5, 0.7, 0.4, 0.6])
        assert _is_percentage_col("Conversion Rate", series), "Conversion Rate should be percentage"
        assert _is_currency_col("Conversion Rate", series) is False, "Conversion Rate should NOT be currency"

    def test_rate_kpi_integration(self):
        from app.services.pdf_service import _compute_kpi_data
        df = pd.DataFrame({
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "Rate": [100.0, 150.0, 200.0],
        })
        config = {"metric_columns": ["Rate"], "date_column": "Date"}
        ai_content = {"insights": [], "summary": None, "anomalies": [], "trends": []}
        kpis = _compute_kpi_data(df, config, ai_content, "#6366F1")
        rate_kpi = next(k for k in kpis if "Rate" in k["name"])
        assert rate_kpi["value"].startswith("$"), (
            f"Rate KPI should have $ prefix, got '{rate_kpi['value']}'"
        )
        assert "%" not in rate_kpi["value"], (
            f"Rate KPI should NOT have % suffix, got '{rate_kpi['value']}'"
        )


class TestFooterGrowthLoop:
    """Free tier must show 'Made with Naxely — naxely.com' in footer.
    Pro and Agency must be byte-for-byte unchanged."""

    def test_free_tier_footer_contains_made_with_naxely(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({"Metric": [10, 20], "Value": [100, 200]})
        config = {"metric_columns": ["Value"], "title": "Free Footer", "sections": ["kpi_overview"], "report_id": "test-free-footer-gl1"}
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {"brand_color": "#6366F1", "tier": "free", "logo_url": None, "company_name": None}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            assert "Made with Naxely" in text, "Free footer should contain 'Made with Naxely'"
            assert "naxely.com" in text, "Free footer should contain 'naxely.com'"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_free_tier_footer_not_old_generic(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({"Metric": [10, 20], "Value": [100, 200]})
        config = {"metric_columns": ["Value"], "title": "Free Footer Old", "sections": ["kpi_overview"], "report_id": "test-free-footer-gl2"}
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {"brand_color": "#6366F1", "tier": "free", "logo_url": None, "company_name": None}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            assert "Naxely Report" not in text, "Free footer must NOT use old generic text"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_pro_tier_footer_unchanged(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({"Metric": [10, 20], "Value": [100, 200]})
        config = {"metric_columns": ["Value"], "title": "Pro Footer", "sections": ["kpi_overview"], "report_id": "test-pro-footer-gl1"}
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "TestCo"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            assert "Naxely Report" in text, "Pro footer must still contain 'Naxely Report'"
            assert "Made with Naxely" not in text, "Pro footer must NOT contain 'Made with Naxely'"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_agency_tier_footer_unchanged(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({"Metric": [10, 20], "Value": [100, 200]})
        config = {"metric_columns": ["Value"], "title": "Agency Footer", "sections": ["kpi_overview"], "report_id": "test-agency-footer-gl1"}
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {"brand_color": "#6366F1", "tier": "agency", "logo_url": None, "company_name": "AgencyCo"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            assert "Naxely" not in text, "Agency footer must NOT contain 'Naxely'"
            assert "AgencyCo" in text, "Agency footer must contain company name"
            assert "Made with Naxely" not in text, "Agency footer must NOT contain growth loop"
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestRecommendationsGuard:
    """Recommendations section must only render when the user selected
    'insights' or 'executive_summary' and AI actually ran."""

    def test_no_recommendations_when_no_ai_section(self):
        """sections=['charts','kpi_overview','data_table'] → no Recommendations TOC entry/page."""
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({"Metric": [10, 20], "Value": [100, 200]})
        config = {
            "metric_columns": ["Value"],
            "title": "No AI Sections",
            "sections": ["charts", "kpi_overview", "data_table"],
            "report_id": "test-rec-guard-noai",
        }
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": [],
                       "recommendations": []}
        user_data = {"brand_color": "#6366F1", "tier": "free", "logo_url": None, "company_name": None}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            assert "Recommendations" not in text, (
                "Recommendations section should NOT appear when no AI sections selected"
            )
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_recommendations_appears_with_insights_and_ai_ran(self):
        """sections includes 'insights' and AI content present → Recommendations page appears normally."""
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({"Metric": [10, 20], "Value": [100, 200]})
        config = {
            "metric_columns": ["Value"],
            "title": "With Insights",
            "sections": ["charts", "kpi_overview", "insights", "data_table"],
            "report_id": "test-rec-guard-ai",
        }
        ai_content = {"summary": None, "insights": [{"kpi": "Revenue", "number": "$300", "reason": "Revenue increased steadily", "action": "Invest in growth", "sentiment": "positive", "priority": "high"}], "anomalies": [],
                      "trends": [{"column": "Value", "trend": "increasing", "pct_change": 100.0}], "recommendations": ["Optimize revenue by 10%"]}
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            assert "Recommendations" in text, (
                "Recommendations section header should appear when 'insights' is selected and AI ran"
            )
            assert "Optimize revenue by 10%" in text, (
                "Recommendation content should appear"
            )
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestSectionToggles:
    """Every section toggle must be respected: PDF should only render sections
    that are present in config['sections'].  Cover Page and TOC always render."""

    SECTION_TOC_NAMES = {
        "executive_summary": "Executive Summary",
        "kpi_overview": "Key Metrics Overview",
        "charts": "Charts & Visualizations",
        "insights": "AI Insights",
        "anomalies": "Anomaly Flags",
        "data_table": "Data Table",
        "appendix": "Appendix — Raw Data",
        "recommendations": "Recommendations",
    }
    """Maps section ID → text that appears in TOC / section headers."""

    @staticmethod
    def _make_df():
        return pd.DataFrame({
            "Metric": [10, 20, 30],
            "Value": [100, 200, 300],
        })

    @staticmethod
    def _make_ai_content(with_summary=False):
        ai = {
            "summary": None,
            "insights": [],
            "anomalies": [],
            "trends": [],
            "recommendations": [],
        }
        if with_summary:
            from app.services.ai_service import SummaryResult
            ai["summary"] = SummaryResult(
                lead="Sales grew.",
                context="Context text.",
                implication="Implication text.",
                action="Action text.",
            )
        return ai

    @staticmethod
    def _make_user_data(**overrides):
        data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        data.update(overrides)
        return data

    def _check_pdf(self, sections: list[str], expect_present: set[str], expect_absent: set[str]):
        """Generate a PDF with the given sections and assert TOC/section-header presence."""
        import fitz
        from app.services.pdf_service import build_sync

        df = self._make_df()
        has_summary = "executive_summary" in sections
        ai = self._make_ai_content(with_summary=has_summary)

        # Add some anomalies so anomaly section can render if toggled (plain-language wording)
        if "anomalies" in sections:
            ai["anomalies"] = [{"message": "Value was unusually high at 10.00 — well outside the typical range of 2.00 – 8.00.", "z_score": 3.5}]

        if "insights" in sections:
            ai["insights"] = [{"kpi": "Value", "number": "$300", "reason": "Steady growth", "action": "Invest", "sentiment": "positive", "priority": "high"}]

        config = {
            "metric_columns": ["Value"],
            "title": "Section Toggle Test",
            "sections": sections,
            "report_id": f"test-section-{'-'.join(sections) if sections else 'none'}",
        }
        user_data = self._make_user_data()

        path = build_sync(df, [], ai, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()

            for name in expect_present:
                assert name in text, (
                    f"Expected section '{name}' to appear in PDF with sections={sections}, "
                    f"but it was not found in the rendered text"
                )
            for name in expect_absent:
                assert name not in text, (
                    f"Section '{name}' appeared in PDF with sections={sections}, "
                    f"but it should have been excluded"
                )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    # ── 9 test cases ──────────────────────────────────────────────────

    def test_executive_summary_only(self):
        """Only Cover + Executive Summary + Recommendations (tied to exec_summary)."""
        self._check_pdf(
            sections=["executive_summary"],
            expect_present={"Executive Summary", "Recommendations", "Cover Page"},
            expect_absent={"Key Metrics Overview", "Charts & Visualizations", "AI Insights",
                           "Anomaly Flags", "Data Table", "Appendix — Raw Data"},
        )

    def test_kpi_overview_only(self):
        """Only Cover + Key Metrics Overview."""
        self._check_pdf(
            sections=["kpi_overview"],
            expect_present={"Key Metrics Overview", "Cover Page"},
            expect_absent={"Executive Summary", "Charts & Visualizations", "AI Insights",
                           "Anomaly Flags", "Data Table", "Recommendations", "Appendix — Raw Data"},
        )

    def test_charts_only(self):
        """Only Cover + Charts."""
        self._check_pdf(
            sections=["charts"],
            expect_present={"Charts & Visualizations", "Cover Page"},
            expect_absent={"Executive Summary", "Key Metrics Overview", "AI Insights",
                           "Anomaly Flags", "Data Table", "Recommendations", "Appendix — Raw Data"},
        )

    def test_ai_insights_only(self):
        """Only Cover + AI Insights + Recommendations (tied to insights)."""
        self._check_pdf(
            sections=["insights"],
            expect_present={"AI Insights", "Recommendations", "Cover Page"},
            expect_absent={"Executive Summary", "Key Metrics Overview", "Charts & Visualizations",
                           "Anomaly Flags", "Data Table", "Appendix — Raw Data"},
        )

    def test_anomalies_only(self):
        """Only Cover + Anomaly Flags."""
        self._check_pdf(
            sections=["anomalies"],
            expect_present={"Anomaly Flags", "Cover Page"},
            expect_absent={"Executive Summary", "Key Metrics Overview", "Charts & Visualizations",
                           "AI Insights", "Data Table", "Recommendations", "Appendix — Raw Data"},
        )

    def test_data_table_only(self):
        """Only Cover + Data Table."""
        self._check_pdf(
            sections=["data_table"],
            expect_present={"Data Table", "Cover Page"},
            expect_absent={"Executive Summary", "Key Metrics Overview", "Charts & Visualizations",
                           "AI Insights", "Anomaly Flags", "Recommendations", "Appendix — Raw Data"},
        )

    def test_appendix_only(self):
        """Only Cover + Appendix."""
        self._check_pdf(
            sections=["appendix"],
            expect_present={"Appendix — Raw Data", "Cover Page"},
            expect_absent={"Executive Summary", "Key Metrics Overview", "Charts & Visualizations",
                           "AI Insights", "Anomaly Flags", "Data Table", "Recommendations"},
        )

    def test_all_sections(self):
        """Every section checked → all present except Key Metrics Overview which is now merged into Executive Summary."""
        self._check_pdf(
            sections=["executive_summary", "kpi_overview", "charts", "insights",
                      "anomalies", "data_table", "appendix"],
            expect_present={"Executive Summary", "Charts & Visualizations",
                            "AI Insights", "Anomaly Flags", "Data Table", "Recommendations",
                            "Appendix — Raw Data", "Cover Page", "Key Metrics"},
            expect_absent={"Key Metrics Overview"},
        )

    def test_no_sections(self):
        """No sections checked → only Cover + TOC page, no body section headers."""
        self._check_pdf(
            sections=[],
            expect_present={"Cover Page"},
            expect_absent={"Executive Summary", "Key Metrics Overview", "Charts & Visualizations",
                           "AI Insights", "Anomaly Flags", "Data Table", "Recommendations",
                           "Appendix — Raw Data"},
        )


# ────────────────────────────────────────────────────────────────────────────
# Part B — PDF "Ledger" redesign
# ────────────────────────────────────────────────────────────────────────────

class TestLedgerTocNumbering:
    """TOC entries must be zero-padded two-digit numbers (01, 02, … 0N)."""

    def _build_toc_text(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300],
            "Profit": [100, 300, 500, 700],
        })
        config = {
            "metric_columns": ["Revenue", "Profit"],
            "title": "TOC Numbering Test",
            "sections": ["kpi_overview", "charts", "anomalies"],
            "report_id": "test-ledger-toc",
        }
        ai_content = {
            "summary": None,
            "insights": [],
            "anomalies": [{"message": "Spike in Revenue"}],
            "trends": [],
            "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            assert len(doc) >= 3, "Expected at least Cover, TOC, and one body page"
            toc_text = doc[1].get_text()  # TOC is the 2nd page
            doc.close()
            return toc_text
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_toc_entries_zero_padded_two_digit(self):
        toc_text = self._build_toc_text()
        assert "01" in toc_text, f"Cover Page must be numbered 01, got:\n{toc_text}"
        assert "02" in toc_text, f"Table of Contents must be numbered 02, got:\n{toc_text}"
        assert "03" in toc_text, f"First section must be numbered 03, got:\n{toc_text}"


class TestChartsTwoPerPage:
    """Charts section must paginate two charts per page (not one per page)."""

    def test_charts_render_two_per_page(self):
        import fitz
        from app.services.chart_service import generate_sync, cleanup_charts
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=12, freq="D"),
            "Revenue": [1000, 1200, 1100, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100],
            "Clicks": [100, 110, 105, 120, 130, 125, 140, 150, 145, 160, 155, 170],
            "Region": ["North"] * 6 + ["South"] * 6,
        })
        specs = [
            {"x": "Date", "y": "Revenue", "type": "line", "title": "Revenue Trend"},
            {"x": "Date", "y": "Clicks", "type": "line", "title": "Clicks Trend"},
            {"x": "Region", "y": "Revenue", "type": "bar", "title": "Revenue by Region"},
            {"x": "Region", "y": "Clicks", "type": "bar", "title": "Clicks by Region"},
        ]
        report_id = "test-ledger-charts"
        chart_config = {"tier": "pro", "metric_columns": ["Revenue", "Clicks"]}
        chart_paths = generate_sync(df, report_id, chart_config, "#6366F1", specs)
        assert len(chart_paths) == 4, f"Expected 4 charts, got {len(chart_paths)}"

        config = {
            "metric_columns": ["Revenue", "Clicks"],
            "title": "Two-Per-Page Test",
            "sections": ["charts"],
            "report_id": report_id,
        }
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, chart_paths, ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            image_counts = [len(page.get_images(full=True)) for page in doc]
            doc.close()
            chart_pages = [c for c in image_counts if c > 0]
            assert chart_pages, f"No chart pages found: {image_counts}"
            assert max(chart_pages) <= 2, f"More than 2 charts on a page: {image_counts}"
            assert sum(chart_pages) == 4, f"Expected 4 chart images total, got {image_counts}"
            assert chart_pages.count(2) >= 2, f"Expected 2 pages with 2 charts each, got {image_counts}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
            cleanup_charts(report_id)


class TestKpiMonoNumbers:
    """KPI numeric values must be set in the mono typeface (tabular alignment)."""

    def test_kpi_values_use_mono_font(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300],
            "Profit": [100, 300, 500, 700],
        })
        config = {
            "metric_columns": ["Revenue", "Profit"],
            "title": "Mono Numbers Test",
            "sections": ["kpi_overview"],
            "report_id": "test-ledger-mono",
        }
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            mono_spans = []
            for page in doc:
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        for span in line["spans"]:
                            if span["font"] == "IBMPlexMono-Bold":
                                mono_spans.append(span["text"])
            doc.close()
            assert mono_spans, "No KPI value rendered in IBMPlexMono-Bold"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestAnomalyRustColor:
    """Anomaly text and accent must use the fixed RUST (#A8481F), not the old red."""

    def test_anomaly_text_uses_rust_color(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 4800, 4600, 4400],
        })
        config = {
            "metric_columns": ["Revenue"],
            "title": "Rust Anomaly Test",
            "sections": ["anomalies"],
            "report_id": "test-ledger-rust",
        }
        ai_content = {
            "summary": None,
            "insights": [],
            "anomalies": [{"message": "Revenue was unusually high at 9999.00 — well outside the typical range of 100.00 – 500.00.", "z_score": 5.1}],
            "trends": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        ink = int("1A1D24", 16)
        try:
            doc = fitz.open(path)
            found = []
            for page in doc:
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        for span in line["spans"]:
                            if "unusually high" in span["text"]:
                                found.append(span["color"])
            doc.close()
            assert found, "Anomaly message text not found"
            assert all(c == ink for c in found), f"Anomaly text should be INK #1A1D24 (redesigned tinted row, tier-varying accent), got {found}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestSectionHeaderLedger:
    """Section headers must be plain serif headings in INK with a hairline rule,
    NOT solid brand-colored bands with white text (the pre-redesign style)."""

    INK_RGB = int("1A1D24", 16)
    BRAND_RGB = int("6366F1", 16)

    HEADERS = [
        "Executive Summary",
        # "Key Metrics Overview" is now merged into Executive Summary as "Key Metrics" subheading (IBMPlexSans, not Fraunces) — no longer a standalone Fraunces header
        "Charts & Visualizations",
        "AI Insights",
        "Anomaly Flags",
        "Data Table",
        "Recommendations",
        "Appendix",
    ]

    def _build_all_sections_pdf(self):
        import fitz
        from app.services.ai_service import SummaryResult
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300],
            "Profit": [100, 300, 500, 700],
        })
        config = {
            "metric_columns": ["Revenue", "Profit"],
            "title": "Section Header Test",
            "sections": ["executive_summary", "kpi_overview", "charts", "insights",
                         "anomalies", "data_table", "appendix"],
            "report_id": "test-ledger-header",
        }
        ai_content = {
            "summary": SummaryResult(
                lead="Revenue grew steadily.",
                context="Context text.",
                implication="Implication text.",
                action="Action text.",
            ),
            "insights": [{"kpi": "Revenue", "number": "$5000", "reason": "Steady", "action": "Invest",
                          "sentiment": "positive", "priority": "high"}],
            "anomalies": [{"message": "Spike detected in Revenue"}],
            "trends": [],
            "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        return path

    def _body_pages(self, doc):
        """Pages after cover (0) and TOC (1)."""
        return [doc[i] for i in range(2, len(doc))]

    def test_all_section_headers_are_serif_ink(self):
        import fitz
        path = self._build_all_sections_pdf()
        try:
            doc = fitz.open(path)
            spans = []
            for page in self._body_pages(doc):
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        spans.extend(line["spans"])
            doc.close()

            serif_spans = [s for s in spans if s["font"].startswith("Fraunces")]
            for name in self.HEADERS:
                matching = [s for s in serif_spans if name in s["text"]]
                assert matching, (
                    f"Section header '{name}' not rendered as Fraunces serif"
                )
                assert all(s["color"] == self.INK_RGB for s in matching), (
                    f"Section header '{name}' must be INK #1A1D24 (not white-on-band), got "
                    f"{[hex(s['color']) for s in matching]}"
                )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_no_brand_colored_band_rects(self):
        """No wide brand-colored filled rectangles near the top of body pages —
        the old section-header band must be gone on every page."""
        import fitz
        path = self._build_all_sections_pdf()
        try:
            doc = fitz.open(path)
            bands = []
            for page in self._body_pages(doc):
                for d in page.get_drawings():
                    if not d.get("fill"):
                        continue
                    r, g, b = (round(c * 255) for c in d["fill"])
                    fill = (r << 16) | (g << 8) | b
                    rect = d["rect"]
                    if (fill == self.BRAND_RGB and rect.width > 300
                            and rect.height <= 45 and rect.y0 < 100):
                        bands.append((page.number, fill, rect))
            doc.close()
            assert not bands, f"Brand-colored band rectangles still present: {bands}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestDataTableLedger:
    """The data table's internal column-header row must follow the Ledger
    design (plain uppercase mono labels + hairline rule) and must never
    overlap cell content — no colored band, no sideways text spill."""

    MUTED_RGB = int("6B6E76", 16)
    BRAND_RGB = int("6366F1", 16)

    @staticmethod
    def _build_table_pdf(n_rows=48):
        import fitz
        from app.services.pdf_service import build_sync

        rng = np.random.default_rng(1)
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-06", periods=n_rows, freq="D"),
            "Region": [rng.choice(["East", "West", "North", "South"]) for _ in range(n_rows)],
            "Salesperson": [rng.choice(["Carol", "David", "Elena", "Grace", "Ivy", "Jack"]) for _ in range(n_rows)],
            "Product": [rng.choice(["Widget", "Gadget", "Whatchamacallit", "Thingamajig"]) for _ in range(n_rows)],
            "Category": [rng.choice(["Hardware", "Software", "Services", "Accessories"]) for _ in range(n_rows)],
        })
        config = {
            "metric_columns": [],
            "title": "Data Table Ledger Test",
            "sections": ["data_table"],
            "report_id": f"test-ledger-datatable-{n_rows}",
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        return build_sync(df, [], {}, config, user_data)

    @staticmethod
    def _build_appendix_pdf(n_rows=48):
        import fitz
        from app.services.pdf_service import build_sync

        rng = np.random.default_rng(1)
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-06", periods=n_rows, freq="D"),
            "Region": [rng.choice(["East", "West", "North", "South"]) for _ in range(n_rows)],
            "Salesperson": [rng.choice(["Carol", "David", "Elena", "Grace", "Ivy", "Jack"]) for _ in range(n_rows)],
            "Product": [rng.choice(["Widget", "Gadget", "Whatchamacallit", "Thingamajig"]) for _ in range(n_rows)],
            "Category": [rng.choice(["Hardware", "Software", "Services", "Accessories"]) for _ in range(n_rows)],
        })
        config = {
            "metric_columns": [],
            "title": "Appendix Ledger Test",
            "sections": ["appendix"],
            "report_id": f"test-ledger-appendix-{n_rows}",
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        return build_sync(df, [], {}, config, user_data)

    def _appendix_pages(self, doc):
        """Pages that render the Appendix table header (uppercase mono labels)."""
        pages = []
        for i in range(2, len(doc)):
            text = doc[i].get_text()
            if "SALESPERSON" in text and "REGION" in text:
                pages.append(doc[i])
        return pages

    def test_appendix_header_is_mono_muted_uppercase(self):
        """The Appendix — Raw Data table must use the same Ledger header style
        (uppercase mono muted labels), not the old brand-colored band."""
        import fitz
        path = self._build_appendix_pdf()
        try:
            doc = fitz.open(path)
            pages = self._appendix_pages(doc)
            assert pages, "expected at least one Appendix table page"
            for page in pages:
                spans = []
                for b in page.get_text("dict")["blocks"]:
                    if b["type"] != 0:
                        continue
                    for line in b.get("lines", []):
                        spans.extend(line["spans"])
                headers = [s for s in spans if s["text"] in
                           ("DATE", "REGION", "SALESPERSON", "PRODUCT", "CATEGORY")]
                assert headers, f"uppercase mono header labels missing on page {page.number}"
                assert all(s["font"].startswith("IBMPlexMono") for s in headers), (
                    f"appendix header must be IBMPlexMono, got {[s['font'] for s in headers]}"
                )
                assert all(s["color"] == self.MUTED_RGB for s in headers), (
                    f"appendix header must be MUTED #6B6E76, got "
                    f"{[hex(s['color']) for s in headers]}"
                )
            doc.close()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_no_brand_band_behind_appendix_header(self):
        """Appendix header row must have no brand-colored background fill."""
        import fitz
        path = self._build_appendix_pdf()
        try:
            doc = fitz.open(path)
            bands = []
            for page in self._appendix_pages(doc):
                for d in page.get_drawings():
                    if not d.get("fill"):
                        continue
                    r, g, b = (round(c * 255) for c in d["fill"])
                    fill = (r << 16) | (g << 8) | b
                    rect = d["rect"]
                    if fill == self.BRAND_RGB and rect.width > 300 and rect.height <= 45:
                        bands.append((page.number, fill, rect))
            doc.close()
            assert not bands, f"brand-colored appendix header band still present: {bands}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _table_pages(self, doc):
        """Pages after cover (0) and TOC (1) that contain table header labels."""
        pages = []
        for i in range(2, len(doc)):
            text = doc[i].get_text()
            if "SALESPERSON" in text or "REGION" in text:
                pages.append(doc[i])
        return pages

    def test_header_is_mono_muted_uppercase(self):
        import fitz
        path = self._build_table_pdf()
        try:
            doc = fitz.open(path)
            pages = self._table_pages(doc)
            assert len(pages) >= 2, "expected the data table to span multiple pages"
            for page in pages:
                spans = []
                for b in page.get_text("dict")["blocks"]:
                    if b["type"] != 0:
                        continue
                    for line in b.get("lines", []):
                        spans.extend(line["spans"])
                headers = [s for s in spans if s["text"] in
                           ("DATE", "REGION", "SALESPERSON", "PRODUCT", "CATEGORY")]
                assert headers, f"uppercase mono header labels missing on page {page.number}"
                assert all(s["font"].startswith("IBMPlexMono") for s in headers), (
                    f"table header must be IBMPlexMono, got {[s['font'] for s in headers]}"
                )
                assert all(s["color"] == self.MUTED_RGB for s in headers), (
                    f"table header must be MUTED #6B6E76, got "
                    f"{[hex(s['color']) for s in headers]}"
                )
            doc.close()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_no_brand_band_behind_header(self):
        import fitz
        path = self._build_table_pdf()
        try:
            doc = fitz.open(path)
            bands = []
            for page in self._table_pages(doc):
                for d in page.get_drawings():
                    if not d.get("fill"):
                        continue
                    r, g, b = (round(c * 255) for c in d["fill"])
                    fill = (r << 16) | (g << 8) | b
                    rect = d["rect"]
                    if fill == self.BRAND_RGB and rect.width > 300 and rect.height <= 45:
                        bands.append((page.number, fill, rect))
            doc.close()
            assert not bands, f"brand-colored header band still present: {bands}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_no_overlapping_cell_text(self):
        """Column text must never spill over into an adjacent column or row
        (datetime values are the historical offender: width was computed from
        a date-only str sample while cells render the full timestamp)."""
        import fitz
        path = self._build_table_pdf()
        try:
            doc = fitz.open(path)
            overlaps = []
            for page in self._table_pages(doc):
                words = page.get_text("words")
                for i in range(len(words)):
                    for j in range(i + 1, len(words)):
                        w1, w2 = words[i], words[j]
                        x0, x1 = max(w1[0], w2[0]), min(w1[2], w2[2])
                        y0, y1 = max(w1[1], w2[1]), min(w1[3], w2[3])
                        if x0 < x1 and y0 < y1:
                            h1, h2 = w1[3] - w1[1], w2[3] - w2[1]
                            if (y1 - y0) / min(h1, h2) > 0.4:
                                overlaps.append((page.number, w1[4], w2[4]))
            doc.close()
            assert not overlaps, f"overlapping table text: {overlaps[:5]}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestChartCaptionsRendered:
    """Data-driven chart captions must render under each chart in the PDF."""

    def test_caption_text_appears_below_charts(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=12, freq="D"),
            "Revenue": [1000, 1200, 1100, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100],
        })
        specs = [{"x": "Date", "y": "Revenue", "type": "line", "title": "Revenue Trend"}]
        report_id = "test-ledger-caprender"
        chart_config = {"tier": "pro", "metric_columns": ["Revenue"]}
        chart_paths = generate_sync(df, report_id, chart_config, "#6366F1", specs)

        config = {
            "metric_columns": ["Revenue"],
            "title": "Caption Render Test",
            "sections": ["charts"],
            "report_id": report_id,
        }
        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, chart_paths, ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            assert "1,000" in text, "Caption should cite the actual start figure"
            assert "2,100" in text, "Caption should cite the actual end figure"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
            cleanup_charts(report_id)


class TestNoBackgroundRuledLines:
    """Body pages must not be filled with full-page hairline ledger rules —
    only content-own rules (section header hairlines, table borders) remain."""

    @staticmethod
    def _count_horizontal_rules(page):
        count = 0
        for d in page.get_drawings():
            r = d["rect"]
            if r.height < 1.5 and r.width > 400:
                count += 1
        return count

    def test_body_pages_have_no_full_page_hairlines(self):
        import fitz
        from app.services.ai_service import SummaryResult
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300],
            "Profit": [100, 300, 500, 700],
        })
        config = {
            "metric_columns": ["Revenue", "Profit"],
            "title": "Ruled Lines Test",
            "sections": ["executive_summary", "kpi_overview"],
            "report_id": "test-ledger-norules",
        }
        ai_content = {
            "summary": SummaryResult(
                lead="Revenue grew steadily.",
                context="Context text.",
                implication="Implication text.",
                action="Action text.",
            ),
            "insights": [],
            "anomalies": [],
            "trends": [],
            "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            per_page = [self._count_horizontal_rules(page) for page in doc]
            doc.close()
            assert per_page, "No pages found in PDF"
            assert max(per_page) < 8, (
                f"Expected only content-owned rules, found {per_page} full-page "
                f"horizontal lines per page — background ruling may still be drawing"
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestExecutiveSummaryStatRow:
    """Executive Summary lead uses a serif drop cap and a 3-column ruled stat
    row (vertical hairline dividers) instead of the old single-line strip."""

    def _build_es_pdf(self):
        import fitz
        from app.services.ai_service import SummaryResult
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300],
            "Profit": [100, 300, 500, 700],
        })
        config = {
            "metric_columns": ["Revenue", "Profit"],
            "title": "Stat Row Test",
            "sections": ["executive_summary"],
            "report_id": "test-ledger-statrow",
        }
        ai_content = {
            "summary": SummaryResult(
                lead="Revenue grew steadily through the quarter.",
                context="Context text.",
                implication="Implication text.",
                action="Action text.",
            ),
            "insights": [],
            "anomalies": [],
            "trends": [],
            "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        doc = fitz.open(path)
        return doc, path

    def test_lead_paragraph_has_serif_drop_cap(self):
        doc, path = self._build_es_pdf()
        try:
            spans = []
            for block in doc[2].get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans.extend(line["spans"])
            drop_caps = [
                s for s in spans
                if s["font"].startswith("Fraunces") and 19 <= s["size"] <= 23
                and len(s["text"].strip()) == 1
            ]
            assert drop_caps, (
                f"Expected a single-character Fraunces drop cap in the lead, "
                f"spans: {[(s['font'], round(s['size'], 1), s['text']) for s in spans if s['font'].startswith('Fraunces')]}"
            )
        finally:
            doc.close()
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_stat_row_has_vertical_dividers(self):
        doc, path = self._build_es_pdf()
        try:
            vertical = sum(
                1 for d in doc[2].get_drawings()
                if d["rect"].width < 1.5 and d["rect"].height > 20
            )
            assert vertical >= 2, (
                f"Expected 2 vertical hairline dividers in the 3-column stat row, "
                f"found {vertical}"
            )
        finally:
            doc.close()
            try:
                os.unlink(path)
            except OSError:
                pass


class TestInsightLedgerRow:
    """AI insight rows must use tinted card treatment: severity-tinted background
    via _brand_tint, left accent strip, serif index, severity tag, and arrowed action."""

    def _build_insights_pdf(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300],
        })
        config = {
            "metric_columns": ["Revenue"],
            "title": "Insight Ledger Test",
            "sections": ["insights"],
            "report_id": "test-ledger-insights",
        }
        ai_content = {
            "summary": None,
            "insights": [
                {"kpi": "Revenue", "number": "$5,200", "reason": "Steady growth in billings.",
                 "action": "Scale the winning channel", "sentiment": "positive", "priority": "high"},
                {"kpi": "Revenue", "number": "$5,100", "reason": "Slight dip in the middle week.",
                 "action": "Review campaign mix", "sentiment": "negative", "priority": "low"},
            ],
            "anomalies": [],
            "trends": [],
            "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        doc = fitz.open(path)
        return doc, path

    def test_no_card_background_rectangles(self):
        doc, path = self._build_insights_pdf()
        try:
            filled = []
            for d in doc[2].get_drawings():
                if not d.get("fill"):
                    continue
                rect = d["rect"]
                if rect.width > 300 and 40 < rect.height < 200:
                    filled.append((doc[2].number, rect))
            assert filled, f"Insight rows should now have tinted card backgrounds (phase 2), but none found"
            assert len(filled) == 2, f"Expected 2 insight card backgrounds, got {len(filled)}: {filled}"
        finally:
            doc.close()
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_severity_tag_and_arrowed_action_render(self):
        doc, path = self._build_insights_pdf()
        try:
            text = doc[2].get_text()
            assert "HIGH" in text, f"Severity tag HIGH missing, got:\n{text}"
            assert "LOW" in text, f"Severity tag LOW missing, got:\n{text}"
            assert "\u2192" in text, f"Arrowed action (\u2192) missing, got:\n{text}"
            assert "01" in text, f"Serif index 01 missing, got:\n{text}"
        finally:
            doc.close()
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_fit_text_lines_truncates_at_word_boundary(self):
        """Long AI text must wrap to at most MAX_LINES and any ellipsis must
        follow a whole word — never a mid-word cut."""
        from reportlab.pdfbase import pdfmetrics as pm
        from app.services.pdf_service import _fit_text_lines

        font, size, width, max_lines = 'IBMPlexSans', 8, 477, 2
        words = [f'word{i:03d}' for i in range(300)]
        long_text = ' '.join(words)
        lines = _fit_text_lines(long_text, font, size, width, max_lines)
        assert len(lines) == 2, f"expected exactly {max_lines} lines, got {len(lines)}"
        assert lines[1].endswith('\u2026'), f"long text should end with ellipsis, got: {lines[1][-40:]}"
        assert all(pm.stringWidth(l, font, size) <= width for l in lines), "a wrapped line overflowed the box"

        # Word-boundary guarantee: every emitted line is a contiguous slice of
        # whole input words (ellipsis truncated last line included).
        slices = {' '.join(words[i:j]) for i in range(len(words)) for j in range(i, len(words) + 1)}
        assert lines[0] in slices, f"first line splits a word: …{lines[0][-30:]}"
        core = lines[1][:-1]  # drop the trailing ellipsis
        assert core in slices, f"truncated line splits a word: …{core[-30:]}"

        # Short text is left untouched (no ellipsis, no wrapping needed)
        short = _fit_text_lines('A short reason.', font, size, width, max_lines)
        assert short == ['A short reason.'] and not short[-1].endswith('\u2026')

    def test_long_insight_pdf_text_wraps_without_mid_word_cut(self):
        """The rendered insight page must show the wrapped reason (not clipped
        mid-word) and the action arrow intact."""
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({"Revenue": [5000, 5200]})
        config = {
            "metric_columns": ["Revenue"],
            "title": "Insight Wrap Test",
            "sections": ["insights"],
            "report_id": "test-ledger-insight-wrap",
        }
        reason = ("This is an unusually long insight reason produced by the language model that "
                  "keeps going on and on about the underlying driver behind the recent decline in "
                  "billable output across the entire agency portfolio and how it relates to staffing "
                  "levels and utilization rates over the whole reporting period under review.")
        action = ("Launch an aggressive utilization improvement program across every single team "
                  "and every single project right away to lift average weekly hours back toward the "
                  "seven hour target and stop the decline before it compounds further next quarter")
        ai_content = {
            "summary": None,
            "insights": [{"kpi": "Revenue", "number": "$5,200", "reason": reason,
                          "action": action, "sentiment": "negative", "priority": "high"}],
            "anomalies": [],
            "trends": [],
            "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = doc[2].get_text()
            doc.close()
            assert '\u2026' in text, "long insight text should truncate with an ellipsis"
            assert "decline in billable" in text, "wrapped reason line missing from page"
            assert '\u2192' in text, "arrowed action missing"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestTrendQualifierLabels:
    """The Key Metrics % must carry a qualifier naming which calculation
    produced it (monthly-aggregate trend vs raw first-to-last), so it never
    silently contradicts a chart caption using the other measure."""

    def test_ledger_and_cover_render_monthly_trend_qualifier(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Date": pd.date_range("2026-01-12", periods=48, freq="D"),
            "Revenue": list(range(348, 396)),
        })
        config = {
            "metric_columns": ["Revenue"],
            "date_column": "Date",
            "title": "Label Test",
            "sections": ["kpi_overview"],
            "report_id": "test-trend-label",
        }
        ai_content = {
            "summary": None, "insights": [], "anomalies": [],
            "trends": [], "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "\n".join(p.get_text() for p in doc)
            doc.close()
            assert "monthly trend" in text, f"trend qualifier missing from PDF:\n{text}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestWordBoundaryTruncation:
    """Anomaly messages and data-table cells must truncate at a word boundary
    (the same guarantee insight cards got in da20c41), never a raw character
    slice."""

    def test_truncate_words_keeps_whole_words(self):
        from app.services.pdf_service import _truncate_words

        text = "Summer Sale Extended Launch Campaign 2026"
        out = _truncate_words(text, 18)
        words = text.split(' ')
        prefixes = {' '.join(words[:i]) for i in range(len(words) + 1)}
        assert out[:-1] in prefixes, f"mid-word cut: {out!r}"
        assert out == "Summer Sale\u2026", out

    def test_truncate_words_short_text_untouched(self):
        from app.services.pdf_service import _truncate_words

        assert _truncate_words("Short name", 18) == "Short name"

    def test_truncate_words_unbreakable_word_falls_back_to_char_cut(self):
        from app.services.pdf_service import _truncate_words

        token = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        out = _truncate_words(token, 18)
        assert out == token[:17] + '\u2026'

    def test_anomaly_box_truncates_at_word_boundary_in_pdf(self):
        import fitz
        from app.services.pdf_service import build_sync

        msg = ("This is an unusually long anomaly message that comfortably exceeds one "
               "hundred twenty characters so the legacy character slice would cut straight "
               "through the middle of a word when it reaches the end of the box budget")
        assert len(msg) > 120, len(msg)
        config = {
            "metric_columns": ["Revenue"],
            "title": "Anomaly Wrap Test",
            "sections": ["anomalies"],
            "report_id": "test-anomaly-wrap",
        }
        ai_content = {
            "summary": None, "insights": [], "trends": [], "recommendations": [],
            "anomalies": [{"message": msg}],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df := pd.DataFrame({"Revenue": [100, 200]}), [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            page_text = "\n".join(p.get_text() for p in doc)
            doc.close()
            msg_words = msg.split(' ')
            found = False
            for line in page_text.splitlines():
                line = line.strip()
                if line.endswith('\u2026'):
                    core = line[:-1].strip()
                    # Core must be a contiguous sequence of whole words from msg (1-line prefix or 2nd-line continuation)
                    core_words = core.split()
                    found_seq = False
                    for i in range(len(msg_words) - len(core_words) + 1):
                        if msg_words[i:i+len(core_words)] == core_words:
                            found_seq = True
                            break
                    assert found_seq, f"mid-word cut in anomaly box: {line!r} core {core_words!r} not a word-boundary subsequence"
                    found = True
            assert found, f"no word-truncated anomaly line found:\n{page_text}"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_data_table_cell_truncates_at_word_boundary(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [100, 200],
            "Campaign Name": ["Summer Sale Extended Launch Campaign 2026", "AB" * 20],
        })
        config = {
            "metric_columns": ["Revenue"],
            "title": "Cell Wrap Test",
            "sections": ["data_table"],
            "report_id": "test-cell-wrap",
        }
        ai_content = {
            "summary": None, "insights": [], "anomalies": [],
            "trends": [], "recommendations": [],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            text = "\n".join(p.get_text() for p in doc)
            doc.close()
            assert "Summer Sale\u2026" in text, f"cell should end at a word boundary:\n{text}"
            assert "Summer Sale Extended" not in text, "full untruncated cell leaked through"
            assert "ABABABABABABABABA\u2026" in text, "unbreakable token fallback missing"
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    """Recommendation numbering must be rendered in Fraunces at display size
    (16pt), zero-padded, not the old tiny 12pt badge number."""

class TestRecommendationDisplayNumbering:
    """Recommendation numbering must be rendered in Fraunces at display size
    (16pt), zero-padded, not the old tiny 12pt badge number."""

    def test_recommendation_number_is_serif_display_size(self):
        import fitz
        from app.services.pdf_service import build_sync

        df = pd.DataFrame({
            "Revenue": [5000, 5200, 5100, 5300],
        })
        config = {
            "metric_columns": ["Revenue"],
            "title": "Rec Numbering Test",
            "sections": ["insights"],
            "report_id": "test-ledger-recnum",
        }
        ai_content = {
            "summary": None,
            "insights": [{"kpi": "Revenue", "number": "$5,200", "reason": "Steady.",
                          "action": "Invest", "sentiment": "positive", "priority": "medium"}],
            "anomalies": [],
            "trends": [],
            "recommendations": ["Double down on the top channel.", "Cut spend on underperformers."],
        }
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test"}
        path = build_sync(df, [], ai_content, config, user_data)
        try:
            doc = fitz.open(path)
            spans = []
            for page in doc:
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        spans.extend(line["spans"])
            doc.close()
            numbers = [
                s for s in spans
                if s["font"].startswith("Fraunces") and s["size"] >= 15
                and s["text"].strip() in {"01", "02"}
            ]
            assert numbers, (
                f"Expected Fraunces display-size recommendation numbers 01/02, "
                f"got: {[(s['font'], round(s['size'], 1), s['text']) for s in spans if s['font'].startswith('Fraunces')]}"
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


class TestKpiGridCounts:
    """Regression for KPI-count branches (1/2/4/5) never exercised before — both merged
    exec+KPI and standalone KPI pages. Fixes n==1 clipping and deduplicates grid logic."""

    def _make_df(self, n):
        import pandas as pd
        names = ["Revenue", "Units Sold", "Clicks", "Profit", "Cost"]
        base = [
            [1000, 1200, 1100, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
            [300, 290, 285, 280, 275, 270, 265, 260, 255, 250],
            [100, 110, 105, 120, 130, 125, 140, 150, 145, 160],
            [5000, 5200, 5100, 5300, 5400, 5500, 5600, 5700, 5800, 5900],
            [200, 220, 210, 230, 240, 250, 260, 270, 280, 290],
        ]
        data = {"Date": pd.date_range("2024-01-01", periods=10, freq="D")}
        for i in range(n):
            data[names[i]] = base[i]
        data["Region"] = ["North", "South"] * 5
        return pd.DataFrame(data)

    def _render(self, n, mode):
        import fitz
        from app.services.pdf_service import build_sync
        from app.services.ai_service import SummaryResult
        df = self._make_df(n)
        metric_cols = [c for c in df.columns if c not in ("Date", "Region")][:n]
        if mode == "merged":
            sections = ["executive_summary", "kpi_overview"]
            summary = SummaryResult(lead="Sales grew.", context="Ctx", implication="Imp", action="Act")
            ai = {"summary": summary, "insights": [], "anomalies": [], "trends": [], "recommendations": []}
            rid = f"test-kpi-n{n}-merged"
        else:
            sections = ["kpi_overview"]
            ai = {"summary": None, "insights": [], "anomalies": [], "trends": [], "recommendations": []}
            rid = f"test-kpi-n{n}-standalone"
        config = {"metric_columns": metric_cols, "title": f"KPI {n} {mode}", "sections": sections, "report_id": rid}
        user_data = {"brand_color": "#6366F1", "tier": "pro", "logo_url": None, "company_name": "Test Corp"}
        path = build_sync(df, [], ai, config, user_data)
        doc = fitz.open(path)
        text = " ".join(p.get_text() for p in doc)
        pages = len(doc)
        doc.close()
        return path, text, pages

    def test_kpi_1_merged(self):
        import os
        path, text, pages = self._render(1, "merged")
        try:
            assert pages == 4, f"merged n=1 should be 4 pages (cover,TOC,exec+KPI,pagebreak?), got {pages}"
            assert "Total Revenue" in text
            assert "Key Metrics" in text
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_1_standalone(self):
        import os
        path, text, pages = self._render(1, "standalone")
        try:
            assert pages == 3
            assert "Key Metrics Overview" in text
            assert "Total Revenue" in text
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_2_merged(self):
        import os
        path, text, _ = self._render(2, "merged")
        try:
            assert "Total Revenue" in text and "Total Units Sold" in text
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_2_standalone(self):
        import os
        path, text, _ = self._render(2, "standalone")
        try:
            assert "Total Revenue" in text and "Total Units Sold" in text
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_4_merged(self):
        import os
        path, text, _ = self._render(4, "merged")
        try:
            for name in ["Total Revenue", "Total Units Sold", "Total Clicks", "Total Profit"]:
                assert name in text, f"missing {name}"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_4_standalone(self):
        import os
        path, text, _ = self._render(4, "standalone")
        try:
            for name in ["Total Revenue", "Total Units Sold", "Total Clicks", "Total Profit"]:
                assert name in text
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_5_merged(self):
        import os
        path, text, _ = self._render(5, "merged")
        try:
            for name in ["Total Revenue", "Total Units Sold", "Total Clicks", "Total Profit", "Total Cost"]:
                assert name in text
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_5_standalone(self):
        import os
        path, text, _ = self._render(5, "standalone")
        try:
            for name in ["Total Revenue", "Total Units Sold", "Total Clicks", "Total Profit", "Total Cost"]:
                assert name in text
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_kpi_grid_helper_deduplicated_and_n1_centered(self):
        """Helper is single source and n==1 card width equals table cell width (no clipping)."""
        from app.services.pdf_service import _build_kpi_grid_flowables
        kpis = [{"name": "Total Revenue", "value": "$14.5K", "trend_pct": 90.0, "trend_label": "change"}]
        flow = _build_kpi_grid_flowables(kpis, "#6366F1", content_width=451.28)
        assert len(flow) == 1, f"n=1 should produce 1 Table, got {len(flow)}"
        table = flow[0]
        # Table colWidths should be single_w ≈ 270, and inner card width must match
        # inspect the one _KPICard inside
        from app.services.pdf_service import _KPICard
        card = table._cellvalues[0][0]  # type: ignore
        assert isinstance(card, _KPICard)
        assert card.width == min(451.28 * 0.60, 300), f"n=1 card width should be single_w, got {card.width}"
        assert table._argW[0] == card.width, "Table cell width must equal card width for n==1 (no overflow)"

    def test_kpi_grid_helper_row_counts(self):
        from app.services.pdf_service import _build_kpi_grid_flowables
        def n_flow(n):
            kpis = [{"name": f"K{i}", "value": "1K", "trend_pct": 1, "trend_label": "change"} for i in range(n)]
            return _build_kpi_grid_flowables(kpis, "#6366F1", 451.28)
        # n=2 → 1 row table
        assert len([f for f in n_flow(2) if hasattr(f, '_cellvalues')]) == 1
        # n=4 → 2 rows + 1 spacer = 3 flowables
        assert len(n_flow(4)) == 3
        # n=5 → 2 rows (3+2) + 1 spacer = 3 flowables
        assert len(n_flow(5)) == 3