"""Service layer bridging FastAPI HTTP endpoints with the LangGraph CognitiveTwinAgent."""

import time
import uuid
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agent.agent import CognitiveTwinAgent
from app.agent.models import AgentRequest, AgentResponse, ExecutionStatus
from app.agent.providers.factory import ProviderFactory
from app.api.dependencies import AuthenticatedPrincipal
from app.api.schemas.agent import AgentRunRequest, AgentRunResponse
from app.core.config import get_settings
from app.services.history_service import HistoryService


class AgentService:
    """Manages agent execution, authorization verification, and persistence."""

    def __init__(
        self,
        agent: Optional[CognitiveTwinAgent] = None,
    ):
        self._agent = agent

    def get_agent(self, mode: Optional[str] = None) -> CognitiveTwinAgent:
        """Returns initialized agent instance."""
        if self._agent is not None:
            return self._agent
        settings = get_settings()
        selected_mode = mode or settings.agent_mode
        provider = ProviderFactory.create_provider(mode=selected_mode)
        return CognitiveTwinAgent(
            provider=provider,
            mode=selected_mode,
            max_steps=settings.agent_max_steps,
            max_tool_calls=settings.agent_max_tool_calls,
        )

    def run_agent_request(
        self,
        payload: AgentRunRequest,
        principal: AuthenticatedPrincipal,
        db: Optional[Session] = None,
        override_mode: Optional[str] = None,
    ) -> AgentRunResponse:
        """Execute agent workflow with scope verification and persistence."""
        # 1. Determine and authorize target user scope
        target_user_id = payload.target_user_id or principal.user_id
        if not principal.is_authorized_for_user(target_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: You are not authorized to query or execute agent actions for user '{target_user_id}'.",
            )

        # 2. Construct correlated request conforming to AgentRequest schema
        request_id = payload.request_id or f"req_{uuid.uuid4().hex[:12]}"
        constraints_dict: Dict[str, Any] = {}
        if payload.constraints:
            constraints_dict["constraints"] = payload.constraints

        agent_request = AgentRequest(
            request_id=request_id,
            query=payload.goal,
            user_id=target_user_id,
            simulation_params=payload.simulation_params,
            constraints=constraints_dict,
        )

        # 3. Execute LangGraph agent
        agent = self.get_agent(mode=override_mode)
        start_time = time.perf_counter()
        agent_response: AgentResponse = agent.run(agent_request)
        latency = round(time.perf_counter() - start_time, 4)

        # 4. Parse provider and mode metadata
        provider_mode_str = agent_response.provider_mode or "llm:gemini"
        if ":" in provider_mode_str:
            exec_mode, model_or_provider = provider_mode_str.split(":", 1)
        else:
            exec_mode = provider_mode_str
            model_or_provider = "default"

        provider_name = "gemini" if "gemini" in model_or_provider.lower() else ("mock" if "mock" in model_or_provider.lower() else "deterministic")
        model_name = model_or_provider

        # 5. Extract telemetry and summary for persistence
        tools_called = [
            {
                "tool_name": step.get("tool") or step.get("tool_name", "unknown"),
                "status": step.get("status", "SUCCESS").upper(),
                "duration_ms": step.get("duration_ms", 0.0),
            }
            for step in (agent_response.execution_trace or [])
            if step.get("step") == "execute_tool" or "tool" in step
        ]

        simulation_performed = bool(agent_response.simulation_results)
        verification_passed = (
            agent_response.verification.is_verified
            if agent_response.verification
            else (agent_response.status == ExecutionStatus.COMPLETED)
        )

        # Build disclaimer
        base_disclaimer = "AI Cognitive Digital Twin experimental research twin. Observational findings only; strictly non-clinical and non-causal."
        if agent_response.limitations_and_uncertainty:
            disclaimer_text = f"{base_disclaimer} " + " ".join(agent_response.limitations_and_uncertainty)
        else:
            disclaimer_text = base_disclaimer

        status_str = agent_response.status.value.upper()
        error_dict = None
        if agent_response.status in (ExecutionStatus.FAILED, ExecutionStatus.REJECTED):
            error_dict = {
                "category": status_str,
                "message": agent_response.summary,
            }

        # 6. Persist record if DB session is provided
        if db is not None:
            HistoryService.create_record(
                db=db,
                request_id=request_id,
                user_id=target_user_id,
                status=status_str,
                user_goal=payload.goal,
                provider=provider_name,
                model=model_name,
                execution_mode=exec_mode,
                execution_latency=latency,
                tools_called=tools_called,
                findings_count=len(agent_response.findings),
                recommendations_count=len(agent_response.recommendations or []),
                simulation_performed=simulation_performed,
                verification_passed=verification_passed,
                findings_summary=agent_response.summary,
                error_category=status_str if error_dict else None,
                error_message=agent_response.summary if error_dict else None,
            )

        sim_output = None
        if agent_response.simulation_results and len(agent_response.simulation_results) > 0:
            sim_output = agent_response.simulation_results[0]

        verif_dict = (
            agent_response.verification.model_dump()
            if agent_response.verification
            else {"is_verified": True, "unsupported_claims": [], "disclosed_limitations": []}
        )

        return AgentRunResponse(
            request_id=request_id,
            user_id=target_user_id,
            status=status_str,
            execution_mode=exec_mode,
            provider=provider_name,
            model=model_name,
            execution_latency=latency,
            summary=agent_response.summary,
            findings=agent_response.findings,
            recommendations=agent_response.recommendations or [],
            simulation_result=sim_output,
            verification=verif_dict,
            execution_trace_summary=agent_response.execution_trace or [],
            disclaimer=disclaimer_text,
            error=error_dict,
        )


# Global service singleton
agent_service = AgentService()
