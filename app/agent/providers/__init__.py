"""LLM and mock provider abstractions for Milestone 8 agent."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.agent.models import AgentPlan, AgentRequest, ToolExecutionResult


class BaseLLMProvider(ABC):
    """Abstract interface for agent LLM providers."""

    @abstractmethod
    def generate_plan(
        self,
        request: AgentRequest,
        available_tools: List[Dict[str, Any]],
        iteration: int = 0,
        prior_results: Optional[List[ToolExecutionResult]] = None,
    ) -> AgentPlan:
        """Analyze request and generate structured tool call plan."""
        pass

    @abstractmethod
    def synthesize_findings(
        self,
        request: AgentRequest,
        tool_results: List[ToolExecutionResult],
    ) -> Dict[str, Any]:
        """Synthesize final evidence-grounded summary and findings from executed tools."""
        pass


from app.agent.providers.factory import MockLLMProvider, ProviderFactory

__all__ = ["BaseLLMProvider", "MockLLMProvider", "ProviderFactory"]
