"""Administrative API schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.api.schemas.history import HistoryItem
from app.api.schemas.users import UserResponse


class AdminUserItem(UserResponse):
    """User account item in admin user management."""

    email: Optional[str] = Field(None, description="Account email")
    role: str = Field("user", description="Account role (user, admin)")
    execution_count: int = Field(0, description="Total agent executions run by user")


class AdminUserListResponse(BaseModel):
    """Paginated response for user management."""

    total: int = Field(..., description="Total registered accounts")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
    items: List[AdminUserItem] = Field(..., description="User accounts")


class AdminOverviewMetrics(BaseModel):
    """Aggregated operational metrics for administrator dashboard."""

    total_users: int = Field(..., description="Total registered user accounts")
    active_users: int = Field(..., description="Active user accounts")
    total_executions: int = Field(..., description="Total agent inquiries executed")
    completed_executions: int = Field(..., description="Total successful executions")
    failed_executions: int = Field(..., description="Total failed or rejected executions")
    database_status: str = Field(..., description="PostgreSQL operational state")
    database_latency_ms: Optional[float] = Field(None, description="Database ping latency in ms")
    ml_models_status: str = Field(..., description="Cognitive models operational state")
    recent_executions: List[HistoryItem] = Field(default_factory=list, description="Latest system-wide audit records")


class AdminSystemDiagnostics(BaseModel):
    """Internal technical infrastructure diagnostics."""

    app_name: str
    environment: str
    version: str
    database: Dict[str, Any]
    models: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    security: Dict[str, Any]


class AdminAnalyticsResponse(BaseModel):
    """Analytics and model performance operational data."""

    total_executions: int
    completed_executions: int
    failed_executions: int
    success_rate_percent: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    provider_distribution: Dict[str, int]
    tool_usage: Dict[str, int]
    execution_timeline: List[Dict[str, Any]]
    benchmark_baseline_productivity: float = 72.4
    benchmark_baseline_focus_hours: float = 5.2


class AdminSecurityResponse(BaseModel):
    """Security posture and access event data."""

    total_registered_users: int
    admin_accounts_count: int
    regular_accounts_count: int
    active_sessions_count: int
    security_posture: Dict[str, Any]
    recent_access_events: List[Dict[str, Any]]


class AdminConfigurationResponse(BaseModel):
    """Sanitized system and integration configuration."""

    app_name: str
    app_env: str
    app_version: str
    database: Dict[str, Any]
    llm: Dict[str, Any]
    frameworks: Dict[str, Any]
    security_policies: Dict[str, Any]
    database_migrations: Dict[str, Any]


class AdminRoleUpdateRequest(BaseModel):
    """Payload to promote or demote a user's role."""

    role: str = Field(..., pattern="^(user|admin)$", description="Role: 'user' or 'admin'")

