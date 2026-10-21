"""Agent execution history schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    """Summarized execution history entry."""

    id: str = Field(..., description="Unique record identifier")
    request_id: str = Field(..., description="Correlated request identifier")
    user_id: str = Field(..., description="Target user identifier")
    status: str = Field(..., description="Execution status")
    user_goal: str = Field(..., description="Sanitized inquiry / goal")
    provider: str = Field(..., description="LLM provider name")
    model: str = Field(..., description="Model identifier")
    execution_mode: str = Field(..., description="Execution mode")
    execution_latency: float = Field(..., description="Duration in seconds")
    findings_count: int = Field(0, description="Number of evidence findings")
    recommendations_count: int = Field(0, description="Number of recommendations generated")
    simulation_performed: bool = Field(False, description="Whether simulation was evaluated")
    verification_passed: bool = Field(False, description="Verification outcome")
    error_category: Optional[str] = Field(None, description="Safe error category if failed")
    findings_summary: Optional[str] = Field(None, description="Summary of findings")
    created_at: datetime = Field(..., description="Timestamp of execution")


class HistoryListResponse(BaseModel):
    """Paginated response containing agent execution history."""

    total: int = Field(..., description="Total available records matching filter")
    limit: int = Field(..., description="Page limit applied")
    offset: int = Field(..., description="Page offset applied")
    items: List[HistoryItem] = Field(..., description="Execution history records")


class HistoryDetailResponse(HistoryItem):
    """Detailed execution history entry including tool execution trace."""

    tools_called: List[Dict[str, Any]] = Field(
        default_factory=list, description="Telemetry of tools executed"
    )
    error_message: Optional[str] = Field(None, description="Safe error message if failed")
