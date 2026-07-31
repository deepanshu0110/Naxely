"""
A1 — Chart Selection feature (fail-first tests).

Spec (Part A, task):
- preview-charts returns ALL generatable {x, y, type, title} candidates, not just 3.
- Each candidate carries a `recommended` flag (AI/rule-picked subset).
- generate_sync no longer hard-caps at 3: it derives the cap from tier
  (Free=3, Pro=8, Agency=16), following the deps.py tier-check pattern.
- histogram is selectable.
- PPTX export uses chart_specs_override when present instead of re-deriving.
"""

import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.chart_service import generate_sync, cleanup_charts
from app.api.routes.reports import SAMPLE_CSV_PATH


# ── Fixtures ────────────────────────────────────────────────────────────────

def _df():
    """Wide-enough dataframe so every spec pool chart can render."""
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=20, freq="D"),
        "Region": ["North", "South", "East", "West", "Central"] * 4,
        "Service": ["Training", "Audit", "Consulting", "Dashboard Build"] * 5,
        "Revenue": [1000.0 + i * 50.0 for i in range(20)],
        "Hours": [float(i % 9 + 1) for i in range(20)],
    })


def _specs(n):
    """Build n valid chart specs from a renderable pool (16 distinct types)."""
    pool = [
        ("Date", "Revenue", "line"),
        ("Region", "Revenue", "bar"),
        ("Date", "Hours", "line"),
        ("Hours", "Revenue", "scatter"),
        ("Region", "Hours", "bar"),
        ("Revenue", "Revenue", "histogram"),
        ("Service", "Revenue", "bar"),
        ("Region", "Service", "heatmap"),
        ("Date", "Revenue", "area"),
        ("Region", "Revenue", "donut"),
        ("Service", "Hours", "lollipop"),
        ("Region", "Revenue", "box"),
        ("Region", "Hours", "stacked_bar"),
        ("Region", "Revenue", "grouped_bar"),
        ("Date", "Revenue", "combo"),
        ("Service", "Revenue", "treemap"),
    ]
    return [
        {"x": pool[i % len(pool)][0], "y": pool[i % len(pool)][1],
         "type": pool[i % len(pool)][2], "title": f"{pool[i % len(pool)][1]} by {pool[i % len(pool)][0]}"}
        for i in range(n)
    ]


class _SequenceDB:
    """AsyncSession stub returning a fixed sequence of rows."""

    def __init__(self, rows):
        self._rows = list(rows)
        self._i = 0

    async def execute(self, query, params=None):
        result = MagicMock()
        row = self._rows[self._i] if self._i < len(self._rows) else None
        self._i += 1
        if row is not None:
            result.mappings.return_value.first.return_value = row
        else:
            result.mappings.return_value.first.return_value = None
        return result

    async def commit(self):
        pass

    async def rollback(self):
        pass


# ── Tier caps ───────────────────────────────────────────────────────────────

class TestTierCaps:
    def test_chart_cap_for_tier_defaults_to_free(self):
        from app.services.chart_service import chart_cap_for_tier
        assert chart_cap_for_tier(None) == 3
        assert chart_cap_for_tier("") == 3
        assert chart_cap_for_tier("mystery") == 3

    def test_chart_cap_for_tier_free_is_three(self):
        from app.services.chart_service import chart_cap_for_tier
        assert chart_cap_for_tier("free") == 3

    def test_chart_cap_for_tier_pro_is_eight(self):
        from app.services.chart_service import chart_cap_for_tier
        assert chart_cap_for_tier("pro") == 8

    def test_chart_cap_for_tier_agency_is_sixteen(self):
        from app.services.chart_service import chart_cap_for_tier
        assert chart_cap_for_tier("agency") == 16

    def test_generate_sync_pro_allows_eight_charts(self):
        """8 valid specs for a Pro user must produce 8 charts (not truncated to 3)."""
        specs = _specs(8)
        paths = generate_sync(_df(), "test-pro8", {"tier": "pro"}, "#0D7377", specs)
        try:
            assert len(paths) == 8, f"Expected 8 charts for Pro, got {len(paths)}"
            for p, _, _, _ in paths:
                assert p.endswith(".png")
        finally:
            cleanup_charts("test-pro8")

    def test_generate_sync_free_caps_at_three(self):
        specs = _specs(8)
        paths = generate_sync(_df(), "test-free3", {"tier": "free"}, "#0D7377", specs)
        try:
            assert len(paths) == 3, f"Expected 3 charts for Free, got {len(paths)}"
        finally:
            cleanup_charts("test-free3")

    def test_generate_sync_agency_allows_sixteen_charts(self):
        specs = _specs(16)
        paths = generate_sync(_df(), "test-agency16", {"tier": "agency"}, "#0D7377", specs)
        try:
            assert len(paths) == 16, f"Expected 16 charts for Agency, got {len(paths)}"
        finally:
            cleanup_charts("test-agency16")

    def test_generate_sync_default_tier_caps_at_three(self):
        """No tier in config → falls back to Free cap of 3 (backward compatible)."""
        specs = _specs(8)
        paths = generate_sync(_df(), "test-default3", {}, "#0D7377", specs)
        try:
            assert len(paths) == 3, f"Expected 3 charts by default, got {len(paths)}"
        finally:
            cleanup_charts("test-default3")


# ── histogram selectability ─────────────────────────────────────────────────

class TestHistogramSelectable:
    def test_histogram_spec_renders(self):
        specs = [{"x": "Revenue", "y": "Revenue", "type": "histogram", "title": "Revenue Distribution"}]
        paths = generate_sync(_df(), "test-hist", {"tier": "pro"}, "#0D7377", specs)
        try:
            assert len(paths) == 1
            assert "histogram" in paths[0][0]
        finally:
            cleanup_charts("test-hist")


# ── preview-charts returns full candidate list ──────────────────────────────

class TestPreviewCharts:
    async def _call(self, tier="pro"):
        from app.api.routes.reports import preview_charts, PreviewChartsRequest
        from app.models.user import User

        csv_bytes = SAMPLE_CSV_PATH.read_bytes()

        db = _SequenceDB([
            {"id": "upload-preview-1", "file_url": "user-1/upload-preview-1/raw.csv", "user_id": "user-1"},
            {"id": "user-1", "tier": tier},
        ])

        user = User()
        user.id = "user-1"
        user.tier = tier

        with patch("app.api.routes.reports._get_supabase", MagicMock()):
            with patch("app.api.routes.reports._run_sync", new=AsyncMock(return_value=csv_bytes)):
                with patch("app.services.chart_service.select_charts_with_ai", return_value=None):
                    return await preview_charts(
                        body=PreviewChartsRequest(upload_id="upload-preview-1"),
                        current_user=user,
                        db=db,
                    )

    @pytest.mark.asyncio
    async def test_preview_charts_returns_full_candidate_list(self):
        """preview-charts returns every generatable candidate, not just the top 3."""
        resp = await self._call()
        specs = resp["chart_specs"]
        assert len(specs) >= 10, f"Expected a full candidate list, got {len(specs)}"

    @pytest.mark.asyncio
    async def test_preview_charts_marks_recommended_subset(self):
        """Every spec carries a `recommended` flag; AI/rule picks are pre-marked True."""
        specs = (await self._call())["chart_specs"]
        assert all({"x", "y", "type", "title", "recommended"} <= set(s.keys()) for s in specs)

        recommended = [s for s in specs if s["recommended"]]
        not_recommended = [s for s in specs if not s["recommended"]]
        assert len(recommended) >= 3, f"Expected recommended subset, got {len(recommended)}"
        assert len(not_recommended) >= 1, "Full candidate list must include non-recommended charts"

    @pytest.mark.asyncio
    async def test_preview_charts_includes_histogram_and_scatter(self):
        specs = (await self._call())["chart_specs"]
        types = {s["type"] for s in specs}
        assert "histogram" in types, "histogram must be selectable from preview-charts"
        assert "scatter" in types, "scatter must be selectable from preview-charts"


# ── PPTX export honours chart_specs_override ────────────────────────────────

class TestPptxExportOverride:
    @pytest.mark.asyncio
    async def test_pptx_export_passes_chart_specs_override(self):
        from app.api.routes.reports import export_report_pptx
        from app.models.user import User

        csv_bytes = SAMPLE_CSV_PATH.read_bytes()

        specs = [
            {"x": "Date", "y": "Billable Amount", "type": "line", "title": "Billable Amount Over Time"},
            {"x": "Client", "y": "Billable Amount", "type": "bar", "title": "Billable Amount by Client"},
        ]
        report_row = {
            "id": "report-pptx-1",
            "status": "completed",
            "ai_summary": None,
            "ai_insights": [],
            "ai_anomalies": [],
            "config": json.dumps({
                "upload_id": "upload-preview-1",
                "sections": ["charts"],
                "chart_specs_override": specs,
            }),
        }
        user_row = {"id": "user-1", "brand_color": "#6366F1", "company_name": None,
                    "logo_url": None, "tier": "agency"}

        db = _SequenceDB([report_row, user_row])

        user = User()
        user.id = "user-1"
        user.tier = "agency"

        with (
            patch("app.api.routes.reports._get_supabase", MagicMock()),
            patch("app.api.routes.reports._run_sync", new=AsyncMock(return_value=csv_bytes)),
            patch("app.services.report_service.get_upload", new=AsyncMock(return_value={"source_type": "csv"})),
            patch("app.services.pdf_service._compute_kpi_data", return_value=[]),
            patch("app.services.chart_service.generate_sync") as mock_charts,
            patch("app.services.pptx_service.generate_pptx", return_value=b"fake-pptx-bytes"),
        ):
            resp = await export_report_pptx(report_id="report-pptx-1", current_user=user, db=db)

        assert resp.status_code == 200
        assert mock_charts.called, "PPTX export must call generate_sync"
        call_args = mock_charts.call_args.args
        assert len(call_args) >= 5, f"generate_sync must receive chart_specs, got {len(call_args)} args"
        assert call_args[4] == specs, "PPTX export must pass chart_specs_override through"
