"""Tests for agent execution endpoint."""

from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine

from app.agent.agent import CognitiveTwinAgent
from app.agent.models import AgentResponse, ExecutionStatus, VerificationFindings
from app.agent.providers import MockLLMProvider
from app.api.dependencies import rate_limiter
from app.db.base import Base
from app.db.session import create_app_engine, set_engine, reset_engine
from app.main import app
from app.services.agent_service import agent_service

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_isolated_db_and_mock_agent():
    engine = create_app_engine("sqlite:///:memory:")
    set_engine(engine)
    Base.metadata.create_all(engine)
    rate_limiter.history.clear()

    # Configure agent_service with mock provider for deterministic offline tests
    mock_provider = MockLLMProvider()
    mock_agent = CognitiveTwinAgent(provider=mock_provider)
    agent_service._agent = mock_agent

    yield

    agent_service._agent = None
    reset_engine()


def test_valid_agent_request_returns_structured_response():
    response = client.post(
        "/api/v1/agent/run",
        headers={"Authorization": "Bearer dev-synthetic-00"},
        json={
            "goal": "Summarize my recent behavioral patterns and focus duration.",
            "target_user_id": "synthetic_user_00",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "synthetic_user_00"
    assert data["status"] == "COMPLETED"
    assert data["provider"] == "mock"
    assert "findings" in data
    assert "recommendations" in data
    assert "verification" in data
    assert data["verification"]["is_verified"] is True
    assert "disclaimer" in data
    assert "experimental research twin" in data["disclaimer"]


def test_agent_request_validation_error_on_short_goal():
    response = client.post(
        "/api/v1/agent/run",
        headers={"Authorization": "Bearer dev-synthetic-00"},
        json={"goal": "a"},  # min_length=3
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "validation_errors" in data["details"]


def test_agent_request_with_invalid_simulation_params():
    # Physically impossible focus duration > 24h
    response = client.post(
        "/api/v1/agent/run",
        headers={"Authorization": "Bearer dev-synthetic-00"},
        json={
            "goal": "Simulate focus duration",
            "simulation_params": {"focus_duration_hours": 35.0},
        },
    )
    assert response.status_code == 200
    data = response.json()
    # The agent catches validation error in policy / executor and reports safe error
    assert data["verification"]["is_verified"] is True


def test_agent_request_handles_provider_failure_gracefully():
    with patch.object(
        CognitiveTwinAgent,
        "run",
        side_effect=RuntimeError("Simulated LLM network timeout"),
    ):
        response = client.post(
            "/api/v1/agent/run",
            headers={"Authorization": "Bearer dev-synthetic-00"},
            json={"goal": "Summarize my behavior"},
        )
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"
        # Verify no traceback or secrets leaked
        assert "RuntimeError" not in data["message"]
        assert "Simulated LLM" not in data["message"]
