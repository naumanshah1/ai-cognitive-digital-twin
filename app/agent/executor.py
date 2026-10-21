"""Tool execution engine with policy enforcement and telemetry tracing."""

import time
from typing import Any, Dict, Optional

from app.agent.models import ToolCallProposal, ToolExecutionResult, ToolExecutionStatus
from app.agent.policies import validate_tool_arguments
from app.agent.tools import TOOL_REGISTRY


class ToolExecutor:
    """Executes registered tools with strict argument validation and telemetry."""

    def __init__(self, registry: Optional[Dict[str, Any]] = None):
        self.registry = registry or TOOL_REGISTRY

    def execute(self, proposal: ToolCallProposal, authorized_user: Optional[str] = None) -> ToolExecutionResult:
        """Execute a tool call proposal with policy validation and error handling."""
        start_time = time.perf_counter()
        tool_name = proposal.tool_name
        args = proposal.arguments.copy()

        # If user_id wasn't in arguments but was authorized in request, inject it
        if "user_id" not in args and authorized_user:
            args["user_id"] = authorized_user

        # 1. Application-level Policy Validation
        is_valid, err_msg = validate_tool_arguments(tool_name, args, requested_user=authorized_user)
        if not is_valid:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.REJECTED,
                data=None,
                evidence_summary=f"Tool call rejected by policy: {err_msg}",
                error_message=err_msg,
                execution_time_ms=round(duration_ms, 2),
            )

        # 2. Tool Lookup
        func = self.registry.get(tool_name)
        if not func:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.ERROR,
                data=None,
                evidence_summary=f"Tool '{tool_name}' not found in registry.",
                error_message=f"Unregistered tool: {tool_name}",
                execution_time_ms=round(duration_ms, 2),
            )

        # 3. Safe Execution
        try:
            result_data = func(**args)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Build human-readable evidence summary
            evidence = self._summarize_evidence(tool_name, result_data)

            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                data=result_data,
                evidence_summary=evidence,
                error_message=None,
                execution_time_ms=round(duration_ms, 2),
            )
        except Exception as ex:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.ERROR,
                data=None,
                evidence_summary=f"Execution error in tool '{tool_name}': {str(ex)}",
                error_message=str(ex),
                execution_time_ms=round(duration_ms, 2),
            )

    def _summarize_evidence(self, tool_name: str, data: Dict[str, Any]) -> str:
        """Produce structured textual evidence summary from tool output."""
        if not isinstance(data, dict):
            return str(data)

        if "error" in data:
            return f"Error: {data['error']}"

        if tool_name == "get_behavioral_summary":
            avgs = data.get("averages", {})
            return (
                f"Analyzed {data.get('records_analyzed', 0)} days for user {data.get('user_id')}. "
                f"Avg Focus: {avgs.get('focus_duration_hours')}h, "
                f"Avg Sleep: {avgs.get('sleep_hours')}h, "
                f"Avg Interruptions: {avgs.get('interruption_count')}, "
                f"Task Completion: {avgs.get('task_completion_rate')}, "
                f"Productivity Score: {avgs.get('actual_productivity_score')} pts."
            )

        if tool_name == "detect_behavioral_drift":
            state = data.get("overall_state", "unknown")
            flagged = data.get("features_flagged_count", 0)
            flagged_names = [f["feature"] for f in data.get("flagged_features", [])]
            return (
                f"Drift assessment for user {data.get('user_id')}: Overall state '{state}' with "
                f"{flagged} flagged feature(s): {', '.join(flagged_names) if flagged_names else 'none'}."
            )

        if tool_name == "generate_recommendations":
            count = data.get("total_recommendations", 0)
            recs = data.get("recommendations", [])
            categories = [r["category"] for r in recs]
            return (
                f"Generated {count} prioritized recommendation(s) for user {data.get('user_id')} "
                f"in categories: {', '.join(set(categories)) if categories else 'none'}."
            )

        if tool_name == "run_what_if_simulation":
            delta = data.get("prediction_delta", 0.0)
            baseline = data.get("baseline_prediction", 0.0)
            sim = data.get("simulated_prediction", 0.0)
            task = data.get("task_type", "retrospective")
            ood = data.get("is_out_of_distribution", False)
            ood_str = " (Flagged Out-of-Distribution)" if ood else ""
            return (
                f"What-if simulation ({task}): Baseline {baseline} -> Simulated {sim} "
                f"(Delta: {delta:+} pts){ood_str} for perturbations {data.get('modified_features')}."
            )

        if tool_name == "predict_productivity":
            task = data.get("task_type", "retrospective")
            score = (
                data.get("predicted_productivity_score")
                if "predicted_productivity_score" in data
                else data.get("predicted_next_day_score")
            )
            return f"Productivity baseline prediction ({task}): {score} pts using model {data.get('model_type')}."

        return str(data)
