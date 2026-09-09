import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["AWS_MODE"] = "mock"
os.environ["LOCAL_STORAGE_ROOT"] = "./test_storage"
os.environ["JWT_SECRET"] = "test-secret"

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

get_settings.cache_clear()

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    storage_dir = Path("./test_storage")
    if storage_dir.exists():
        shutil.rmtree(storage_dir, ignore_errors=True)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "test@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
