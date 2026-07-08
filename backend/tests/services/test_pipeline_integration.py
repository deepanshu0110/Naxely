import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import pandas as pd
from pathlib import Path

from app.services.data_service import parse_csv
from app.services.chart_service import generate_sync, cleanup_charts


class TestPipelineIntegration:
    def test_csv_bytes_to_pdf_e2e(self):
        from app.services.pdf_service import build_sync

        csv_bytes = b"Date,Revenue,Clicks\n2024-01-01,1000,100\n2024-01-02,1200,110\n2024-01-03,1100,105\n2024-01-04,1300,120\n2024-01-05,1400,130\n2024-01-06,1500,125\n2024-01-07,1600,140\n2024-01-08,1700,150\n2024-01-09,1800,145\n2024-01-10,1900,160\n"

        df = parse_csv(csv_bytes)
        assert len(df) == 10
        assert "Revenue" in df.columns

        report_id = "test-pipeline-e2e"

        config = {
            "upload_id": "upload-fake-123",
            "metric_columns": ["Revenue", "Clicks"],
            "title": "E2E Pipeline Test",
            "sections": ["kpi_overview", "charts", "data_table"],
            "date_column": "Date",
        }

        chart_paths = generate_sync(df, report_id, config)
        assert len(chart_paths) >= 2
        for p, col_name in chart_paths:
            assert os.path.isfile(p)
            assert isinstance(col_name, str)

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
            "company_name": None,
        }
        pdf_config = dict(config)
        pdf_config["report_id"] = report_id

        pdf_path = build_sync(df, chart_paths, ai_content, pdf_config, user_data)
        assert pdf_path is not None
        assert Path(pdf_path).exists()
        assert os.path.getsize(pdf_path) > 1000

        with open(pdf_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

        import fitz
        doc = fitz.open(pdf_path)
        assert len(doc) >= 2
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        assert "Revenue" in full_text
        assert "E2E Pipeline Test" in full_text

        cleanup_charts(report_id)
        try:
            os.unlink(pdf_path)
        except OSError:
            pass

    def test_csv_bytes_to_pdf_free_tier_no_charts(self):
        from app.services.pdf_service import build_sync

        csv_bytes = b"Category,Count\nA,10\nB,20\nC,30\n"

        df = parse_csv(csv_bytes)
        report_id = "test-pipeline-free"

        config = {
            "upload_id": "upload-free-456",
            "metric_columns": ["Count"],
            "title": "Free Tier Pipeline",
            "sections": ["kpi_overview"],
        }

        chart_paths = generate_sync(df, report_id, config)

        ai_content = {"summary": None, "insights": [], "anomalies": [], "trends": []}
        user_data = {
            "brand_color": "#6366F1",
            "tier": "free",
            "logo_url": None,
            "company_name": None,
        }
        pdf_config = dict(config)
        pdf_config["report_id"] = report_id

        pdf_path = build_sync(df, chart_paths, ai_content, pdf_config, user_data)

        with open(pdf_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

        import fitz
        doc = fitz.open(pdf_path)
        assert len(doc) >= 1
        page_text = doc[0].get_text()
        assert "Naxely" in page_text
        doc.close()

        cleanup_charts(report_id)
        try:
            os.unlink(pdf_path)
        except OSError:
            pass
