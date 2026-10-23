"""Regression tests for CORS preflight, dev persona tokens, and readiness contracts."""

from fastapi.testclient import TestClient
import pytest

from app.db.base import Base
from app.db.session import create_app_engine, reset_engine, set_engine
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_isolated_db():
    engine = create_app_engine("sqlite:///:memory:")
    set_engine(engine)
    Base.metadata.create_all(engine)
    yield
    reset_engine()


def test_cors_preflight_for_localhost_5173():
    """Verify CORS preflight succeeds for frontend origin http://localhost:5173."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "GET" in response.headers.get("access-control-allow-methods", "")
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_for_127_0_0_1_5173():
    """Verify CORS preflight succeeds for frontend origin http://127.0.0.1:5173."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


def test_cors_preflight_with_authorization_headers():
    """Verify CORS preflight accepts Authorization header for authenticated endpoints."""
    response = client.options(
        "/api/v1/users/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "authorization" in response.headers.get("access-control-allow-headers", "").lower()


def test_cors_preflight_rejects_unauthorized_origins():
    """Verify CORS preflight rejects origins not on the explicit whitelist."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://untrusted-third-party.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "Disallowed CORS origin" in response.text


def test_persona_switcher_tokens_and_roles():
    """Verify development persona switcher tokens map correctly to expected users and roles."""
    # Synthetic User 00
    res0 = client.get("/api/v1/users/me", headers={"Authorization": "Bearer dev-synthetic-00"})
    assert res0.status_code == 200
    assert res0.json()["id"] == "synthetic_user_00"
    assert "user" in res0.json()["roles"]

    # Synthetic User 01
    res1 = client.get("/api/v1/users/me", headers={"Authorization": "Bearer dev-synthetic-01"})
    assert res1.status_code == 200
    assert res1.json()["id"] == "synthetic_user_01"
    assert "user" in res1.json()["roles"]

    # Admin Researcher
    res_admin = client.get("/api/v1/users/me", headers={"Authorization": "Bearer dev-admin-token"})
    assert res_admin.status_code == 200
    assert "admin" in res_admin.json()["roles"]
    assert "*" in res_admin.json()["authorized_scopes"]

    # Invalid / Unauthorized Token
    res_bad = client.get("/api/v1/users/me", headers={"Authorization": "Bearer unauthorized-token"})
    assert res_bad.status_code == 401


def test_readiness_endpoint_component_contract():
    """Verify /health/ready returns database, ml_pipeline, and models components."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data["components"]
    assert "ml_pipeline" in data["components"]
    assert "models" in data["components"]
    assert data["components"]["database"]["status"] == "ready"
    assert data["components"]["ml_pipeline"]["status"] == "ready"
    assert data["components"]["models"]["status"] == "ready"
