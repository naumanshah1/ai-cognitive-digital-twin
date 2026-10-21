"""Database engine, connection pooling, and session management."""

import time
from typing import Generator, Optional, Tuple
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def create_app_engine(database_url: Optional[str] = None) -> Engine:
    """Create and configure a SQLAlchemy engine with connection pooling."""
    settings = get_settings()
    url = database_url or settings.database_url

    if url.startswith("sqlite"):
        is_memory = ":memory:" in url
        connect_args = {"check_same_thread": False}
        if is_memory:
            return create_engine(
                url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        return create_engine(url, connect_args=connect_args)

    return create_engine(
        url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_pre_ping=True,
    )


def get_engine() -> Engine:
    """Get or initialize the global engine singleton."""
    global _engine, _session_factory
    if _engine is None:
        _engine = create_app_engine()
        _session_factory = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _engine


def set_engine(engine: Engine) -> None:
    """Override engine (e.g. for testing with an in-memory SQLite database)."""
    global _engine, _session_factory
    _engine = engine
    _session_factory = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def reset_engine() -> None:
    """Dispose and clear current engine."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_session_factory() -> sessionmaker:
    """Get or initialize the session factory."""
    global _session_factory
    if _session_factory is None:
        get_engine()
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated database session with safe rollback."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_readiness(engine: Optional[Engine] = None) -> Tuple[bool, str, Optional[float]]:
    """Safe database connectivity check executing 'SELECT 1'.

    Returns:
        (is_ready, safe_status_description, latency_ms)
        Never leaks connection strings, passwords, or detailed tracebacks.
    """
    target_engine = engine or get_engine()
    start_time = time.perf_counter()
    try:
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return True, "connected", latency_ms
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        # Classify safely without exposing any credentials or host names
        error_type = type(exc).__name__
        safe_msg = f"database connection error ({error_type})"
        return False, safe_msg, latency_ms
