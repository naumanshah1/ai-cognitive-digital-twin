"""Tests for agent history and audit endpoints."""

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine

from app.agent.agent import CognitiveTwinAgent
from app.agent.providers import MockLLMProvider
from app.api.dependencies import rate_limiter
from app.db.base import Base
from app.db.models.history import AgentExecutionRecord
from app.db.session import create_app_engine, get_session_factory, reset_engine, set_engine
from app.main import app
from app.services.agent_service import agent_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_isolated_db_and_agent():
    engine = create_app_engine("sqlite:///:memory:")
    set_engine(engine)
    Base.metadata.create_all(engine)
    rate_limiter.history.clear()

    mock_provider = MockLLMProvider()
    agent_service._agent = CognitiveTwinAgent(provider=mock_provider)

    yield

    agent_service._agent = None
    reset_engine()


def test_agent_run_persists_history_record():
    # 1. Run agent inquiry
    headers = {"Authorization": "Bearer dev-synthetic-00"}
    run_res = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={"goal": "Summarize my focus patterns"},
    )
    assert run_res.status_code == 200
    req_id = run_res.json()["request_id"]

    # 2. Query history list
    hist_res = client.get("/api/v1/agent/history", headers=headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total"] >= 1
    matching = [item for item in hist_data["items"] if item["request_id"] == req_id]
    assert len(matching) == 1
    assert matching[0]["user_id"] == "synthetic_user_00"
    assert matching[0]["status"] == "COMPLETED"


def test_history_pagination_limit_and_offset():
    session = get_session_factory()()
    # Insert 5 fake records
    for i in range(5):
        rec = AgentExecutionRecord(
            id=f"rec_{i}",
            request_id=f"req_{i}",
            user_id="synthetic_user_00",
            status="COMPLETED",
            user_goal=f"Goal {i}",
            provider="mock",
            model="mock-model",
            execution_mode="llm",
            execution_latency=0.1,
            tools_called=[],
        )
        session.add(rec)
    session.commit()
    session.close()

    headers = {"Authorization": "Bearer dev-synthetic-00"}
    res = client.get("/api/v1/agent/history?limit=2&offset=0", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    res_page2 = client.get("/api/v1/agent/history?limit=2&offset=2", headers=headers)
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert len(data2["items"]) == 2


def test_get_history_detail_and_cross_user_isolation():
    session = get_session_factory()()
    # Record belonging to synthetic_user_01
    rec = AgentExecutionRecord(
        id="rec_user_01",
        request_id="req_user_01",
        user_id="synthetic_user_01",
        status="COMPLETED",
        user_goal="Private goal for user 01",
        provider="mock",
        model="mock-model",
        execution_mode="llm",
        execution_latency=0.2,
        tools_called=[{"tool_name": "get_behavioral_summary", "status": "SUCCESS"}],
    )
    session.add(rec)
    session.commit()
    session.close()

    # User 00 attempts to read User 01's history record
    headers_user_00 = {"Authorization": "Bearer dev-synthetic-00"}
    res = client.get("/api/v1/agent/history/req_user_01", headers=headers_user_00)
    assert res.status_code == 404

    # User 01 reads their own record
    headers_user_01 = {"Authorization": "Bearer user:synthetic_user_01"}
    res_own = client.get("/api/v1/agent/history/req_user_01", headers=headers_user_01)
    assert res_own.status_code == 200
    detail = res_own.json()
    assert detail["request_id"] == "req_user_01"
    assert detail["user_id"] == "synthetic_user_01"
    assert len(detail["tools_called"]) == 1
