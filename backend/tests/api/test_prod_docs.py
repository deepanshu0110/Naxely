import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import importlib
import pytest
from unittest.mock import patch


def _reload_app(environment, dsn):
    import app.main as main_module
    from app.core.config import settings
    with patch.object(settings, "ENVIRONMENT", environment), patch.object(
        settings, "SENTRY_DSN", dsn
    ):
        importlib.reload(main_module)
    return main_module.app


class TestProdDocsDisabled:
    def test_docs_redoc_openapi_return_404_in_production(self):
        from fastapi.testclient import TestClient

        app = _reload_app("production", "https://example@sentry.io/1")
        with TestClient(app, raise_server_exceptions=False) as c:
            assert c.get("/docs").status_code == 404
            assert c.get("/redoc").status_code == 404
            assert c.get("/openapi.json").status_code == 404

    def test_openapi_available_in_development(self):
        from fastapi.testclient import TestClient

        app = _reload_app("development", "")
        with TestClient(app, raise_server_exceptions=False) as c:
            assert c.get("/openapi.json").status_code == 200
