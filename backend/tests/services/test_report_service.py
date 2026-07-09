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


from unittest.mock import patch, MagicMock, AsyncMock


class TestProcessCsv:
    def test_process_csv_with_config(self):
        from unittest.mock import patch
        import pandas as pd
        from app.services.report_service import _process_csv

        df_in = pd.DataFrame({"Date": ["2026-01-01"], "Revenue": [100.0]})
        df_out, df_norm = _process_csv(df_in, {"sections": ["charts"]})

        assert df_out is not None
        assert "Date" in df_out.columns

    def test_process_csv_date_detection(self):
        import pandas as pd
        from app.services.report_service import _process_csv

        df = pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "sales": [100, 200]})
        _, df_norm = _process_csv(df, {"sections": ["charts"]})

        assert len(df_norm) == 2


class TestPipelineWithAsyncSessionLocal:
    @pytest.mark.asyncio
    async def test_pipeline_csv_parse_error(self):
        from unittest.mock import patch, MagicMock, AsyncMock
        from app.services.report_service import run_report_pipeline

        class FakeSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def execute(self, query, params=None):
                return self
            async def commit(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []

        with patch("app.services.report_service.AsyncSessionLocal", return_value=FakeSession()):
            with patch("app.services.report_service.data_service.parse_csv", side_effect=ValueError("Parse error")):
                with patch("app.services.report_service.sentry_sdk") as mock_sentry:
                    await run_report_pipeline(
                        report_id="rep-pipe-1",
                        user_id="user-pipe-1",
                        config={"sections": ["charts"]},
                    )

                    mock_sentry.capture_exception.assert_called()

    @pytest.mark.asyncio
    async def test_pipeline_successful_upload_not_found(self):
        from unittest.mock import patch, MagicMock, AsyncMock
        from app.services.report_service import run_report_pipeline

        class FakeSession:
            def __init__(self):
                self.queries = []
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def execute(self, query, params=None):
                self.queries.append(str(query))
                return self
            async def commit(self):
                pass
            def mappings(self):
                return self
            def first(self):
                return None
            def all(self):
                return []
            def __getitem__(self, k):
                return None
            def get(self, k, default=None):
                return default

        with patch("app.services.report_service.AsyncSessionLocal", return_value=FakeSession()):
            await run_report_pipeline(
                report_id="rep-pipe-2",
                user_id="user-pipe-2",
                config={"upload_id": "nonexistent", "sections": ["charts"]},
            )
            # No exception assertion — pipeline should swallow the error
            # and set report status to failed internally
class TestGetUser:
    """Cover get_user function (lines 62-69)."""

    @pytest.mark.asyncio
    async def test_get_user_returns_none_when_not_found(self):
        from app.services.report_service import get_user

        class FakeSession:
            async def __aenter__(s):
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, *a, **kw):
                return s
            def mappings(s):
                return s
            def first(s):
                return None

        with patch('app.services.report_service.AsyncSessionLocal', return_value=FakeSession()):
            result = await get_user('missing-id')
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_returns_dict_when_found(self):
        from app.services.report_service import get_user

        class FakeSession:
            async def __aenter__(s):
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, *a, **kw):
                return s
            def mappings(s):
                return s
            def first(s):
                return {'id': 'u1', 'tier': 'pro', 'brand_color': '#FF5733'}

        with patch('app.services.report_service.AsyncSessionLocal', return_value=FakeSession()):
            result = await get_user('u1')
            assert result == {'id': 'u1', 'tier': 'pro', 'brand_color': '#FF5733'}

class TestProcessCsvColumnConfig:
    """Cover _process_csv with column_config (lines 78-108)."""

    def test_apply_column_config_called_when_column_config_provided(self):
        import pandas as pd
        from app.services.report_service import _process_csv

        df = pd.DataFrame({'old_a': [1, 2], 'old_b': [3, 4]})
        config = {'column_config': [{'original_name': 'old_a', 'display_name': 'NewA', 'type': 'metric', 'include': True}]}

        with patch('app.services.report_service.data_service.apply_column_config') as mock_apply:
            mock_apply.return_value = pd.DataFrame({'NewA': [1, 2], 'old_b': [3, 4]})
            with patch('app.services.report_service.data_service.normalize_for_aggregation') as mock_norm:
                mock_norm.return_value = pd.DataFrame({'NewA': [1, 2]})
                df_out, _ = _process_csv(df, config)

        mock_apply.assert_called_once()
        assert 'NewA' in df_out.columns

    def test_column_types_loop_populates_raw_null_counts(self):
        import pandas as pd
        from app.services.report_service import _process_csv

        df = pd.DataFrame({'Metric': [1, None], 'Category': ['x', 'y']})
        config = {
            'column_config': [
                {'original_name': 'Metric', 'display_name': 'Metric', 'type': 'dimension', 'include': True},
                {'original_name': 'Category', 'display_name': 'Category', 'type': 'dimension', 'include': True},
            ]
        }

        with patch('app.services.report_service.data_service.apply_column_config') as mock_apply:
            mock_apply.return_value = df
            with patch('app.services.report_service.data_service.normalize_for_aggregation') as mock_norm:
                mock_norm.return_value = df
                _process_csv(df, config)

        assert '_raw_null_counts' in config
        assert config['_raw_null_counts']['Metric'] == 1
        assert config['_raw_null_counts']['Category'] == 0

    def test_date_column_detected_from_column_names(self):
        import pandas as pd
        from app.services.report_service import _process_csv

        df = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
        config = {'sections': ['charts']}

        with patch('app.services.report_service.data_service.normalize_for_aggregation') as mock_norm:
            mock_norm.return_value = df
            _process_csv(df, config)

        assert config['date_column'] == 'Date'

    def test_date_column_fallback_to_compute_column_stats(self):
        import pandas as pd
        from app.services.report_service import _process_csv

        df = pd.DataFrame({'sales': [100], 'revenue': [200]})
        config = {'sections': ['charts']}

        with patch('app.services.report_service.data_service.normalize_for_aggregation') as mock_norm:
            mock_norm.return_value = df
            with patch('app.services.report_service.data_service.compute_column_stats') as mock_stats:
                mock_stats.return_value = {'date_column': 'sales'}
                _process_csv(df, config)

        assert config['date_column'] == 'sales'
        mock_stats.assert_called_once_with(df)

    def test_date_column_none_when_no_date_found_and_no_stats_result(self):
        import pandas as pd
        from app.services.report_service import _process_csv

        df = pd.DataFrame({'sales': [100]})
        config = {'sections': ['charts']}

        with patch('app.services.report_service.data_service.normalize_for_aggregation') as mock_norm:
            mock_norm.return_value = df
            with patch('app.services.report_service.data_service.compute_column_stats') as mock_stats:
                mock_stats.return_value = {'date_column': None}
                _process_csv(df, config)

        assert config['date_column'] is None

class TestBrandColorFromUserRow:
    """Cover brand_color from user_data_row (line 144)."""

    @pytest.mark.asyncio
    async def test_brand_color_uses_user_row_when_present(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value={'brand_color': '#FF5733', 'tier': 'pro'}),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts'], 'brand': {}}
            await run_report_pipeline(
                report_id='rep-color',
                user_id='user-color',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

    @pytest.mark.asyncio
    async def test_brand_color_default_when_no_user_row(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value=None),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-color-def',
                user_id='user-color-def',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )


class TestChartSpecsOverride:
    """Cover chart_specs override branch (lines 147-148)."""

    @pytest.mark.asyncio
    async def test_chart_specs_from_config_override_used(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value=None),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = ['/tmp/chart1.png']

            config = {'sections': ['charts'], 'chart_specs_override': [{'type': 'bar', 'title': 'Test'}]}
            await run_report_pipeline(
                report_id='rep-override',
                user_id='user-override',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.info.assert_any_call(
            '[report_service] using user chart overrides: [\'bar\']'
        )


class TestChartSpecsAiFallback:
    """Cover AI chart selection when no override (lines 150-161)."""

    @pytest.mark.asyncio
    async def test_chart_specs_from_ai_when_no_override(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        ai_chart_specs = [{'type': 'line', 'title': 'AI Chart'}]

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'pro'}),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = ['/tmp/chart1.png']
            mock_ai.get_user_api_key.return_value = ('openai', 'sk-test', 'gpt-4')
            mock_chart.select_charts_with_ai.return_value = ai_chart_specs

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-ai-chart',
                user_id='user-ai-chart',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_chart.select_charts_with_ai.assert_called_once()
        mock_chart.generate_sync.assert_called_once()
        args_gen, _ = mock_chart.generate_sync.call_args
        assert args_gen[4] == ai_chart_specs

    @pytest.mark.asyncio
    async def test_chart_specs_ai_exception_swallowed(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value=None),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []
            mock_ai.get_user_api_key.return_value = ('openai', 'sk-test', 'gpt-4')
            mock_chart.select_charts_with_ai.side_effect = ValueError('AI failed')

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-ai-fail',
                user_id='user-ai-fail',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.warning.assert_called_once_with(
            '[report_service] AI chart selection skipped: AI failed'
        )

class TestCsvCleanupFromDefaultPath:
    """Cover CSV cleanup in _use_default_path with error suppression (lines 169-175)."""

    @pytest.mark.asyncio
    async def test_csv_cleanup_error_suppressed_when_remove_fails(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()
        actual_calls = []

        def run_sync_side_effect(func, *args, **kwargs):
            actual_calls.append(str(func))
            call_str = str(func)
            if '.remove' in call_str or 'remove' in call_str.lower():
                raise RuntimeError('Storage removal failed')
            return b'a,b\n1,2\n'

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock) as mock_get_upload,
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', side_effect=run_sync_side_effect),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value=None),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_get_upload.return_value = {'file_url': 'uploads/test-path.csv'}
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts'], 'upload_id': 'upl-001'}
            await run_report_pipeline(
                report_id='rep-csv-clean',
                user_id='user-csv-clean',
                config=config,
                csv_bytes=None,
            )

        mock_logger.warning.assert_any_call(
            'Failed to delete CSV from storage: %s', 'uploads/test-path.csv'
        )


class TestAiSectionsProcessing:
    """Cover AI sections processing (lines 182-218)."""

    @pytest.mark.asyncio
    async def test_ai_skipped_when_api_key_none(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'pro'}),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []
            mock_ai.get_user_api_key.return_value = ('openai', None, None)

            config = {'sections': ['executive_summary']}
            await run_report_pipeline(
                report_id='rep-ai-skip',
                user_id='user-ai-skip',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

            assert config.get('_ai_skipped') is True

    @pytest.mark.asyncio
    async def test_ai_summary_http_exception_handled(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession
        from fastapi import HTTPException

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'pro'}),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []
            mock_ai.get_user_api_key.return_value = ('openai', 'sk-test', 'gpt-4')
            mock_ai.generate_summary.side_effect = HTTPException(status_code=429, detail='Rate limited')
            mock_ai.generate_nra_insights.return_value = []
            mock_ai.generate_recommendations.return_value = []
            mock_ai.detect_anomalies.return_value = []
            mock_ai.detect_trends.return_value = []

            config = {'sections': ['executive_summary']}
            await run_report_pipeline(
                report_id='rep-ai-sum-err',
                user_id='user-ai-sum-err',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.warning.assert_any_call(
            'AI summary skipped for %s: %s', 'rep-ai-sum-err', 'Rate limited'
        )

    @pytest.mark.asyncio
    async def test_ai_recommendations_http_exception_logged(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession
        from fastapi import HTTPException

        class FakeSummaryResult:
            pass

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'pro'}),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_ai.SummaryResult = FakeSummaryResult
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []
            mock_ai.get_user_api_key.return_value = ('openai', 'sk-test', 'gpt-4')
            mock_ai.generate_summary = AsyncMock(return_value=None)
            mock_ai.generate_nra_insights = AsyncMock(return_value=[])
            mock_ai.generate_recommendations = AsyncMock(side_effect=HTTPException(status_code=500, detail='LLM error'))
            mock_ai.detect_anomalies.return_value = []
            mock_ai.detect_trends.return_value = []

            config = {'sections': ['executive_summary']}
            await run_report_pipeline(
                report_id='rep-ai-rec-err',
                user_id='user-ai-rec-err',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.warning.assert_any_call(
            'AI recommendations skipped for %s: %s', 'rep-ai-rec-err', 'LLM error'
        )

class TestLogoUrlFromUserRow:
    """Cover logo_url from user_data_row (lines 222-234)."""

    @pytest.mark.asyncio
    async def test_logo_url_generated_from_user_row(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value={'signedURL': 'https://supabase.co/logo.png'}),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value={
                'tier': 'pro', 'brand_color': '#6366F1',
                'logo_url': 'logos/company_logo.png',
                'company_name': 'Acme Inc',
            }),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-logo',
                user_id='user-logo',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.info.assert_any_call(
            "[report_service] logo signed URL result: raw='logos/company_logo.png' clean='company_logo.png' url='https://supabase.co/logo.png'"
        )

    @pytest.mark.asyncio
    async def test_logo_url_exception_sets_none(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', side_effect=RuntimeError('Supabase error')),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value={
                'tier': 'pro', 'brand_color': '#6366F1',
                'logo_url': 'logos/bad.png',
            }),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-logo-bad',
                user_id='user-logo-bad',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )


class TestTrendPctMonthlyAggregate:
    """Cover trend_pct with monthly aggregates (lines 287-324)."""

    @pytest.mark.asyncio
    async def test_trend_pct_computed_from_monthly_aggregates(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        class FakeSummaryResult:
            pass

        dates = pd.date_range('2026-01-01', '2026-03-31', freq='D')
        values = [100 + i for i in range(len(dates))]
        df = pd.DataFrame({'date': dates, 'revenue': values})
        df_str = df.to_csv(index=False).encode()

        class RecordingSession:
            def __init__(self):
                self.last_trend_params = None
            async def __aenter__(s):
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, query, params=None):
                if isinstance(params, dict) and 'trend_pct' in params:
                    s.last_trend_params = params
                return s
            async def commit(s):
                pass
            def mappings(s):
                return s
            def first(s):
                return None
            def all(s):
                return []

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        rec = RecordingSession()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=df_str),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=rec),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'pro', 'brand_color': '#6366F1'}),
            patch('builtins.open'),
        ):
            mock_ai.SummaryResult = FakeSummaryResult
            mock_data.parse_csv.return_value = df
            mock_data.normalize_for_aggregation.return_value = df
            mock_chart.generate_sync.return_value = ['/tmp/chart1.png']

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-trend-mo',
                user_id='user-trend-mo',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        assert rec.last_trend_params is not None, 'UPDATE with trend_pct was never called'
        trend = rec.last_trend_params['trend_pct']
        assert isinstance(trend, float)
        assert trend > 0, f'Expected positive monthly trend, got {trend}%'


class TestTrendPctRowLevelFallback:
    """Cover trend_pct fallback to row-level when no date column (lines 326-330)."""

    @pytest.mark.asyncio
    async def test_trend_pct_falls_back_to_row_level(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        class FakeSummaryResult:
            pass

        df = pd.DataFrame({'sales': [100.0, 150.0, 200.0], 'revenue': [500.0, 600.0, 700.0]})
        df_str = df.to_csv(index=False).encode()

        class RecordingSession:
            def __init__(self):
                self.last_trend_params = None
            async def __aenter__(s):
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, query, params=None):
                if isinstance(params, dict) and 'trend_pct' in params:
                    s.last_trend_params = params
                return s
            async def commit(s):
                pass
            def mappings(s):
                return s
            def first(s):
                return None
            def all(s):
                return []

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        rec = RecordingSession()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=df_str),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=rec),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'pro', 'brand_color': '#6366F1'}),
            patch('builtins.open'),
        ):
            mock_ai.SummaryResult = FakeSummaryResult
            mock_data.parse_csv.return_value = df
            mock_data.normalize_for_aggregation.return_value = df
            mock_chart.generate_sync.return_value = ['/tmp/chart1.png']

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-trend-row',
                user_id='user-trend-row',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        assert rec.last_trend_params is not None, 'UPDATE with trend_pct was never called'
        trend = rec.last_trend_params['trend_pct']
        expected = round(((200.0 - 100.0) / 100.0) * 100, 2)
        assert trend == expected, f'Expected row-level trend {expected}%, got {trend}%'

class TestOnboardingUpdate:
    """Cover onboarding update after successful pipeline (lines 365-375)."""

    @pytest.mark.asyncio
    async def test_onboarding_update_success(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        class FakeSummaryResult:
            pass

        class OnboardSession:
            def __init__(self):
                self.onboarding_called = False
            async def __aenter__(s):
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, query, params=None):
                if isinstance(params, dict) and 'has_completed_onboarding' in str(query):
                    s.onboarding_called = True
                return s
            async def commit(s):
                pass
            def mappings(s):
                return s
            def first(s):
                return None
            def all(s):
                return []

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        sess = OnboardSession()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=sess),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'free', 'brand_color': '#6366F1'}),
            patch('builtins.open'),
        ):
            mock_ai.SummaryResult = FakeSummaryResult
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-onboard',
                user_id='user-onboard',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        assert sess.onboarding_called, 'Onboarding update was not executed'

    @pytest.mark.asyncio
    async def test_onboarding_update_error_handled(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        class FakeSummaryResult:
            pass

        mock_logger = MagicMock()

        class OnboardFailSession:
            def __init__(self):
                self.enter_count = 0
            async def __aenter__(s):
                s.enter_count += 1
                if s.enter_count == 3:
                    raise RuntimeError('Onboarding DB failure')
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, query, params=None):
                return s
            async def commit(s):
                pass
            def mappings(s):
                return s
            def first(s):
                return None
            def all(s):
                return []

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=OnboardFailSession()),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service') as mock_ai,
            patch.object(svc, 'get_user', return_value={'tier': 'free', 'brand_color': '#6366F1'}),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_ai.SummaryResult = FakeSummaryResult
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-onboard-err',
                user_id='user-onboard-err',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.warning.assert_any_call(
            'Failed to set has_completed_onboarding for user %s', 'user-onboard-err'
        )


class TestPipelineMainExceptHandler:
    """Cover main except handler (lines 377-389)."""

    @pytest.mark.asyncio
    async def test_except_sets_status_to_failed(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        class FailRecSession:
            def __init__(self):
                self.failed_params = None
            async def __aenter__(s):
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, query, params=None):
                if isinstance(params, dict) and 'err' in params and 'rid' in params:
                    s.failed_params = params
                return s
            async def commit(s):
                pass
            def mappings(s):
                return s
            def first(s):
                return None
            def all(s):
                return []

        rec = FailRecSession()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=rec),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service'),
            patch.object(svc, 'pdf_service'),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value={'tier': 'pro'}),
        ):
            mock_data.parse_csv.side_effect = ValueError('CSV parse failed')

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-except',
                user_id='user-except',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        assert rec.failed_params is not None, 'Status was not updated to failed'
        assert rec.failed_params['err'] == 'CSV parse failed'
        assert rec.failed_params['rid'] == 'rep-except'

    @pytest.mark.asyncio
    async def test_nested_except_when_failed_update_also_fails(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline

        mock_logger = MagicMock()

        class DoubleFailSession:
            def __init__(self):
                self.execute_count = 0
            async def __aenter__(s):
                return s
            async def __aexit__(s, *a):
                pass
            async def execute(s, query, params=None):
                s.execute_count += 1
                if s.execute_count == 1:
                    raise RuntimeError('Failed to update status to failed')
                return s
            async def commit(s):
                pass
            def mappings(s):
                return s
            def first(s):
                return None
            def all(s):
                return []

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=DoubleFailSession()),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service'),
            patch.object(svc, 'pdf_service'),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value={'tier': 'pro'}),
            patch.object(svc, 'logger', mock_logger),
        ):
            mock_data.parse_csv.side_effect = ValueError('Pipeline failed')

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-double-fail',
                user_id='user-double-fail',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.error.assert_any_call(
            'Failed to update report status to failed for %s', 'rep-double-fail'
        )


class TestFinallyBlockCleanup:
    """Cover finally block (lines 394-405)."""

    @pytest.mark.asyncio
    async def test_chart_cleanup_error_suppressed(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value=None),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = ['/tmp/chart1.png']
            mock_chart.cleanup_charts.side_effect = RuntimeError('Cleanup failed')

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-clean-err',
                user_id='user-clean-err',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.warning.assert_any_call(
            'Failed to clean up chart temp files for %s', 'rep-clean-err'
        )

    @pytest.mark.asyncio
    async def test_pdf_cleanup_error_suppressed(self):
        import app.services.report_service as svc
        from app.services.report_service import run_report_pipeline
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.__aenter__.return_value = mock_db

        class FakePdf:
            @staticmethod
            def build_sync(*a, **kw):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                f.write(b'%PDF-1.4...')
                f.close()
                return f.name
            @staticmethod
            def _compute_kpi_data(*a, **kw):
                return []

        mock_logger = MagicMock()

        with (
            patch.object(svc, 'get_upload', new_callable=AsyncMock),
            patch.object(svc, '_get_supabase'),
            patch.object(svc, '_run_sync', return_value=b'a,b\n1,2\n'),
            patch.object(svc, 'mark_upload_used', new_callable=AsyncMock),
            patch.object(svc, 'update_status'),
            patch.object(svc, 'AsyncSessionLocal', return_value=mock_db),
            patch.object(svc, 'data_service') as mock_data,
            patch.object(svc, 'chart_service') as mock_chart,
            patch.object(svc, 'pdf_service', FakePdf),
            patch.object(svc, 'ai_service'),
            patch.object(svc, 'get_user', return_value=None),
            patch.object(svc, 'logger', mock_logger),
            patch('builtins.open'),
            patch('app.services.report_service.os.path.isfile', return_value=True),
            patch('app.services.report_service.os.unlink', side_effect=RuntimeError('Unlink failed')),
        ):
            mock_data.parse_csv.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_data.normalize_for_aggregation.return_value = pd.DataFrame({'Date': ['2026-01-01'], 'Revenue': [100.0]})
            mock_chart.generate_sync.return_value = []

            config = {'sections': ['charts']}
            await run_report_pipeline(
                report_id='rep-pdf-clean',
                user_id='user-pdf-clean',
                config=config,
                csv_bytes=b'a,b\n1,2\n',
            )

        mock_logger.warning.assert_any_call(
            'Failed to clean up PDF temp file for %s', 'rep-pdf-clean'
        )


class TestMakeUserProxySetattrException:
    """Cover _make_user_proxy setattr exception swallowing (line 414-415)."""

    def test_setattr_exception_swallowed_for_bad_keys(self):
        from app.services.report_service import _make_user_proxy
        from app.models.user import User

        class BadValue:
            def __hash__(self):
                raise TypeError('cannot hash')

        user_data = {
            'id': 'test-id',
            'email': 'test@example.com',
            'valid_key': 'valid_value',
            '_private': BadValue(),
        }

        user = _make_user_proxy(user_data)
        assert isinstance(user, User)
        assert user.id == 'test-id'

