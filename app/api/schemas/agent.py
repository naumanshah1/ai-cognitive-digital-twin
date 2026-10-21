"""Agent execution request and response schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """Payload to trigger an agentic digital twin evaluation."""

    goal: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural-language user inquiry or command",
        examples=["Summarize my recent behavioral patterns and focus trends."],
    )
    target_user_id: Optional[str] = Field(
        None,
        description="Target user ID to analyze. If omitted, defaults to the authenticated user's ID.",
    )
    simulation_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional feature perturbation parameters for what-if simulation",
        examples=[{"focus_duration_hours": 6.5}],
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Explicit constraints for the agent planning phase",
    )
    request_id: Optional[str] = Field(
        None,
        max_length=64,
        description="Optional client-provided correlation ID",
    )


class AgentRunResponse(BaseModel):
    """Structured response from the agentic execution engine."""

    request_id: str = Field(..., description="Correlated request identifier")
    user_id: str = Field(..., description="Target user ID analyzed")
    status: str = Field(..., description="Final execution status (e.g. COMPLETED, REJECTED, FAILED)")
    execution_mode: str = Field(..., description="Operating mode: llm or deterministic")
    provider: str = Field(..., description="LLM provider name: gemini or mock")
    model: str = Field(..., description="Model identifier used")
    execution_latency: float = Field(..., description="Total execution duration in seconds")
    summary: str = Field(..., description="Natural language synthesis of findings")
    findings: List[str] = Field(default_factory=list, description="Evidence-backed analytical observations")
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Operational, non-clinical recommendations"
    )
    simulation_result: Optional[Dict[str, Any]] = Field(
        None, description="Counterfactual what-if simulation outputs if requested"
    )
    verification: Dict[str, Any] = Field(
        ..., description="Verification findings and grounding audit results"
    )
    execution_trace_summary: List[Dict[str, Any]] = Field(
        default_factory=list, description="Audit trace of tools proposed, approved, and executed"
    )
    disclaimer: str = Field(
        ..., description="Non-clinical and non-causal behavioral twin disclaimer"
    )
    error: Optional[Dict[str, Any]] = Field(
        None, description="Safe error details if execution encountered an issue"
    )
