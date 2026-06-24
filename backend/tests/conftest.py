import os
import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("MASTER_ENCRYPTION_KEY", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", "")


@pytest.fixture(scope="session")
def app():
    from app.main import app
    return app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
