"""Agentic AI workflow execution API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    AuthenticatedPrincipal,
    check_rate_limit,
    get_current_user,
)
from app.api.schemas.agent import AgentRunRequest, AgentRunResponse
from app.db.session import get_db
from app.services.agent_service import agent_service

router = APIRouter(prefix="/api/v1/agent", tags=["Agent"])


@router.post(
    "/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_rate_limit)],
    summary="Execute digital twin agent inquiry",
    description="Invokes the LangGraph-orchestrated Gemini agent to evaluate behavioral patterns, drift, recommendations, or counterfactual simulations.",
)
def run_agent(
    payload: AgentRunRequest,
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AgentRunResponse:
    """Run an authenticated agent inquiry scoped strictly to authorized user telemetry."""
    return agent_service.run_agent_request(
        payload=payload,
        principal=current_user,
        db=db,
    )
