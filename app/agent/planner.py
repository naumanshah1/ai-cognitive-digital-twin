"""Agent planning coordinator supporting LLM and deterministic modes."""

from typing import Any, Dict, List, Optional
from app.agent.models import AgentPlan, AgentRequest, ToolCallProposal, ToolExecutionResult
from app.agent.policies import check_prompt_injection
from app.agent.providers import BaseLLMProvider
from app.agent.tools import TOOL_SCHEMAS


class AgentPlanner:
    """Plans tool calls and natural-language goal execution."""

    def __init__(self, provider: BaseLLMProvider, tool_schemas: Optional[List[Dict[str, Any]]] = None):
        self.provider = provider
        self.tool_schemas = tool_schemas or TOOL_SCHEMAS

    def create_plan(
        self,
        request: AgentRequest,
        iteration: int = 0,
        prior_results: Optional[List[ToolExecutionResult]] = None,
    ) -> AgentPlan:
        """Create structured execution plan with prompt injection validation."""
        # 1. Pre-execution Prompt Injection Inspection
        is_injection, injection_msg = check_prompt_injection(request.query)
        if is_injection:
            return AgentPlan(
                intent="adversarial_attempt",
                rationale="Security policy rejected query due to code pattern detection.",
                planned_tools=[],
                requires_clarification=True,
                clarification_message=f"Request blocked by security policy: {injection_msg}",
            )

        # 2. Invoke Configured Provider (Gemini or Mock)
        return self.provider.generate_plan(
            request=request,
            available_tools=self.tool_schemas,
            iteration=iteration,
            prior_results=prior_results,
        )


class DeterministicPlanner:
    """Explicit rule-based fallback planner that does not rely on external models."""

    @staticmethod
    def plan(request: AgentRequest) -> AgentPlan:
        """Generate deterministic tool plan using transparent keyword routing."""
        query_lower = request.query.lower()
        user_id = request.user_id or "synthetic_0001"

        if "drift" in query_lower:
            return AgentPlan(
                intent="drift_analysis",
                rationale="Deterministic rule: 'drift' keyword routed to detect_behavioral_drift.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="detect_behavioral_drift",
                        arguments={"user_id": user_id, "ref_window": 14, "cmp_window": 7},
                        reason="Rule-based drift trigger",
                        expected_output="Longitudinal drift metrics",
                    )
                ],
            )
        elif "recommend" in query_lower:
            return AgentPlan(
                intent="recommendations",
                rationale="Deterministic rule: 'recommend' keyword routed to generate_recommendations.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="generate_recommendations",
                        arguments={"user_id": user_id},
                        reason="Rule-based recommendation trigger",
                        expected_output="Prioritized recommendations",
                    )
                ],
            )
        elif "simulat" in query_lower:
            mods = request.simulation_params or {"focus_duration_hours": 1.0}
            return AgentPlan(
                intent="what_if_simulation",
                rationale="Deterministic rule: 'simulat' keyword routed to run_what_if_simulation.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="run_what_if_simulation",
                        arguments={"user_id": user_id, "modifications": mods, "task_type": "retrospective"},
                        reason="Rule-based simulation trigger",
                        expected_output="Simulation prediction delta",
                    )
                ],
            )
        elif "predict" in query_lower or "forecast" in query_lower:
            task = "forecasting" if "forecast" in query_lower else "retrospective"
            return AgentPlan(
                intent="productivity_prediction",
                rationale=f"Deterministic rule: '{task}' keyword routed to predict_productivity.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="predict_productivity",
                        arguments={"user_id": user_id, "task_type": task},
                        reason=f"Rule-based {task} prediction trigger",
                        expected_output=f"Predicted {task} score",
                    )
                ],
            )
        else:
            return AgentPlan(
                intent="behavioral_summary",
                rationale="Deterministic rule: default routed to get_behavioral_summary.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="get_behavioral_summary",
                        arguments={"user_id": user_id, "days": 14},
                        reason="Rule-based telemetry summary trigger",
                        expected_output="Observational summary averages",
                    )
                ],
            )
