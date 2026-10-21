"""Tests for database lifecycle, connection pooling, and models."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.history import AgentExecutionRecord
from app.db.models.user import User
from app.db.session import (
    check_db_readiness,
    create_app_engine,
    get_db,
    get_session_factory,
    reset_engine,
    set_engine,
)


@pytest.fixture(autouse=True)
def setup_test_engine():
    engine = create_engine("sqlite:///:memory:")
    set_engine(engine)
    Base.metadata.create_all(engine)
    yield
    reset_engine()


def test_user_and_history_models_crud_and_cascade():
    factory = get_session_factory()
    session: Session = factory()

    # 1. Create User
    user = User(
        id="usr_01",
        username="twin_researcher",
        display_name="Twin Researcher",
    )
    session.add(user)
    session.commit()

    # 2. Add execution records
    rec1 = AgentExecutionRecord(
        id="rec_01",
        request_id="req_01",
        user_id="usr_01",
        status="COMPLETED",
        user_goal="Test goal",
        provider="mock",
        model="mock-model",
        execution_mode="llm",
        execution_latency=0.05,
    )
    session.add(rec1)
    session.commit()

    # 3. Query user with relationship
    queried_user = session.execute(select(User).where(User.id == "usr_01")).scalar_one()
    assert len(queried_user.execution_records) == 1
    assert queried_user.execution_records[0].request_id == "req_01"

    # 4. Cascade delete: deleting user deletes related execution records
    session.delete(queried_user)
    session.commit()

    remaining_records = session.execute(select(AgentExecutionRecord)).scalars().all()
    assert len(remaining_records) == 0
    session.close()


def test_get_db_session_rolls_back_on_exception():
    factory = get_session_factory()
    session_gen = get_db()
    session = next(session_gen)

    user = User(id="usr_temp", username="temp", display_name="Temp")
    session.add(user)

    # Simulate an error inside the request context
    with pytest.raises(RuntimeError):
        try:
            raise RuntimeError("Simulation of uncaught handler failure")
        except Exception:
            try:
                session_gen.throw(RuntimeError("Handler failure"))
            except StopIteration:
                pass

    # Verify that the uncommitted user was rolled back
    verify_session = factory()
    res = verify_session.execute(select(User).where(User.id == "usr_temp")).scalar_one_or_none()
    assert res is None
    verify_session.close()


def test_check_db_readiness_reports_latency_and_never_leaks_secrets():
    # Healthy test
    is_ready, msg, latency = check_db_readiness()
    assert is_ready is True
    assert msg == "connected"
    assert latency is not None and latency >= 0.0

    # Unreachable / failing engine test
    failing_engine = create_engine("sqlite:///nonexistent_dir/impossible.db")
    is_ready_fail, msg_fail, latency_fail = check_db_readiness(failing_engine)
    assert is_ready_fail is False
    assert "database connection error" in msg_fail
    assert "password" not in msg_fail
    failing_engine.dispose()
