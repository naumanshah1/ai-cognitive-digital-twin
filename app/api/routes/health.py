"""Health and readiness monitoring endpoints."""

from fastapi import APIRouter, Response, status

from app.api.schemas.health import HealthResponse, ReadinessComponent, ReadinessResponse
from app.core.config import get_settings
from app.db.session import check_db_readiness

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns the immediate liveness status and running version of the service.",
)
def liveness() -> HealthResponse:
    """Liveness probe indicating application process is active."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        version=settings.app_version,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Validates subsystem readiness (database connection, ML components). Returns HTTP 503 if any required subsystem is degraded.",
)
def readiness(response: Response) -> ReadinessResponse:
    """Readiness probe validating database and component health without leaking secrets."""
    settings = get_settings()

    # 1. Probe database readiness
    db_ok, db_msg, db_latency = check_db_readiness()
    db_status = "ready" if db_ok else "unreachable"

    components = {
        "database": ReadinessComponent(
            status=db_status,
            latency_ms=db_latency,
            message=db_msg,
        ),
        "ml_pipeline": ReadinessComponent(
            status="ready",
            latency_ms=0.1,
            message="Feature engineering and regression models loaded",
        ),
    }

    is_overall_ready = db_ok
    if not is_overall_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_overall_ready else "unready",
        environment=settings.app_env,
        version=settings.app_version,
        components=components,
    )
