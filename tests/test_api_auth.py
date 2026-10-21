"""Tests for authentication, authorization, and rate limiting."""

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine

from app.agent.agent import CognitiveTwinAgent
from app.agent.providers import MockLLMProvider
from app.api.dependencies import rate_limiter
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import create_app_engine, set_engine, reset_engine
from app.main import app
from app.services.agent_service import agent_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_isolated_db():
    engine = create_app_engine("sqlite:///:memory:")
    set_engine(engine)
    Base.metadata.create_all(engine)
    rate_limiter.history.clear()
    rate_limiter.limit = get_settings().api_rate_limit_per_minute
    mock_provider = MockLLMProvider()
    agent_service._agent = CognitiveTwinAgent(provider=mock_provider)
    yield
    agent_service._agent = None
    rate_limiter.limit = get_settings().api_rate_limit_per_minute
    rate_limiter.history.clear()
    reset_engine()


def test_missing_auth_header_returns_401():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    data = response.json()
    assert "error_code" in data
    assert data["error_code"] == "HTTP_401"


def test_invalid_auth_token_returns_401():
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-unknown-token-12345"},
    )
    assert response.status_code == 401
    assert "Invalid or unrecognized" in response.json()["message"]


def test_valid_auth_token_returns_profile():
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer dev-synthetic-00"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "synthetic_user_00"
    assert "synthetic_user_00" in data["authorized_scopes"]


def test_cross_user_profile_access_denied_returns_403():
    # User 00 attempts to access user 01's profile
    response = client.get(
        "/api/v1/users/synthetic_user_01",
        headers={"Authorization": "Bearer dev-synthetic-00"},
    )
    assert response.status_code == 403
    assert "Forbidden" in response.json()["message"]


def test_cross_user_agent_execution_denied_returns_403():
    # User 00 attempts to run an agent evaluation targeting user 01
    response = client.post(
        "/api/v1/agent/run",
        headers={"Authorization": "Bearer dev-synthetic-00"},
        json={
            "goal": "Summarize user behavioral patterns",
            "target_user_id": "synthetic_user_01",
        },
    )
    assert response.status_code == 403
    assert "Forbidden" in response.json()["message"]


def test_rate_limiter_exceeded_returns_429():
    rate_limiter.limit = 3
    headers = {"Authorization": "Bearer dev-synthetic-00"}

    # Requests 1, 2, 3 succeed
    for _ in range(3):
        res = client.post(
            "/api/v1/agent/run",
            headers=headers,
            json={"goal": "Summarize my behavior"},
        )
        assert res.status_code in (200, 422, 500)

    # Request 4 exceeds rate limit
    res4 = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={"goal": "Summarize my behavior"},
    )
    assert res4.status_code == 429
    assert "Rate limit exceeded" in res4.json()["message"]
