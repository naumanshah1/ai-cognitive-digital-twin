"""Provider factory and mock provider for offline testing."""

from typing import Any, Dict, List, Optional
from app.agent.models import AgentMode, AgentPlan, AgentRequest, ToolCallProposal, ToolExecutionResult
from app.agent.providers import BaseLLMProvider
from app.agent.providers.gemini import GeminiProvider
from app.core.config import get_settings


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for offline tests without external API calls."""

    def __init__(
        self,
        behavior: str = "normal",
        simulated_tools: Optional[List[str]] = None,
        simulate_error: Optional[str] = None,
    ):
        self.behavior = behavior
        self.simulated_tools = simulated_tools
        self.simulate_error = simulate_error

    def generate_plan(
        self,
        request: AgentRequest,
        available_tools: List[Dict[str, Any]],
        iteration: int = 0,
        prior_results: Optional[List[ToolExecutionResult]] = None,
    ) -> AgentPlan:
        """Generate mock plan based on configured test behavior."""
        if self.simulate_error == "quota":
            raise RuntimeError("Gemini API quota exceeded or rate limit reached.")
        elif self.simulate_error == "timeout":
            raise TimeoutError("Gemini API request timed out after 30.0s.")
        elif self.simulate_error == "auth":
            raise RuntimeError("Gemini API authentication failed. Verify API key validity.")
        elif self.simulate_error == "malformed":
            raise ValueError("Failed to extract valid JSON from LLM response.")

        # If prior results already satisfied request, stop proposing
        if prior_results and len(prior_results) >= 1 and self.behavior != "multi_step":
            return AgentPlan(
                intent="completed",
                rationale="Prior tool execution satisfied the query.",
                planned_tools=[],
                requires_clarification=False,
            )

        user_id = request.user_id or "synthetic_0001"
        query_lower = request.query.lower()

        # Behavior: Unknown tool injection
        if self.behavior == "unknown_tool":
            return AgentPlan(
                intent="adversarial",
                rationale="Proposing unauthorized tool to test policy.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="unauthorized_system_shell",
                        arguments={"command": "dir"},
                        reason="Adversarial tool call test",
                        expected_output="System output",
                    )
                ],
            )

        # Behavior: Prompt injection
        if self.behavior == "prompt_injection":
            return AgentPlan(
                intent="adversarial",
                rationale="Proposing code execution.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="get_behavioral_summary",
                        arguments={"user_id": user_id, "days": "__import__('os').system('dir')"},
                        reason="Injection attack test",
                        expected_output="Bypass output",
                    )
                ],
            )

        # Behavior: Explicitly specified tools
        if self.simulated_tools:
            planned = [
                ToolCallProposal(
                    tool_name=t_name,
                    arguments={"user_id": user_id},
                    reason=f"Mock plan proposing {t_name}",
                    expected_output="Mock evidence",
                )
                for t_name in self.simulated_tools
            ]
            return AgentPlan(
                intent="custom_mock",
                rationale="Executing mock tool proposals.",
                planned_tools=planned,
            )

        # Normal intent inference
        if "drift" in query_lower:
            return AgentPlan(
                intent="drift_analysis",
                rationale="Reviewing longitudinal behavioral drift.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="detect_behavioral_drift",
                        arguments={"user_id": user_id, "ref_window": 14, "cmp_window": 7},
                        reason="Detect statistical drift across candidate telemetry features.",
                        expected_output="FDR-corrected drift states.",
                    )
                ],
            )
        elif "recommend" in query_lower:
            return AgentPlan(
                intent="recommendation_review",
                rationale="Generating prioritized behavioral recommendations.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="generate_recommendations",
                        arguments={"user_id": user_id},
                        reason="Synthesize telemetry and drift into operational suggestions.",
                        expected_output="Prioritized recommendation list.",
                    )
                ],
            )
        elif "simulat" in query_lower:
            mods = request.simulation_params or {"focus_duration_hours": 1.0}
            return AgentPlan(
                intent="what_if_simulation",
                rationale="Evaluating counterfactual what-if scenario.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="run_what_if_simulation",
                        arguments={"user_id": user_id, "modifications": mods, "task_type": "retrospective"},
                        reason="Estimate conditional productivity change.",
                        expected_output="Simulation prediction delta.",
                    )
                ],
            )
        elif "unsupported" in query_lower or "weather" in query_lower or "stock" in query_lower:
            return AgentPlan(
                intent="unsupported_intent",
                rationale="Request cannot be fulfilled with cognitive twin tools.",
                planned_tools=[],
                requires_clarification=True,
                clarification_message="This agent is specialized in behavioral telemetry, drift detection, and productivity simulation.",
            )
        elif "predict" in query_lower or "forecast" in query_lower:
            task = "forecasting" if "forecast" in query_lower else "retrospective"
            return AgentPlan(
                intent="productivity_prediction",
                rationale=f"Running {task} productivity model.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="predict_productivity",
                        arguments={"user_id": user_id, "task_type": task},
                        reason=f"Calculate baseline score for {task} task.",
                        expected_output="Predicted point productivity score.",
                    )
                ],
            )
        elif "comprehensive" in query_lower:
            return AgentPlan(
                intent="comprehensive_review",
                rationale="Conducting complete multi-tool behavioral intelligence audit.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="get_behavioral_summary",
                        arguments={"user_id": user_id, "days": 14},
                        reason="Baseline observational telemetry.",
                        expected_output="Statistical summary.",
                    ),
                    ToolCallProposal(
                        tool_name="detect_behavioral_drift",
                        arguments={"user_id": user_id},
                        reason="Longitudinal distribution shift check.",
                        expected_output="Drift metrics.",
                    ),
                    ToolCallProposal(
                        tool_name="generate_recommendations",
                        arguments={"user_id": user_id},
                        reason="Evidence-grounded action items.",
                        expected_output="Prioritized recommendations.",
                    ),
                ],
            )
        else:
            # Default: behavioral summary
            return AgentPlan(
                intent="behavioral_summary",
                rationale="Summarizing observational telemetry.",
                planned_tools=[
                    ToolCallProposal(
                        tool_name="get_behavioral_summary",
                        arguments={"user_id": user_id, "days": 14},
                        reason="Compute averages for key behavioral dimensions.",
                        expected_output="Observational averages.",
                    )
                ],
            )

    def synthesize_findings(
        self,
        request: AgentRequest,
        tool_results: List[ToolExecutionResult],
    ) -> Dict[str, Any]:
        """Synthesize mock summary and findings strictly from tool results."""
        if not tool_results:
            return {
                "summary": "No tool operations were executed for this request.",
                "findings": [],
            }

        findings = [r.evidence_summary for r in tool_results if r.evidence_summary]
        summary = (
            f"Autonomous analysis completed for user {request.user_id or 'synthetic_0001'} "
            f"based on {len(tool_results)} executed tool(s)."
        )
        return {
            "summary": summary,
            "findings": findings,
        }


class ProviderFactory:
    """Factory for instantiating LLM or deterministic mock providers."""

    @staticmethod
    def create_provider(
        mode: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_behavior: str = "normal",
    ) -> BaseLLMProvider:
        """Instantiate configured provider."""
        settings = get_settings()
        selected_mode = (mode or settings.agent_mode).lower()

        if selected_mode == AgentMode.LLM.value:
            return GeminiProvider(model_id=model_id, api_key=api_key)
        elif selected_mode in [AgentMode.MOCK.value, AgentMode.DETERMINISTIC.value]:
            return MockLLMProvider(behavior=mock_behavior)
        else:
            raise ValueError(f"Unknown agent provider mode: '{selected_mode}'. Valid: 'llm', 'mock', 'deterministic'")
