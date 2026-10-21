"""Unit tests for agent providers, mock simulation, and ProviderFactory."""

import pytest

from app.agent.models import AgentRequest, ToolExecutionResult, ToolExecutionStatus
from app.agent.providers.factory import MockLLMProvider, ProviderFactory
from app.agent.providers.gemini import GeminiProvider


def test_provider_factory_resolution():
    """Verify ProviderFactory creates correct provider instances."""
    p_mock = ProviderFactory.create_provider(mode="mock")
    assert isinstance(p_mock, MockLLMProvider)

    p_det = ProviderFactory.create_provider(mode="deterministic")
    assert isinstance(p_det, MockLLMProvider)

    with pytest.raises(ValueError, match="Unknown agent provider mode"):
        ProviderFactory.create_provider(mode="invalid_mode")


def test_gemini_provider_missing_key_error():
    """Verify GeminiProvider raises clear error when API key is missing."""
    with pytest.raises(ValueError, match="Gemini API key is not configured"):
        GeminiProvider(api_key="")


def test_gemini_json_extractor():
    """Verify GeminiProvider._extract_json handles various LLM formatting styles."""
    # 1. Clean JSON
    raw = '{"intent": "drift", "planned_tools": []}'
    assert GeminiProvider._extract_json(raw)["intent"] == "drift"

    # 2. Markdown fenced JSON
    fenced = 'Here is the plan:\n```json\n{"intent": "recommend", "planned_tools": []}\n```'
    assert GeminiProvider._extract_json(fenced)["intent"] == "recommend"

    # 3. Text with embedded JSON brackets
    embedded = 'I have analyzed the request: {"intent": "summary", "planned_tools": []} end of message.'
    assert GeminiProvider._extract_json(embedded)["intent"] == "summary"

    # 4. Invalid text
    with pytest.raises(ValueError, match="Failed to extract valid JSON"):
        GeminiProvider._extract_json("No json here at all")


def test_mock_provider_simulated_errors():
    """Verify MockLLMProvider correctly simulates provider failure conditions."""
    req = AgentRequest(request_id="1", query="Summarize telemetry", user_id="synthetic_0001")

    # Quota
    p_quota = MockLLMProvider(simulate_error="quota")
    with pytest.raises(RuntimeError, match="quota exceeded"):
        p_quota.generate_plan(req, available_tools=[])

    # Timeout
    p_timeout = MockLLMProvider(simulate_error="timeout")
    with pytest.raises(TimeoutError, match="timed out"):
        p_timeout.generate_plan(req, available_tools=[])

    # Auth
    p_auth = MockLLMProvider(simulate_error="auth")
    with pytest.raises(RuntimeError, match="authentication failed"):
        p_auth.generate_plan(req, available_tools=[])


def test_mock_provider_synthesizes_from_tool_results():
    """Verify MockLLMProvider synthesis generates summary from tool results."""
    provider = MockLLMProvider()
    req = AgentRequest(request_id="1", query="Summarize telemetry", user_id="synthetic_0001")
    tool_res = [
        ToolExecutionResult(
            tool_name="get_behavioral_summary",
            status=ToolExecutionStatus.SUCCESS,
            data={"records_analyzed": 14},
            evidence_summary="Analyzed 14 days of telemetry for synthetic_0001.",
        )
    ]
    synthesis = provider.synthesize_findings(req, tool_res)
    assert "synthetic_0001" in synthesis["summary"]
    assert len(synthesis["findings"]) == 1
    assert "Analyzed 14 days" in synthesis["findings"][0]
