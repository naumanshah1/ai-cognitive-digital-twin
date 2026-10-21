"""Unit tests for Milestone 8 agent data models and contracts."""

import pytest
from pydantic import ValidationError

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


def test_agent_request_valid():
    """Verify valid AgentRequest instantiation."""
    req = AgentRequest(
        request_id="req-001",
        query="Summarize my focus and interruption patterns",
        user_id="synthetic_0001",
        simulation_params={"focus_duration_hours": 1.0},
    )
    assert req.request_id == "req-001"
    assert req.query.startswith("Summarize")
    assert req.user_id == "synthetic_0001"
    assert req.simulation_params == {"focus_duration_hours": 1.0}


def test_agent_request_missing_required_fields():
    """Verify missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        AgentRequest()  # missing request_id and query


def test_tool_call_proposal_and_result():
    """Verify ToolCallProposal and ToolExecutionResult structure."""
    proposal = ToolCallProposal(
        tool_name="get_behavioral_summary",
        arguments={"user_id": "synthetic_0001", "days": 7},
        reason="Check recent focus averages",
        expected_output="Summary statistics",
    )
    assert proposal.tool_name == "get_behavioral_summary"
    assert proposal.arguments["days"] == 7

    res = ToolExecutionResult(
        tool_name=proposal.tool_name,
        status=ToolExecutionStatus.SUCCESS,
        data={"user_id": "synthetic_0001", "records_analyzed": 7},
        evidence_summary="Analyzed 7 days of telemetry.",
        execution_time_ms=12.5,
    )
    assert res.status == ToolExecutionStatus.SUCCESS
    assert res.data["records_analyzed"] == 7
    assert res.execution_time_ms == 12.5


def test_agent_plan_creation_and_defaults():
    """Verify AgentPlan structure with defaults."""
    plan = AgentPlan(
        intent="behavioral_review",
        rationale="Conducting longitudinal review",
    )
    assert plan.intent == "behavioral_review"
    assert plan.planned_tools == []
    assert not plan.requires_clarification
    assert plan.clarification_message is None


def test_agent_response_serialization():
    """Verify AgentResponse serialization and contract fields."""
    verif = VerificationFindings(
        is_verified=True,
        unsupported_claims=[],
        disclosed_limitations=["Observational synthetic telemetry."],
    )
    resp = AgentResponse(
        request_id="req-123",
        query="Simulate focus +1h",
        status=ExecutionStatus.COMPLETED,
        summary="Simulated +1h focus duration.",
        findings=["Baseline score: 70.0 pts", "Simulated score: 73.9 pts"],
        limitations_and_uncertainty=["Counterfactual model prediction."],
        execution_trace=[{"step": "validate_request"}, {"step": "execute_tools"}],
        provider_mode="mock:test",
        verification=verif,
    )
    d = resp.model_dump()
    assert d["request_id"] == "req-123"
    assert d["status"] == "completed"
    assert len(d["findings"]) == 2
    assert d["verification"]["is_verified"] is True
