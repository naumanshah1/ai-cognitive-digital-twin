"""Agent execution history and audit inspection endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import AuthenticatedPrincipal, get_current_user
from app.api.schemas.history import (
    HistoryDetailResponse,
    HistoryItem,
    HistoryListResponse,
)
from app.db.session import get_db
from app.services.history_service import HistoryService

router = APIRouter(prefix="/api/v1/agent/history", tags=["History"])


@router.get(
    "",
    response_model=HistoryListResponse,
    summary="List agent execution history",
    description="Returns a paginated log of past agent inquiries executed by or for the authenticated principal.",
)
def list_history(
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset index"),
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    """Retrieve execution history strictly scoped to the authenticated caller."""
    records, total = HistoryService.get_user_history(
        db=db,
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
    )

    items = [
        HistoryItem(
            id=r.id,
            request_id=r.request_id,
            user_id=r.user_id,
            status=r.status,
            user_goal=r.user_goal,
            provider=r.provider,
            model=r.model,
            execution_mode=r.execution_mode,
            execution_latency=r.execution_latency,
            findings_count=r.findings_count,
            recommendations_count=r.recommendations_count,
            simulation_performed=r.simulation_performed,
            verification_passed=r.verification_passed,
            error_category=r.error_category,
            findings_summary=r.findings_summary,
            created_at=r.created_at,
        )
        for r in records
    ]

    return HistoryListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get(
    "/{request_id}",
    response_model=HistoryDetailResponse,
    summary="Get single execution history record",
    description="Returns full audit telemetry for a specific agent execution, strictly enforcing user ownership.",
)
def get_history_detail(
    request_id: str,
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryDetailResponse:
    """Retrieve detailed execution audit record by request ID with strict ownership validation."""
    record = HistoryService.get_record_by_request_id(
        db=db,
        request_id=request_id,
        user_id=current_user.user_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record with request_id '{request_id}' not found or you do not have permission to access it.",
        )

    return HistoryDetailResponse(
        id=record.id,
        request_id=record.request_id,
        user_id=record.user_id,
        status=record.status,
        user_goal=record.user_goal,
        provider=record.provider,
        model=record.model,
        execution_mode=record.execution_mode,
        execution_latency=record.execution_latency,
        findings_count=record.findings_count,
        recommendations_count=record.recommendations_count,
        simulation_performed=record.simulation_performed,
        verification_passed=record.verification_passed,
        error_category=record.error_category,
        findings_summary=record.findings_summary,
        created_at=record.created_at,
        tools_called=record.tools_called or [],
        error_message=record.error_message,
    )
