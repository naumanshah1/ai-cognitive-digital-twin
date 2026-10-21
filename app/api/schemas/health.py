"""Health and readiness response schemas."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str = Field("ok", description="Overall liveness status")
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(..., description="Service version")


class ReadinessComponent(BaseModel):
    """Component-level readiness state."""

    status: str = Field(..., description="State of component: ready, degraded, or unreachable")
    latency_ms: Optional[float] = Field(None, description="Check probe latency in milliseconds")
    message: Optional[str] = Field(None, description="Safe status message")


class ReadinessResponse(BaseModel):
    """Readiness probe response distinguishing system liveness from operational readiness."""

    status: str = Field(..., description="Overall readiness: ready or unready")
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(..., description="Service version")
    components: Dict[str, ReadinessComponent] = Field(
        ..., description="Subsystem readiness reports (e.g. database, models)"
    )
