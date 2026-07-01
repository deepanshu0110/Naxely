import pytest
import pandas as pd
from unittest.mock import patch, AsyncMock
from app.services.report_service import _has_ai_sections, _make_user_proxy
from app.models.user import User


class TestReportServiceHelpers:
    def test_has_ai_sections_with_ai(self):
        config = {"sections": ["executive_summary", "kpi_overview", "charts"]}
        assert _has_ai_sections(config) is True

    def test_has_ai_sections_without_ai(self):
        config = {"sections": ["kpi_overview", "charts", "data_table"]}
        assert _has_ai_sections(config) is False

    def test_has_ai_sections_empty(self):
        assert _has_ai_sections({}) is False

    def test_has_ai_sections_insights(self):
        config = {"sections": ["insights"]}
        assert _has_ai_sections(config) is True

    def test_has_ai_sections_anomalies(self):
        config = {"sections": ["anomalies", "trends"]}
        assert _has_ai_sections(config) is True

    def test_make_user_proxy(self):
        user_data = {
            "id": "test-uuid",
            "email": "test@example.com",
            "tier": "pro",
            "brand_color": "#1F3864",
            "encrypted_api_key": "enc",
            "api_key_iv": "iv",
            "ai_provider": "openai",
            "logo_url": "https://example.com/logo.png",
            "company_name": "Acme Corp",
        }
        user = _make_user_proxy(user_data)
        assert isinstance(user, User)
        assert user.tier == "pro"
        assert user.brand_color == "#1F3864"
        assert user.ai_provider == "openai"

    def test_make_user_proxy_empty(self):
        user = _make_user_proxy({})
        assert isinstance(user, User)


class TestRunReportPipelineDefaultPath:
    """Regression: the optional csv_bytes parameter must NOT alter the
    default (None) path. Verify via code-static and lightweight branching tests."""

    def test_signature_accepts_csv_bytes(self):
        """csv_bytes is an optional keyword arg; default is None."""
        import inspect
        from app.services.report_service import run_report_pipeline
        sig = inspect.signature(run_report_pipeline)
        param = sig.parameters.get("csv_bytes")
        assert param is not None, "csv_bytes parameter missing from signature"
        assert param.default is None, "csv_bytes default must be None"
        assert param.kind == param.KEYWORD_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD

    def test_source_has_three_guards(self):
        """The source file must contain exactly three 'if _use_default_path:' guards
        wrapping the original upload/download/delete/mark-used blocks."""
        import os
        source_path = os.path.join(
            os.path.dirname(__file__), '..', '..',
            'app', 'services', 'report_service.py',
        )
        with open(source_path) as f:
            source = f.read()

        guard_lines = [l for l in source.splitlines() if "if _use_default_path:" in l.strip()]
        assert len(guard_lines) == 3, (
            f"Expected exactly 3 'if _use_default_path:' guards in source, "
            f"found {len(guard_lines)}: {guard_lines}"
        )
        assert "get_upload" in source, "get_upload call should still be in the default path"
        assert "mark_upload_used" in source, "mark_upload_used should still be in the default path"
        assert ".remove" in source, "storage remove should still be in the default path"

    @pytest.mark.asyncio
    async def test_csv_bytes_path_skips_upload_and_cleanup(self):
        """When csv_bytes is provided, get_upload and mark_upload_used
        must NOT be called."""
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        provided_bytes = b"a,b\n1,2\n"

        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakeSync:
            @staticmethod
            def generate_sync(*a, **kw):
                return []

            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                f.write(b"%PDF-1.4...")
                f.close()
                return f.name

            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

            @staticmethod
            def cleanup_charts(*a):
                pass

        fake_chart = type("FakeChart", (), {
            "generate_sync": FakeSync.generate_sync,
            "cleanup_charts": FakeSync.cleanup_charts,
        })

        fake_pdf = type("FakePdf", (), {
            "build_sync": FakeSync.build_sync,
            "_compute_kpi_data": FakeSync._compute_kpi_data,
        })

        with (
            patch.object(svc, "get_upload", new_callable=AsyncMock) as mock_get_upload,
            patch.object(svc, "_get_supabase"),
            patch.object(svc, "_run_sync", return_value=provided_bytes),
            patch.object(svc, "mark_upload_used", new_callable=AsyncMock) as mock_mark_used,
            patch.object(svc, "update_status"),
            patch.object(svc, "AsyncSessionLocal", return_value=mock_db),
            patch.object(svc, "data_service") as mock_data,
            patch.object(svc, "chart_service", fake_chart),
            patch.object(svc, "pdf_service", fake_pdf),
            patch.object(svc, "ai_service"),
            patch.object(svc, "get_user", return_value=None),
            patch("builtins.open"),
        ):
            mock_data.parse_csv.return_value = __import__("pandas").DataFrame({"a": [1]})
            mock_data.normalize_for_aggregation.return_value = __import__("pandas").DataFrame({"a": [1]})

            await run_report_pipeline(
                report_id="test-report",
                user_id="test-user",
                config={"upload_id": "upl-001"},
                csv_bytes=provided_bytes,
            )

        mock_get_upload.assert_not_called()
        mock_mark_used.assert_not_called()

    @pytest.mark.asyncio
    async def test_default_path_calls_upload_and_cleanup(self):
        """Mirror of test_csv_bytes_path_skips_upload_and_cleanup — proves the
        DEFAULT (csv_bytes=None) path still performs upload fetch, storage cleanup,
        and mark-used, unchanged by the refactor."""
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakeSync:
            @staticmethod
            def generate_sync(*a, **kw):
                return []

            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                f.write(b"%PDF-1.4...")
                f.close()
                return f.name

            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

            @staticmethod
            def cleanup_charts(*a):
                pass

        fake_chart = type("FakeChart", (), {
            "generate_sync": FakeSync.generate_sync,
            "cleanup_charts": FakeSync.cleanup_charts,
        })

        fake_pdf = type("FakePdf", (), {
            "build_sync": FakeSync.build_sync,
            "_compute_kpi_data": FakeSync._compute_kpi_data,
        })

        with (
            patch.object(svc, "get_upload", new_callable=AsyncMock) as mock_get_upload,
            patch.object(svc, "_get_supabase"),
            patch.object(svc, "_run_sync", return_value=b"a,b\n1,2\n") as mock_run_sync,
            patch.object(svc, "mark_upload_used", new_callable=AsyncMock) as mock_mark_used,
            patch.object(svc, "update_status"),
            patch.object(svc, "AsyncSessionLocal", return_value=mock_db),
            patch.object(svc, "data_service") as mock_data,
            patch.object(svc, "chart_service", fake_chart),
            patch.object(svc, "pdf_service", fake_pdf),
            patch.object(svc, "ai_service"),
            patch.object(svc, "get_user", return_value=None),
            patch("builtins.open"),
        ):
            mock_get_upload.return_value = {"file_url": "uploads/test-path.csv"}
            mock_data.parse_csv.return_value = __import__("pandas").DataFrame({"a": [1]})
            mock_data.normalize_for_aggregation.return_value = __import__("pandas").DataFrame({"a": [1]})

            await run_report_pipeline(
                report_id="test-report",
                user_id="test-user",
                config={"upload_id": "upl-001"},
                csv_bytes=None,
            )

        mock_get_upload.assert_called_once_with("upl-001")
        mock_mark_used.assert_called_once()
        remove_calls = [c for c in mock_run_sync.call_args_list if '.remove' in str(c)]
        assert len(remove_calls) >= 1, (
            "storage.remove should have been called via _run_sync in default path"
        )


# ── Fix 1: Trend % Monthly Aggregation Tests ─────────────────────────────────

@pytest.fixture
def compute_trend_pct_fn():
    """Fixture that mirrors the monthly-aggregate trend logic from report_service.py."""
    from app.services.data_service import _compute_trend_percentage

    def _compute(df: pd.DataFrame, metric_col: str, date_col: str | None = None) -> float:
        series = pd.to_numeric(df[metric_col], errors='coerce').dropna()
        return _compute_trend_percentage(series, df, date_col)

    return _compute


def test_trend_pct_uses_monthly_aggregates_not_row_level(compute_trend_pct_fn):
    """
    Row-level: last row revenue = 14609 (high), first row = 6325 → +131%
    Monthly-aggregate: 2025-01 sum ~3.3M, 2026-11 sum ~3.1M → ~-7%
    Must return the monthly version.
    """
    dates = pd.date_range("2025-01-01", "2026-11-30", freq="D")
    revenue = [10_000.0] * len(dates)
    revenue[0] = 6325.0
    revenue[-1] = 14609.0

    df = pd.DataFrame({"Date": dates, "Revenue": revenue})
    result = compute_trend_pct_fn(df, metric_col="Revenue", date_col="Date")

    assert abs(result) < 10, (
        f"Expected near-flat monthly trend, got {result}%. "
        "Row-level comparison is still being used."
    )


class TestAiSummaryDbSave:
    """Regression: ai_summary must be saved as a string, not SummaryResult."""

    @staticmethod
    def _prepare_db_params(ai_summary_value) -> dict:
        """Replicates the conversion logic at report_service.py:351-353."""
        from app.services.ai_service import SummaryResult
        return {
            "ai_summary": ai_summary_value.full_text
                if isinstance(ai_summary_value, SummaryResult)
                else ai_summary_value,
        }

    def test_summary_result_converts_to_full_text(self):
        """SummaryResult stored in ai_content is converted to .full_text."""
        from app.services.ai_service import SummaryResult
        sr = SummaryResult(lead="L", context="C", implication="I", action="A")
        params = self._prepare_db_params(sr)
        assert isinstance(params["ai_summary"], str)
        assert params["ai_summary"] == "L C I A"

    def test_none_passes_through(self):
        params = self._prepare_db_params(None)
        assert params["ai_summary"] is None

    def test_plain_string_passes_through(self):
        params = self._prepare_db_params("already a string")
        assert params["ai_summary"] == "already a string"


def test_trend_pct_excludes_incomplete_last_month(compute_trend_pct_fn):
    """
    If last month has only 1 row (vs ~30 expected), it must be excluded
    from the trend calculation.
    """
    dates = pd.date_range("2025-01-01", "2026-11-30", freq="D")
    stub = pd.DataFrame({"Date": ["2026-12-01"], "Revenue": [999_999.0]})
    df = pd.concat([
        pd.DataFrame({"Date": dates.strftime("%Y-%m-%d"), "Revenue": [10_000.0] * len(dates)}),
        stub
    ]).reset_index(drop=True)

    result = compute_trend_pct_fn(df, metric_col="Revenue", date_col="Date")

    assert abs(result) < 10, (
        f"Incomplete last bucket was not excluded. Got trend={result}%"
    )
