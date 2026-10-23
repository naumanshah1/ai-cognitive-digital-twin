"""Main FastAPI application entry point for the AI Cognitive Digital Twin."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin, agent, auth, health, history, users
from app.api.schemas.errors import ErrorResponse
from app.core.config import get_settings
from app.db.session import get_engine, reset_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager for clean resource initialization and disposal."""
    settings = get_settings()
    logger.info("Initializing %s (env=%s, version=%s)", settings.app_name, settings.app_env, settings.app_version)
    yield
    # Shutdown: cleanly dispose database engine connections
    logger.info("Shutting down %s, disposing database connection pools", settings.app_name)
    reset_engine()


def create_application() -> FastAPI:
    """Application factory configuring routers, middleware, and exception handlers."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Autonomous Behavioural Intelligence System — REST API for digital twin analytics, "
            "LangGraph agentic evaluation, and what-if simulation."
        ),
        lifespan=lifespan,
    )

    # CORS configuration - restricted to configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(health.router)
    app.include_router(agent.router)
    app.include_router(users.router)
    app.include_router(history.router)

    # Global Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_resp = ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            request_id=request.headers.get("X-Request-ID"),
        )
        headers = getattr(exc, "headers", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_resp.model_dump(),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Simplify validation error details without leaking sensitive structures
        safe_errors = [
            {"loc": " -> ".join(str(l) for l in err.get("loc", [])), "msg": err.get("msg", "Invalid field")}
            for err in exc.errors()
        ]
        error_resp = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed. Please check submitted payload parameters.",
            request_id=request.headers.get("X-Request-ID"),
            details={"validation_errors": safe_errors},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_resp.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log error safely without exposing credentials or internal traces to user
        logger.error("Unhandled server exception: %s", type(exc).__name__, exc_info=False)
        error_resp = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred while processing the request.",
            request_id=request.headers.get("X-Request-ID"),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_resp.model_dump(),
        )

    return app


app = create_application()
