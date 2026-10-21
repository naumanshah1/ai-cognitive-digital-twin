"""Tests for health and readiness endpoints."""

from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine

from app.db.base import Base
from app.db.session import create_app_engine, set_engine, reset_engine
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_isolated_db():
    engine = create_app_engine("sqlite:///:memory:")
    set_engine(engine)
    Base.metadata.create_all(engine)
    yield
    reset_engine()


def test_liveness_endpoint_returns_ok_and_version():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert data["version"] == "0.1.0"


def test_readiness_endpoint_when_db_healthy():
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["version"] == "0.1.0"
    assert "database" in data["components"]
    assert data["components"]["database"]["status"] == "ready"
    assert data["components"]["ml_pipeline"]["status"] == "ready"


def test_readiness_endpoint_when_db_unreachable_returns_503_and_no_secrets():
    # Simulate DB disconnection
    with patch("app.api.routes.health.check_db_readiness", return_value=(False, "database connection error (OperationalError)", 12.3)):
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unready"
        db_component = data["components"]["database"]
        assert db_component["status"] == "unreachable"
        # Verify no credentials or SQL connection strings are present
        assert "postgres" not in str(data)
        assert "password" not in str(data)
        assert "change_me" not in str(data)
