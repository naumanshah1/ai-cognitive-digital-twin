"""LangGraph state schema for Cognitive Digital Twin Agent."""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Execution state passed between nodes in the LangGraph workflow."""
    # Request & context
    request_id: str
    query: str
    user_id: Optional[str]
    intent: Optional[str]
    simulation_params: Optional[Dict[str, Any]]
    constraints: Dict[str, Any]
    validated_context: Dict[str, Any]

    # Planning & routing
    plan: Optional[Dict[str, Any]]
    current_iteration: int
    max_steps: int
    max_tool_calls: int

    # Tool queue and execution trace
    pending_tool_calls: List[Dict[str, Any]]
    approved_tool_calls: List[Dict[str, Any]]
    rejected_tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    execution_trace: List[Dict[str, Any]]

    # Verifier and synthesis
    verification_findings: Optional[Dict[str, Any]]
    execution_mode: str
    status: str
    error: Optional[str]

    # Final synthesized output
    final_response: Optional[Dict[str, Any]]
