"""LangGraph-orchestrated Cognitive Digital Twin Agent."""

import time
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph

from app.agent.executor import ToolExecutor
from app.agent.models import (
    AgentMode,
    AgentPlan,
    AgentRequest,
    AgentResponse,
    ExecutionStatus,
    ToolCallProposal,
    ToolExecutionResult,
    ToolExecutionStatus,
    VerificationFindings,
)
from app.agent.planner import AgentPlanner, DeterministicPlanner
from app.agent.policies import (
    enforce_resource_limits,
    validate_tool_arguments,
    validate_tool_name,
    validate_user_scope,
)
from app.agent.providers import BaseLLMProvider
from app.agent.providers.factory import ProviderFactory
from app.agent.state import AgentState
from app.agent.verification import EvidenceVerifier
from app.core.config import get_settings


class CognitiveTwinAgent:
    """Production LangGraph agent for behavioral intelligence, drift detection, and what-if simulation."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        mode: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        max_steps: Optional[int] = None,
        max_tool_calls: Optional[int] = None,
        mock_behavior: str = "normal",
    ):
        settings = get_settings()
        self.mode = mode or settings.agent_mode
        self.max_steps = max_steps or settings.agent_max_steps
        self.max_tool_calls = max_tool_calls or settings.agent_max_tool_calls

        # Resolve provider
        if provider:
            self.provider = provider
        else:
            self.provider = ProviderFactory.create_provider(
                mode=self.mode,
                model_id=model_id,
                api_key=api_key,
                mock_behavior=mock_behavior,
            )

        self.planner = AgentPlanner(self.provider)
        self.executor = ToolExecutor()
        self.verifier = EvidenceVerifier()

        # Build and compile LangGraph StateGraph
        self.graph = self._build_graph().compile()

    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph state machine with verified nodes and conditional edges."""
        builder = StateGraph(AgentState)

        # 1. Register nodes
        builder.add_node("validate_request", self._node_validate_request)
        builder.add_node("plan_step", self._node_plan_step)
        builder.add_node("policy_check", self._node_policy_check)
        builder.add_node("execute_tools", self._node_execute_tools)
        builder.add_node("evaluate_progress", self._node_evaluate_progress)
        builder.add_node("verify_results", self._node_verify_results)
        builder.add_node("generate_final_response", self._node_generate_final_response)

        # 2. Set entry point
        builder.set_entry_point("validate_request")

        # 3. Add conditional edges
        builder.add_conditional_edges(
            "validate_request",
            self._route_after_validation,
            {
                "valid": "plan_step",
                "invalid": "generate_final_response",
            },
        )

        builder.add_conditional_edges(
            "plan_step",
            self._route_after_planning,
            {
                "has_tools": "policy_check",
                "clarification": "generate_final_response",
                "no_tools": "verify_results",
            },
        )

        builder.add_conditional_edges(
            "policy_check",
            self._route_after_policy,
            {
                "execute": "execute_tools",
                "skip": "verify_results",
            },
        )

        builder.add_edge("execute_tools", "evaluate_progress")

        builder.add_conditional_edges(
            "evaluate_progress",
            self._route_after_evaluation,
            {
                "continue": "plan_step",
                "done": "verify_results",
            },
        )

        builder.add_edge("verify_results", "generate_final_response")
        builder.add_edge("generate_final_response", END)

        return builder

    # -------------------------------------------------------------------------
    # Node Implementations
    # -------------------------------------------------------------------------

    def _node_validate_request(self, state: AgentState) -> Dict[str, Any]:
        """Validate input parameters and authorization boundaries."""
        user_id = state.get("user_id") or "synthetic_0001"
        is_valid_user, user_err = validate_user_scope(user_id, user_id)

        trace = list(state.get("execution_trace", []))
        trace.append({
            "step": "validate_request",
            "timestamp": time.time(),
            "valid": is_valid_user,
            "user_id": user_id,
        })

        if not is_valid_user:
            return {
                "user_id": user_id,
                "status": ExecutionStatus.REJECTED.value,
                "error": user_err,
                "current_iteration": 0,
                "execution_trace": trace,
            }

        return {
            "user_id": user_id,
            "status": "in_progress",
            "current_iteration": 0,
            "pending_tool_calls": [],
            "approved_tool_calls": [],
            "rejected_tool_calls": [],
            "tool_results": [],
            "execution_trace": trace,
        }

    def _node_plan_step(self, state: AgentState) -> Dict[str, Any]:
        """Generate tool proposals via LLM or deterministic fallback."""
        curr_iter = state.get("current_iteration", 0) + 1
        req = AgentRequest(
            request_id=state.get("request_id", "req-default"),
            query=state.get("query", ""),
            intent=state.get("intent"),
            user_id=state.get("user_id"),
            simulation_params=state.get("simulation_params"),
            constraints=state.get("constraints", {}),
        )

        trace = list(state.get("execution_trace", []))

        # Check resource limits
        within_limits, limit_err = enforce_resource_limits(
            current_iteration=curr_iter,
            tool_calls_count=len(state.get("tool_results", [])),
            max_steps=state.get("max_steps", self.max_steps),
            max_tool_calls=state.get("max_tool_calls", self.max_tool_calls),
        )

        if not within_limits:
            trace.append({
                "step": "plan_step",
                "timestamp": time.time(),
                "action": "halted_budget",
                "reason": limit_err,
            })
            return {
                "current_iteration": curr_iter,
                "pending_tool_calls": [],
                "error": limit_err,
                "execution_trace": trace,
            }

        prior_results = [
            ToolExecutionResult(**r)
            for r in state.get("tool_results", [])
        ]

        # Call Planner
        try:
            if state.get("execution_mode") == AgentMode.DETERMINISTIC.value:
                plan = DeterministicPlanner.plan(req)
            else:
                plan = self.planner.create_plan(req, iteration=curr_iter, prior_results=prior_results)
        except Exception as ex:
            # Fallback to deterministic plan if provider failed and mode allows fallback
            trace.append({
                "step": "plan_step",
                "timestamp": time.time(),
                "provider_error": str(ex),
                "fallback": "deterministic",
            })
            plan = DeterministicPlanner.plan(req)

        pending = [p.model_dump() for p in plan.planned_tools]
        trace.append({
            "step": "plan_step",
            "timestamp": time.time(),
            "iteration": curr_iter,
            "intent": plan.intent,
            "proposed_tools": [p.tool_name for p in plan.planned_tools],
        })

        return {
            "current_iteration": curr_iter,
            "plan": plan.model_dump(),
            "pending_tool_calls": pending,
            "execution_trace": trace,
        }

    def _node_policy_check(self, state: AgentState) -> Dict[str, Any]:
        """Authorize or reject pending tool calls through application security policy."""
        pending = state.get("pending_tool_calls", [])
        user_id = state.get("user_id")

        approved = []
        rejected = list(state.get("rejected_tool_calls", []))
        tool_results = list(state.get("tool_results", []))
        trace = list(state.get("execution_trace", []))

        for p_dict in pending:
            proposal = ToolCallProposal(**p_dict)
            is_valid, err = validate_tool_arguments(
                proposal.tool_name,
                proposal.arguments,
                requested_user=user_id,
            )
            if is_valid:
                approved.append(proposal.model_dump())
            else:
                rejected.append(proposal.model_dump())
                tool_results.append(
                    ToolExecutionResult(
                        tool_name=proposal.tool_name,
                        status=ToolExecutionStatus.REJECTED,
                        data=None,
                        evidence_summary=f"Policy rejected tool call: {err}",
                        error_message=err,
                    ).model_dump()
                )

        trace.append({
            "step": "policy_check",
            "timestamp": time.time(),
            "approved_count": len(approved),
            "rejected_count": len(rejected),
        })

        return {
            "approved_tool_calls": approved,
            "rejected_tool_calls": rejected,
            "tool_results": tool_results,
            "pending_tool_calls": [],
            "execution_trace": trace,
        }

    def _node_execute_tools(self, state: AgentState) -> Dict[str, Any]:
        """Execute all authorized tool calls in sequence."""
        approved = state.get("approved_tool_calls", [])
        user_id = state.get("user_id")
        tool_results = list(state.get("tool_results", []))
        trace = list(state.get("execution_trace", []))

        for p_dict in approved:
            proposal = ToolCallProposal(**p_dict)
            res = self.executor.execute(proposal, authorized_user=user_id)
            tool_results.append(res.model_dump())
            trace.append({
                "step": "execute_tools",
                "timestamp": time.time(),
                "tool": proposal.tool_name,
                "status": res.status.value,
                "duration_ms": res.execution_time_ms,
            })

        return {
            "approved_tool_calls": [],
            "tool_results": tool_results,
            "execution_trace": trace,
        }

    def _node_evaluate_progress(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate if additional iterations or tool calls are required."""
        trace = list(state.get("execution_trace", []))
        curr_iter = state.get("current_iteration", 0)
        tool_count = len(state.get("tool_results", []))

        trace.append({
            "step": "evaluate_progress",
            "timestamp": time.time(),
            "current_iteration": curr_iter,
            "total_tools_executed": tool_count,
        })

        return {"execution_trace": trace}

    def _node_verify_results(self, state: AgentState) -> Dict[str, Any]:
        """Run EvidenceVerifier against tool execution outputs."""
        tool_results = [
            ToolExecutionResult(**r)
            for r in state.get("tool_results", [])
        ]
        trace = list(state.get("execution_trace", []))

        # Build preliminary findings text for verifier
        preliminary_summary = f"Execution completed with {len(tool_results)} tool operation(s)."
        preliminary_findings = [r.evidence_summary for r in tool_results]

        verification = self.verifier.verify(
            summary=preliminary_summary,
            findings=preliminary_findings,
            tool_results=tool_results,
        )

        trace.append({
            "step": "verify_results",
            "timestamp": time.time(),
            "is_verified": verification.is_verified,
            "unsupported_claims_count": len(verification.unsupported_claims),
            "disclosed_limitations_count": len(verification.disclosed_limitations),
        })

        return {
            "verification_findings": verification.model_dump(),
            "execution_trace": trace,
        }

    def _node_generate_final_response(self, state: AgentState) -> Dict[str, Any]:
        """Assemble typed final AgentResponse contract."""
        req_id = state.get("request_id", "req-unknown")
        query = state.get("query", "")
        plan_dict = state.get("plan") or {}
        tool_results = [
            ToolExecutionResult(**r)
            for r in state.get("tool_results", [])
        ]
        verif_dict = state.get("verification_findings")
        verif = VerificationFindings(**verif_dict) if verif_dict else None
        trace = list(state.get("execution_trace", []))

        # Check if rejected early
        if state.get("status") == ExecutionStatus.REJECTED.value:
            resp = AgentResponse(
                request_id=req_id,
                query=query,
                status=ExecutionStatus.REJECTED,
                summary=f"Request was rejected: {state.get('error')}",
                findings=[],
                limitations_and_uncertainty=["Request violated input bounds or authorization scope."],
                execution_trace=trace,
                provider_mode=f"{self.mode}:{getattr(self.provider, 'model_id', 'mock')}",
            )
            return {"final_response": resp.model_dump(), "status": ExecutionStatus.REJECTED.value}

        # Check if clarification needed
        if plan_dict.get("requires_clarification"):
            clarif_msg = plan_dict.get("clarification_message") or "Query is ambiguous or unsupported."
            resp = AgentResponse(
                request_id=req_id,
                query=query,
                status=ExecutionStatus.PARTIAL,
                summary=clarif_msg,
                findings=[],
                limitations_and_uncertainty=["Clarification required before tool execution."],
                execution_trace=trace,
                provider_mode=f"{self.mode}:{getattr(self.provider, 'model_id', 'mock')}",
            )
            return {"final_response": resp.model_dump(), "status": ExecutionStatus.PARTIAL.value}

        # Synthesize summary and findings
        req = AgentRequest(
            request_id=req_id,
            query=query,
            user_id=state.get("user_id"),
        )
        synthesis = self.provider.synthesize_findings(req, tool_results)

        # Extract structured domain objects if present
        recs = None
        sims = None
        for r in tool_results:
            if r.tool_name == "generate_recommendations" and r.data:
                recs = r.data.get("recommendations")
            elif r.tool_name == "run_what_if_simulation" and r.data:
                sims = [r.data]

        all_limitations = list(verif.disclosed_limitations if verif else [])
        if state.get("error"):
            all_limitations.append(state["error"])

        status = ExecutionStatus.COMPLETED
        if any(r.status in [ToolExecutionStatus.ERROR, ToolExecutionStatus.REJECTED] for r in tool_results):
            status = ExecutionStatus.PARTIAL

        resp = AgentResponse(
            request_id=req_id,
            query=query,
            status=status,
            summary=synthesis.get("summary", ""),
            findings=synthesis.get("findings", []),
            recommendations=recs,
            simulation_results=sims,
            limitations_and_uncertainty=all_limitations,
            execution_trace=trace,
            provider_mode=f"{self.mode}:{getattr(self.provider, 'model_id', 'mock')}",
            verification=verif,
        )

        trace.append({
            "step": "generate_final_response",
            "timestamp": time.time(),
            "status": status.value,
        })

        return {"final_response": resp.model_dump(), "status": status.value}

    # -------------------------------------------------------------------------
    # Routing Conditions
    # -------------------------------------------------------------------------

    def _route_after_validation(self, state: AgentState) -> str:
        if state.get("status") == ExecutionStatus.REJECTED.value:
            return "invalid"
        return "valid"

    def _route_after_planning(self, state: AgentState) -> str:
        plan = state.get("plan") or {}
        if plan.get("requires_clarification"):
            return "clarification"
        if len(state.get("pending_tool_calls", [])) > 0:
            return "has_tools"
        return "no_tools"

    def _route_after_policy(self, state: AgentState) -> str:
        if len(state.get("approved_tool_calls", [])) > 0:
            return "execute"
        return "skip"

    def _route_after_evaluation(self, state: AgentState) -> str:
        # Check budget limits
        curr_iter = state.get("current_iteration", 0)
        max_steps = state.get("max_steps", self.max_steps)
        if curr_iter >= max_steps:
            return "done"
        if len(state.get("tool_results", [])) >= state.get("max_tool_calls", self.max_tool_calls):
            return "done"
        if state.get("error"):
            return "done"
        # In single-shot planning or satisfied requests, terminate loop
        return "done"

    # -------------------------------------------------------------------------
    # Public Execution Entrypoint
    # -------------------------------------------------------------------------

    def run(self, request: AgentRequest) -> AgentResponse:
        """Execute agent workflow through compiled LangGraph engine."""
        initial_state: AgentState = {
            "request_id": request.request_id,
            "query": request.query,
            "user_id": request.user_id,
            "intent": request.intent,
            "simulation_params": request.simulation_params,
            "constraints": request.constraints,
            "validated_context": {},
            "current_iteration": 0,
            "max_steps": self.max_steps,
            "max_tool_calls": self.max_tool_calls,
            "pending_tool_calls": [],
            "approved_tool_calls": [],
            "rejected_tool_calls": [],
            "tool_results": [],
            "execution_trace": [],
            "execution_mode": self.mode,
            "status": "pending",
            "error": None,
        }

        # Run through LangGraph workflow
        final_state = self.graph.invoke(initial_state)

        resp_dict = final_state.get("final_response")
        if resp_dict:
            return AgentResponse(**resp_dict)

        # Fallback if final_response was not populated
        return AgentResponse(
            request_id=request.request_id,
            query=request.query,
            status=ExecutionStatus.FAILED,
            summary="Workflow completed without populating final response.",
            execution_trace=final_state.get("execution_trace", []),
            provider_mode=f"{self.mode}:{getattr(self.provider, 'model_id', 'mock')}",
        )
