"""Verify the status endpoint returns real step values, not the fake loop."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch
from fastapi import HTTPException


class _Row(dict):
    pass


def _mock_db(rows: list):
    class FakeResult:
        def mappings(self):
            class FakeMappings:
                def first(self):
                    return rows[0] if rows else None
            return FakeMappings()
    class FakeDB:
        async def execute(self, *a, **kw):
            return FakeResult()
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            pass
    return FakeDB()


class TestStatusStepLookup:
    """The status endpoint should return real current_step from the DB row,
    not always the last entry in step_map."""

    @pytest.mark.asyncio
    async def test_status_returns_data_step(self):
        from app.api.routes.reports import get_report_status

        report = _Row({
            "id": "r1",
            "user_id": "u1",
            "status": "processing",
            "current_step": "data",
            "config": '{"sections": ["executive_summary", "charts", "data_table"]}',
            "pdf_url": None,
            "generation_time_seconds": None,
            "error_message": None,
        })

        class FakeUser:
            id = "u1"

        result = await get_report_status("r1", current_user=FakeUser(), db=_mock_db([report]))
        assert result["data"]["status"] == "processing"
        assert result["data"]["current_step"] == "Parsing data..."
        assert result["data"]["progress_percent"] == 20

    @pytest.mark.asyncio
    async def test_status_returns_charts_step(self):
        from app.api.routes.reports import get_report_status

        report = _Row({
            "id": "r2",
            "user_id": "u1",
            "status": "processing",
            "current_step": "charts",
            "config": '{"sections": ["charts"]}',
            "pdf_url": None,
            "generation_time_seconds": None,
            "error_message": None,
        })

        class FakeUser:
            id = "u1"

        result = await get_report_status("r2", current_user=FakeUser(), db=_mock_db([report]))
        assert result["data"]["current_step"] == "Generating charts..."
        assert result["data"]["progress_percent"] == 45
        assert "ai_insights" not in result["data"]["steps_completed"]

    @pytest.mark.asyncio
    async def test_status_returns_pdf_step(self):
        from app.api.routes.reports import get_report_status

        report = _Row({
            "id": "r3",
            "user_id": "u1",
            "status": "processing",
            "current_step": "pdf",
            "config": '{"sections": ["charts", "data_table"]}',
            "pdf_url": None,
            "generation_time_seconds": None,
            "error_message": None,
        })

        class FakeUser:
            id = "u1"

        result = await get_report_status("r3", current_user=FakeUser(), db=_mock_db([report]))
        assert result["data"]["current_step"] == "Building PDF..."
        assert result["data"]["progress_percent"] == 85

    @pytest.mark.asyncio
    async def test_status_falls_back_to_defaults_for_empty_step(self):
        from app.api.routes.reports import get_report_status

        report = _Row({
            "id": "r4",
            "user_id": "u1",
            "status": "processing",
            "current_step": None,
            "config": '{"sections": ["charts"]}',
            "pdf_url": None,
            "generation_time_seconds": None,
            "error_message": None,
        })

        class FakeUser:
            id = "u1"

        result = await get_report_status("r4", current_user=FakeUser(), db=_mock_db([report]))
        assert result["data"]["current_step"] == "Initializing..."
        assert result["data"]["progress_percent"] == 10

    @pytest.mark.asyncio
    async def test_status_falls_back_to_defaults_for_unrecognized_step(self):
        from app.api.routes.reports import get_report_status

        report = _Row({
            "id": "r5",
            "user_id": "u1",
            "status": "processing",
            "current_step": "parsing",
            "config": '{"sections": []}',
            "pdf_url": None,
            "generation_time_seconds": None,
            "error_message": None,
        })

        class FakeUser:
            id = "u1"

        result = await get_report_status("r5", current_user=FakeUser(), db=_mock_db([report]))
        assert result["data"]["current_step"] == "Initializing..."
        assert result["data"]["progress_percent"] == 10

    @pytest.mark.asyncio
    async def test_completed_status_still_works(self):
        from app.api.routes.reports import get_report_status

        report = _Row({
            "id": "r6",
            "user_id": "u1",
            "status": "completed",
            "current_step": None,
            "config": "{}",
            "pdf_url": "reports/u1/r6/report.pdf",
            "generation_time_seconds": 12.5,
            "error_message": None,
        })

        class FakeUser:
            id = "u1"

        with patch("app.api.routes.reports._generate_signed_url", return_value="https://signed.url"):
            result = await get_report_status("r6", current_user=FakeUser(), db=_mock_db([report]))
        assert result["data"]["status"] == "completed"
        assert result["data"]["progress_percent"] == 100
        assert result["data"]["generation_time_seconds"] == 12.5

    @pytest.mark.asyncio
    async def test_failed_status_still_works(self):
        from app.api.routes.reports import get_report_status

        report = _Row({
            "id": "r7",
            "user_id": "u1",
            "status": "failed",
            "current_step": None,
            "config": "{}",
            "pdf_url": None,
            "generation_time_seconds": None,
            "error_message": "Something went wrong",
        })

        class FakeUser:
            id = "u1"

        result = await get_report_status("r7", current_user=FakeUser(), db=_mock_db([report]))
        assert result["data"]["status"] == "failed"
        assert "Something went wrong" in result["data"]["error_message"]


class TestUpdateStatusPersistsStep:

    @pytest.mark.asyncio
    async def test_step_is_included_in_sql(self):
        from app.services.report_service import update_status

        executed_sql = []

        class FakeSession:
            async def execute(self, sql, params):
                executed_sql.append((str(sql), dict(params)))
            async def commit(self):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                pass

        with patch("app.services.report_service.AsyncSessionLocal", return_value=FakeSession()):
            await update_status("r1", "processing", step="charts")

        assert len(executed_sql) == 1
        sql_text = executed_sql[0][0]
        params = executed_sql[0][1]

        assert "current_step" in sql_text
        assert params.get("step") == "charts"

    @pytest.mark.asyncio
    async def test_step_not_persisted_when_not_provided(self):
        from app.services.report_service import update_status

        executed_sql = []

        class FakeSession:
            async def execute(self, sql, params):
                executed_sql.append((str(sql), dict(params)))
            async def commit(self):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                pass

        with patch("app.services.report_service.AsyncSessionLocal", return_value=FakeSession()):
            await update_status("r1", "failed", error_message="err")

        assert len(executed_sql) == 1
        sql_text = executed_sql[0][0]
        assert "error_message" in sql_text
        assert "current_step" not in sql_text
