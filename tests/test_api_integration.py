"""End-to-end integration tests for FastAPI, PostgreSQL/SQLite, Alembic, and LangGraph Agent."""

import os
import pathlib
import tempfile
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine

from app.agent.agent import CognitiveTwinAgent
from app.agent.providers import MockLLMProvider
from app.api.dependencies import rate_limiter
from app.db.base import Base
from app.db.session import reset_engine, set_engine
from app.main import app
from app.services.agent_service import agent_service

client = TestClient(app)


@pytest.fixture(scope="module")
def migrated_db():
    """Applies real Alembic migrations to an isolated temporary SQLite database."""
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = tf.name
    tf.close()

    posix_path = pathlib.Path(temp_db_path).as_posix()
    db_url = f"sqlite:///{posix_path}"

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    set_engine(engine)

    mock_provider = MockLLMProvider()
    agent_service._agent = CognitiveTwinAgent(provider=mock_provider)

    yield db_url

    agent_service._agent = None
    reset_engine()
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass


def test_full_end_to_end_system_workflow(migrated_db):
    rate_limiter.history.clear()

    # Step 1: Verify liveness and readiness
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"

    # Step 2: Authenticate and inspect current user profile
    headers = {"Authorization": "Bearer dev-synthetic-00"}
    user_res = client.get("/api/v1/users/me", headers=headers)
    assert user_res.status_code == 200
    profile = user_res.json()
    assert profile["id"] == "synthetic_user_00"

    # Step 3: Execute Agent Request
    run_payload = {
        "goal": "Review behavioral drift and summarize operational recommendations",
        "target_user_id": "synthetic_user_00",
    }
    run_res = client.post("/api/v1/agent/run", headers=headers, json=run_payload)
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] == "COMPLETED"
    assert len(run_data["findings"]) >= 1
    assert "experimental research twin" in run_data["disclaimer"]
    request_id = run_data["request_id"]

    # Step 4: Check history listing
    hist_res = client.get("/api/v1/agent/history", headers=headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total"] >= 1
    item = hist_data["items"][0]
    assert item["request_id"] == request_id
    assert item["status"] == "COMPLETED"

    # Step 5: Check detailed history record
    detail_res = client.get(f"/api/v1/agent/history/{request_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["request_id"] == request_id
    assert len(detail["tools_called"]) >= 1

    # Step 6: Verify cross-user isolation prevents other user from reading record
    other_headers = {"Authorization": "Bearer user:synthetic_user_05"}
    forbidden_res = client.get(f"/api/v1/agent/history/{request_id}", headers=other_headers)
    assert forbidden_res.status_code == 404
