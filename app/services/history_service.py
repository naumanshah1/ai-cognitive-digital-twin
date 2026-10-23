"""Service layer for persisting and retrieving agent execution audit history."""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models.history import AgentExecutionRecord
from app.db.models.user import User

logger = logging.getLogger(__name__)


class HistoryService:
    """Manages database persistence and retrieval of agent audit trails."""

    @staticmethod
    def create_record(
        db: Session,
        request_id: str,
        user_id: str,
        status: str,
        user_goal: str,
        provider: str,
        model: str,
        execution_mode: str,
        execution_latency: float,
        tools_called: List[Dict[str, Any]],
        findings_count: int,
        recommendations_count: int,
        simulation_performed: bool,
        verification_passed: bool,
        findings_summary: Optional[str] = None,
        error_category: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[AgentExecutionRecord]:
        """Safely creates and commits an agent execution record."""
        # Sanitize and bound fields to prevent DB column overflow
        bounded_goal = user_goal[:495] if user_goal else "No goal provided"
        bounded_error = error_message[:250] if error_message else None
        record_id = f"exec_{uuid.uuid4().hex[:16]}"

        try:
            # Ensure referenced user exists to satisfy foreign key constraint
            user = db.get(User, user_id)
            if user is None:
                user = User(
                    id=user_id,
                    username=user_id,
                    display_name=user_id.replace("_", " ").title(),
                    is_active=True,
                )
                db.add(user)
                db.flush()

            record = AgentExecutionRecord(
                id=record_id,
                request_id=request_id,
                user_id=user_id,
                status=status,
                user_goal=bounded_goal,
                provider=provider,
                model=model,
                execution_mode=execution_mode,
                execution_latency=round(execution_latency, 4),
                tools_called=tools_called,
                findings_count=findings_count,
                recommendations_count=recommendations_count,
                simulation_performed=simulation_performed,
                verification_passed=verification_passed,
                findings_summary=findings_summary,
                error_category=error_category,
                error_message=bounded_error,
            )

            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except Exception as exc:
            db.rollback()
            logger.warning(
                "Failed to persist agent execution record (request_id=%s): %s",
                request_id,
                type(exc).__name__,
            )
            return None

    @staticmethod
    def get_user_history(
        db: Session,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[AgentExecutionRecord], int]:
        """Retrieve paginated execution records belonging strictly to user_id."""
        # Bound limit to protect against oversized query loads
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        try:
            # Total count query
            count_stmt = (
                select(func.count())
                .select_from(AgentExecutionRecord)
                .where(AgentExecutionRecord.user_id == user_id)
            )
            total = db.scalar(count_stmt) or 0

            # Paginated items query
            items_stmt = (
                select(AgentExecutionRecord)
                .where(AgentExecutionRecord.user_id == user_id)
                .order_by(desc(AgentExecutionRecord.created_at))
                .limit(safe_limit)
                .offset(safe_offset)
            )
            records = list(db.scalars(items_stmt).all())
            return records, total
        except Exception as exc:
            logger.error("Error retrieving user history: %s", type(exc).__name__)
            return [], 0

    @staticmethod
    def get_record_by_request_id(
        db: Session,
        request_id: str,
        user_id: str,
    ) -> Optional[AgentExecutionRecord]:
        """Retrieve a specific record ensuring strict ownership enforcement."""
        try:
            stmt = select(AgentExecutionRecord).where(
                AgentExecutionRecord.request_id == request_id,
                AgentExecutionRecord.user_id == user_id,
            )
            return db.execute(stmt).scalar_one_or_none()
        except Exception as exc:
            logger.error("Error querying execution record by request_id: %s", type(exc).__name__)
            return None
