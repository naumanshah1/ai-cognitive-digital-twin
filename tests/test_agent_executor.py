"""Unit tests for tool execution engine with error containment and telemetry."""

from app.agent.executor import ToolExecutor
from app.agent.models import ToolCallProposal, ToolExecutionStatus


def test_tool_executor_successful_run():
    """Verify ToolExecutor runs registered tool and captures telemetry."""
    executor = ToolExecutor()
    proposal = ToolCallProposal(
        tool_name="get_behavioral_summary",
        arguments={"user_id": "synthetic_0001", "days": 7},
        reason="Test summary execution",
        expected_output="Telemetry averages",
    )
    result = executor.execute(proposal, authorized_user="synthetic_0001")
    assert result.status == ToolExecutionStatus.SUCCESS
    assert result.tool_name == "get_behavioral_summary"
    assert result.data is not None
    assert result.execution_time_ms >= 0.0
    assert "Analyzed 7 days" in result.evidence_summary


def test_tool_executor_policy_rejection():
    """Verify ToolExecutor rejects tool call that violates policy."""
    executor = ToolExecutor()
    proposal = ToolCallProposal(
        tool_name="get_behavioral_summary",
        arguments={"user_id": "synthetic_0002", "days": 7},  # Cross-user mismatch
        reason="Unauthorized user test",
        expected_output="Error",
    )
    result = executor.execute(proposal, authorized_user="synthetic_0001")
    assert result.status == ToolExecutionStatus.REJECTED
    assert result.data is None
    assert "Unauthorized cross-user access" in result.error_message


def test_tool_executor_unregistered_tool():
    """Verify ToolExecutor cleanly rejects unknown tools."""
    executor = ToolExecutor()
    proposal = ToolCallProposal(
        tool_name="non_existent_tool",
        arguments={"user_id": "synthetic_0001"},
        reason="Test unregistered",
        expected_output="Error",
    )
    result = executor.execute(proposal, authorized_user="synthetic_0001")
    assert result.status == ToolExecutionStatus.REJECTED
    assert "not on the authorized allowlist" in result.error_message


def test_tool_executor_exception_handling():
    """Verify exceptions inside tools are caught safely without crashing."""
    def broken_tool(**kwargs):
        raise RuntimeError("Simulated internal sensor failure")

    mock_registry = {"broken_tool": broken_tool}
    executor = ToolExecutor(registry=mock_registry)

    # Note: to test tool execution exception, broken_tool must pass policy check
    # We can temporarily patch ALLOWED_TOOLS for this test
    from app.agent import policies
    policies.ALLOWED_TOOLS.add("broken_tool")
    try:
        proposal = ToolCallProposal(
            tool_name="broken_tool",
            arguments={"user_id": "synthetic_0001"},
            reason="Test failure handling",
            expected_output="None",
        )
        result = executor.execute(proposal, authorized_user="synthetic_0001")
        assert result.status == ToolExecutionStatus.ERROR
        assert "Simulated internal sensor failure" in result.error_message
    finally:
        policies.ALLOWED_TOOLS.discard("broken_tool")
