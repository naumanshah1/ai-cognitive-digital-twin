"""Unit and integration tests for authentication, JWT lifecycle, RBAC, and admin endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.agent.agent import CognitiveTwinAgent
from app.agent.providers import MockLLMProvider
from app.api.dependencies import rate_limiter
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models.user import User
from app.db.session import create_app_engine, get_db, reset_engine, set_engine
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

    # Seed an admin user and a regular user
    with Session(engine) as session:
        admin_user = User(
            id="admin_01",
            username="admin_corp",
            display_name="Corporate Admin",
            email="admin@cognitivetwin.ai",
            hashed_password=get_password_hash("AdminPass123!"),
            role="admin",
            is_active=True,
        )
        reg_user = User(
            id="user_reg_01",
            username="jane_doe",
            display_name="Jane Doe",
            email="jane@example.com",
            hashed_password=get_password_hash("SecretPass123!"),
            role="user",
            is_active=True,
        )
        session.add(admin_user)
        session.add(reg_user)
        session.commit()

    mock_provider = MockLLMProvider()
    agent_service._agent = CognitiveTwinAgent(provider=mock_provider)
    yield
    agent_service._agent = None
    rate_limiter.limit = get_settings().api_rate_limit_per_minute
    rate_limiter.history.clear()
    reset_engine()


def test_user_registration_success():
    payload = {
        "email": "newuser@example.com",
        "username": "new_user_1",
        "display_name": "New User",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["username"] == "new_user_1"
    assert data["user"]["role"] == "user"


def test_user_registration_duplicate_email_fails():
    payload = {
        "email": "jane@example.com",
        "username": "jane_duplicate",
        "display_name": "Jane Another",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["message"]


def test_user_registration_duplicate_username_fails():
    payload = {
        "email": "other@example.com",
        "username": "jane_doe",
        "display_name": "Other Jane",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already taken" in response.json()["message"]


def test_user_registration_short_password_fails():
    payload = {
        "email": "short@example.com",
        "username": "short_pass",
        "display_name": "Short Pass",
        "password": "short",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_user_login_success():
    payload = {
        "email_or_username": "jane@example.com",
        "password": "SecretPass123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["role"] == "user"
    assert data["user"]["username"] == "jane_doe"


def test_user_login_with_username_success():
    payload = {
        "email_or_username": "jane_doe",
        "password": "SecretPass123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "jane@example.com"


def test_user_login_wrong_password_fails():
    payload = {
        "email_or_username": "jane@example.com",
        "password": "WrongPassword!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["message"]


def test_user_login_nonexistent_user_fails():
    payload = {
        "email_or_username": "ghost@example.com",
        "password": "SecretPass123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["message"]


def test_auth_me_endpoint_with_jwt():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "jane@example.com", "password": "SecretPass123!"},
    )
    token = login_res.json()["token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["username"] == "jane_doe"
    assert user_data["email"] == "jane@example.com"
    assert user_data["role"] == "user"


def test_regular_user_denied_from_admin_endpoints():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "jane@example.com", "password": "SecretPass123!"},
    )
    user_token = login_res.json()["token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Overview endpoint
    res_overview = client.get("/api/v1/admin/overview", headers=user_headers)
    assert res_overview.status_code == 403

    # Users list endpoint
    res_users = client.get("/api/v1/admin/users", headers=user_headers)
    assert res_users.status_code == 403

    # Audit endpoint
    res_audit = client.get("/api/v1/admin/audit", headers=user_headers)
    assert res_audit.status_code == 403

    # Diagnostics endpoint
    res_system = client.get("/api/v1/admin/system", headers=user_headers)
    assert res_system.status_code == 403


def test_admin_user_allowed_on_admin_endpoints():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "admin@cognitivetwin.ai", "password": "AdminPass123!"},
    )
    assert login_res.status_code == 200
    admin_token = login_res.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Overview endpoint
    res_overview = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert res_overview.status_code == 200
    overview_data = res_overview.json()
    assert "total_users" in overview_data
    assert overview_data["total_users"] >= 2
    assert "database_status" in overview_data

    # Users list endpoint
    res_users = client.get("/api/v1/admin/users", headers=admin_headers)
    assert res_users.status_code == 200
    users_data = res_users.json()
    assert users_data["total"] >= 2

    # Audit endpoint
    res_audit = client.get("/api/v1/admin/audit", headers=admin_headers)
    assert res_audit.status_code == 200

    # Diagnostics endpoint
    res_system = client.get("/api/v1/admin/system", headers=admin_headers)
    assert res_system.status_code == 200
    assert "database" in res_system.json()

    # Analytics endpoint
    res_analytics = client.get("/api/v1/admin/analytics", headers=admin_headers)
    assert res_analytics.status_code == 200
    analytics_data = res_analytics.json()
    assert "total_executions" in analytics_data
    assert "tool_usage" in analytics_data
    assert "provider_distribution" in analytics_data

    # Security endpoint
    res_security = client.get("/api/v1/admin/security", headers=admin_headers)
    assert res_security.status_code == 200
    security_data = res_security.json()
    assert "security_posture" in security_data
    assert security_data["admin_accounts_count"] >= 1

    # Configuration endpoint
    res_config = client.get("/api/v1/admin/configuration", headers=admin_headers)
    assert res_config.status_code == 200
    config_data = res_config.json()
    assert "database" in config_data
    assert "llm" in config_data


def test_user_change_password_and_validation():
    # Login as registered test user
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "jane@example.com", "password": "SecretPass123!"},
    )
    assert login_res.status_code == 200
    user_token = login_res.json()["token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Wrong current password fails
    fail_res = client.post(
        "/api/v1/auth/change-password",
        headers=user_headers,
        json={"current_password": "WrongPassword123!", "new_password": "NewSecretPass456!"},
    )
    assert fail_res.status_code == 400

    # Short new password fails validation
    short_res = client.post(
        "/api/v1/auth/change-password",
        headers=user_headers,
        json={"current_password": "SecretPass123!", "new_password": "short"},
    )
    assert short_res.status_code == 422


def test_regular_user_denied_from_all_new_admin_endpoints():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "jane@example.com", "password": "SecretPass123!"},
    )
    assert login_res.status_code == 200
    user_token = login_res.json()["token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    for path in ["/api/v1/admin/analytics", "/api/v1/admin/security", "/api/v1/admin/configuration"]:
        res = client.get(path, headers=user_headers)
        assert res.status_code == 403, f"Expected 403 on {path}, got {res.status_code}"


def test_admin_role_update_and_self_demotion_protection():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "admin@cognitivetwin.ai", "password": "AdminPass123!"},
    )
    assert login_res.status_code == 200
    admin_token = login_res.json()["token"]
    admin_id = login_res.json()["user"]["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Self-demotion must be rejected with 400
    self_demote = client.post(
        f"/api/v1/admin/users/{admin_id}/role",
        headers=admin_headers,
        json={"role": "user"},
    )
    assert self_demote.status_code == 400
    assert "Cannot demote your own administrator account" in self_demote.json().get("message", "")


