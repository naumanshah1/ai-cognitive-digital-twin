"""Agent data models and contracts for Milestone 8."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentMode(str, Enum):
    LLM = "llm"
    DETERMINISTIC = "deterministic"
    MOCK = "mock"


class ExecutionStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    REJECTED = "rejected"
    FAILED = "failed"


class ToolExecutionStatus(str, Enum):
    SUCCESS = "success"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    ERROR = "error"


class AgentRequest(BaseModel):
    """Input contract for the Cognitive Digital Twin Agent."""
    request_id: str = Field(..., description="Unique request tracking identifier")
    query: str = Field(..., description="Natural language user request or goal")
    intent: Optional[str] = Field(None, description="Inferred or explicitly specified user intent")
    user_id: Optional[str] = Field(None, description="Authorized synthetic user identifier (e.g., 'synthetic_0001')")
    simulation_params: Optional[Dict[str, Any]] = Field(None, description="Optional what-if simulation parameters")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution constraints or parameters")


class ToolCallProposal(BaseModel):
    """Proposal from the planner to execute a registered tool."""
    tool_name: str = Field(..., description="Registered tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Validated tool arguments")
    reason: str = Field(..., description="Rationale for selecting this tool")
    expected_output: str = Field(..., description="Expected utility from the tool output")


class ToolExecutionResult(BaseModel):
    """Result of an executed or rejected tool call."""
    tool_name: str = Field(..., description="Name of the tool executed")
    status: ToolExecutionStatus = Field(..., description="Execution outcome status")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured output from the tool")
    evidence_summary: str = Field(..., description="Human and machine-readable evidence summary")
    error_message: Optional[str] = Field(None, description="Error details if execution failed")
    execution_time_ms: float = Field(0.0, description="Tool execution duration in milliseconds")


class AgentPlan(BaseModel):
    """Proposed plan produced by LLM or deterministic planner."""
    intent: str = Field(..., description="Categorized query intent")
    rationale: str = Field(..., description="Planning reasoning")
    planned_tools: List[ToolCallProposal] = Field(default_factory=list, description="Ordered list of tool proposals")
    requires_clarification: bool = Field(False, description="True if query is ambiguous or unsupported")
    clarification_message: Optional[str] = Field(None, description="Message to user requesting clarification")


class VerificationFindings(BaseModel):
    """Findings from the application-side evidence verifier."""
    is_verified: bool = Field(..., description="Whether response claims are grounded in tool results")
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims flagged as unsupported by evidence")
    disclosed_limitations: List[str] = Field(default_factory=list, description="Required limitations explicitly attached")
    missing_evidence: List[str] = Field(default_factory=list, description="Expected evidence that was not generated")
    sanitized_response: Optional[str] = Field(None, description="Sanitized text with ungrounded claims removed")


class AgentResponse(BaseModel):
    """Final output contract returned by the Cognitive Digital Twin Agent."""
    request_id: str = Field(..., description="Original request identifier")
    query: str = Field(..., description="Original user query")
    status: ExecutionStatus = Field(..., description="Overall execution status")
    summary: str = Field(..., description="Executive summary of the agent findings")
    findings: List[str] = Field(default_factory=list, description="Key evidence-grounded findings")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Generated recommendations if requested")
    simulation_results: Optional[List[Dict[str, Any]]] = Field(None, description="What-if simulation results if requested")
    limitations_and_uncertainty: List[str] = Field(default_factory=list, description="Explicit uncertainty, OOD, or causal caveats")
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list, description="Structured step-by-step execution trace")
    provider_mode: str = Field(..., description="Provider and mode indicator (e.g. 'llm:gemini' or 'deterministic')")
    verification: Optional[VerificationFindings] = Field(None, description="Verification report")
