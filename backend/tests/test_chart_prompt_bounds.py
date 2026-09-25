"""Regression bounds for the AI chart-selection prompt (chart_service).

Background: the 5-row CSV sample embeds raw cell text verbatim. On wide
text-heavy datasets (~800-char cells x 12 text columns) the prompt measured
11.6K tokens — past several providers' input caps. String cells are now
truncated to MAX_SAMPLE_CELL_CHARS (200) before to_csv.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
for _k, _v in {
    "SUPABASE_URL": "https://dummy.supabase.co",
    "SUPABASE_SERVICE_KEY": "dummy",
    "SUPABASE_JWT_SECRET": "dummy",
    "SECRET_KEY": "dummy",
}.items():
    os.environ.setdefault(_k, _v)

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch


def _text_heavy_df(n_rows=200, n_text_cols=12, cell_chars=800):
    rng = np.random.default_rng(11)
    essay = ("The customer expressed significant satisfaction with the quarterly deliverables "
             "and requested further clarification regarding implementation timelines. " * 8)[:cell_chars]
    data = {
        "month": pd.date_range("2024-01-01", periods=n_rows, freq="D").strftime("%Y-%m-%d"),
        "revenue_usd": np.round(rng.normal(10000, 2500, n_rows), 2),
        "orders": rng.integers(200, 500, n_rows),
    }
    for i in range(n_text_cols):
        data[f"survey_q{i}"] = [essay + f" respondent#{k}" for k in range(n_rows)]
    df = pd.DataFrame(data)
    df["month"] = pd.to_datetime(df["month"])
    return df


ESSAY = ("The customer expressed significant satisfaction with the quarterly deliverables "
         "and requested further clarification regarding implementation timelines. " * 8)[:800]


def _capture_chart_prompt(df, max_charts=3, y_col="revenue_usd"):
    from app.services import ai_service, chart_service
    captured = {}

    def fake(provider, prompt, system, api_key, timeout=20):
        captured["prompt"] = prompt
        captured["system"] = system
        return f'[{{"x": "month", "y": "{y_col}", "type": "line", "title": "T"}}]'

    with patch.object(ai_service, "_call_ai", side_effect=fake):
        out = chart_service.select_charts_with_ai(
            df=df, config={}, provider="groq", api_key="x", max_charts=max_charts,
        )
    return out, captured["prompt"], captured["system"]


class TestChartSampleTruncation:
    def test_long_cells_truncated_not_verbatim(self):
        from app.services.chart_service import MAX_SAMPLE_CELL_CHARS
        assert MAX_SAMPLE_CELL_CHARS == 200
        _, prompt, _ = _capture_chart_prompt(_text_heavy_df())
        assert ESSAY not in prompt  # full 800-char cell never appears
        assert ESSAY[:200].rstrip()[:100] in prompt  # truncated gist does

    def test_pathological_prompt_under_token_ceiling(self):
        """Concrete ceiling on the measured pathological case (12 text cols,
        ~800-char cells): full prompt must stay under 5,000 tokens — 60%
        margin under an 8K provider cap. Measured 3,436 after truncation
        (was 11,643 untruncated).

        tiktoken is asserted when importable; the char bound below always
        runs in CI as a tripwire (untruncated measured 54K chars).
        """
        _, prompt, system = _capture_chart_prompt(_text_heavy_df())
        full = prompt + system
        assert len(full) <= 30000, f"prompt chars {len(full)} exceed 30K tripwire"
        tiktoken = pytest.importorskip("tiktoken", reason="tiktoken not installed in CI")
        enc = tiktoken.get_encoding("cl100k_base")
        assert len(enc.encode(full)) < 5000

    def test_short_cells_untouched_and_parsing_intact(self):
        out, prompt, _ = _capture_chart_prompt(_text_heavy_df(n_rows=10, n_text_cols=1, cell_chars=40))
        assert "respondent#3" in prompt  # short cells survive verbatim
        assert out == [{"x": "month", "y": "revenue_usd", "type": "line", "title": "T"}]

    def test_numeric_only_prompt_unchanged_shape(self):
        rng = np.random.default_rng(3)
        df = pd.DataFrame({
            "month": pd.date_range("2024-01-01", periods=30, freq="D"),
            "revenue": np.round(rng.normal(5000, 500, 30), 2),
        })
        out, prompt, _ = _capture_chart_prompt(df, y_col="revenue")
        assert "revenue" in prompt
        assert out == [{"x": "month", "y": "revenue", "type": "line", "title": "T"}]
