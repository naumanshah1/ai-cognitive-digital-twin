"""Agent execution history database model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class AgentExecutionRecord(Base):
    """Persistent audit and history record of an agent run."""

    __tablename__ = "agent_execution_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    user_goal: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_mode: Mapped[str] = mapped_column(
        String(32), default="llm", nullable=False
    )
    execution_latency: Mapped[float] = mapped_column(Float, default=0.0)

    # Telemetry and outputs
    tools_called: Mapped[List[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    recommendations_count: Mapped[int] = mapped_column(Integer, default=0)
    simulation_performed: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_passed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Safe summaries and sanitized error fields
    findings_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_category: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="execution_records"
    )

    __table_args__ = (
        Index("ix_agent_exec_user_created", "user_id", "created_at"),
    )
