"""
A1 — `select_charts_with_ai` covering tests.

Spec (docs/03_ADD for chart selection): the AI returns candidate chart specs;
rules filter out unknown columns / unsupported types; any failure falls back
to None so the caller uses rule-based selection.
"""

import json
import pytest
import pandas as pd
from unittest.mock import patch


def _df():
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=6, freq="D"),
        "Region": ["North", "South", "East", "West", "Central", "North"],
        "Revenue": [1000.0, 1200.0, 900.0, 1500.0, 1100.0, 800.0],
    })


def _ai(return_value):
    return patch("app.services.ai_service._call_ai", return_value=return_value)


class TestSelectChartsWithAI:

    def test_returns_valid_specs(self):
        from app.services.chart_service import select_charts_with_ai

        specs = [
            {"x": "Date", "y": "Revenue", "type": "line", "title": "Revenue Over Time"},
            {"x": "Region", "y": "Revenue", "type": "bar", "title": "Revenue by Region"},
        ]
        with _ai(json.dumps(specs)):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert result == specs

    def test_parses_markdown_fenced_json(self):
        from app.services.chart_service import select_charts_with_ai

        specs = [{"x": "Date", "y": "Revenue", "type": "line", "title": "Trend"}]
        raw = "```json\n" + json.dumps(specs) + "\n```"
        with _ai(raw):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert result == specs

    def test_respects_max_charts_cap(self):
        from app.services.chart_service import select_charts_with_ai

        specs = [
            {"x": "Date", "y": "Revenue", "type": "line", "title": f"T{i}"}
            for i in range(5)
        ]
        with _ai(json.dumps(specs)):
            result = select_charts_with_ai(_df(), {}, "gemini", "key", max_charts=3)

        assert len(result) == 3

    def test_filters_unknown_x_column(self):
        from app.services.chart_service import select_charts_with_ai

        specs = [
            {"x": "Bogus", "y": "Revenue", "type": "line", "title": "Bad x"},
            {"x": "Date", "y": "Revenue", "type": "line", "title": "Good"},
        ]
        with _ai(json.dumps(specs)):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert len(result) == 1
        assert result[0]["title"] == "Good"

    def test_filters_unknown_y_column(self):
        from app.services.chart_service import select_charts_with_ai

        specs = [
            {"x": "Date", "y": "Nope", "type": "line", "title": "Bad y"},
            {"x": "Date", "y": "Revenue", "type": "line", "title": "Good"},
        ]
        with _ai(json.dumps(specs)):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert len(result) == 1
        assert result[0]["title"] == "Good"

    def test_filters_unsupported_type(self):
        from app.services.chart_service import select_charts_with_ai

        specs = [
            {"x": "Date", "y": "Revenue", "type": "radar", "title": "Bad type"},
            {"x": "Date", "y": "Revenue", "type": "line", "title": "Good"},
        ]
        with _ai(json.dumps(specs)):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert len(result) == 1
        assert result[0]["title"] == "Good"

    def test_skips_non_dict_spec_entries(self):
        from app.services.chart_service import select_charts_with_ai

        specs = ["garbage", {"x": "Date", "y": "Revenue", "type": "line", "title": "Good"}]
        with _ai(json.dumps(specs)):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert len(result) == 1

    def test_all_invalid_falls_back_to_none(self):
        from app.services.chart_service import select_charts_with_ai

        specs = [{"x": "Bogus", "y": "Nope", "type": "radar", "title": "All bad"}]
        with _ai(json.dumps(specs)):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert result is None

    def test_non_list_response_returns_none(self):
        from app.services.chart_service import select_charts_with_ai

        with _ai(json.dumps({"x": "Date"})):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert result is None

    def test_invalid_json_returns_none(self):
        from app.services.chart_service import select_charts_with_ai

        with _ai("this is not json"):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert result is None

    def test_ai_exception_returns_none(self):
        from app.services.chart_service import select_charts_with_ai

        with patch("app.services.ai_service._call_ai", side_effect=Exception("provider down")):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert result is None

    def test_builds_column_metadata_pool(self):
        """Exercises the per-column dtype detection (date/numeric/categorical)."""
        from app.services.chart_service import select_charts_with_ai

        captured = {}

        def fake_call_ai(provider, prompt, system, api_key, timeout=20):
            captured["prompt"] = prompt
            return "[]"

        with patch("app.services.ai_service._call_ai", side_effect=fake_call_ai):
            result = select_charts_with_ai(_df(), {}, "gemini", "key")

        assert result is None  # empty array → 0 valid
        prompt = captured["prompt"]
        assert "- Date: date" in prompt
        assert "- Region: categorical" in prompt
        assert "- Revenue: numeric" in prompt
        assert "Date,Region,Revenue" in prompt  # sample CSV header present