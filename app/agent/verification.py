"""Evidence-grounded response verification and hallucination safeguard."""

import re
from typing import Any, Dict, List, Optional
from app.agent.models import ToolExecutionResult, ToolExecutionStatus, VerificationFindings
from app.agent.policies import validate_clinical_and_judgemental_safety


class EvidenceVerifier:
    """Verifies agent claims against execution trace, tool outputs, and ethical guardrails."""

    def verify(
        self,
        summary: str,
        findings: List[str],
        tool_results: List[ToolExecutionResult],
        task_type: Optional[str] = None,
    ) -> VerificationFindings:
        """Run complete evidence verification pass on generated response text and findings."""
        unsupported: List[str] = []
        limitations: List[str] = []
        missing_evidence: List[str] = []

        all_text = (summary + " " + " ".join(findings)).strip()

        # 1. Non-clinical & Non-derogatory Language Audit
        is_safe, safety_violations = validate_clinical_and_judgemental_safety(all_text)
        if not is_safe:
            unsupported.extend(safety_violations)

        # 2. Tool Execution Verification
        successful_tools = {
            t.tool_name: t
            for t in tool_results
            if t.status == ToolExecutionStatus.SUCCESS and t.data is not None
        }

        # Check for failed or rejected tools
        for t in tool_results:
            if t.status == ToolExecutionStatus.REJECTED:
                limitations.append(f"Tool '{t.tool_name}' was rejected by policy: {t.error_message}")
            elif t.status == ToolExecutionStatus.ERROR:
                limitations.append(f"Tool '{t.tool_name}' failed during execution: {t.error_message}")

        # 3. What-if Simulation Specific Audits
        if "run_what_if_simulation" in successful_tools:
            sim_data = successful_tools["run_what_if_simulation"].data or {}
            is_ood = sim_data.get("is_out_of_distribution", False)
            if is_ood:
                limitations.append(
                    "Warning: Evaluated simulation scenario is outside the observed training data distribution."
                )

            # Ensure non-causal disclaimer is present
            if not any("causal" in text.lower() or "hypothetical" in text.lower() for text in [summary] + findings):
                limitations.append(
                    "Counterfactual note: Simulated productivity differences are hypothetical model calculations, "
                    "not guaranteed real-world causal intervention outcomes."
                )

        # 4. Behavioral Drift Audits
        if "detect_behavioral_drift" in successful_tools:
            drift_data = successful_tools["detect_behavioral_drift"].data or {}
            state = drift_data.get("overall_state")
            limitations.append(
                f"Statistical drift assessment: Current telemetry indicates state '{state}' with FDR control."
            )

        # 5. Numerical Claim Cross-Verification
        # If numbers like "Delta: +X" or "Focus: Y" appear, verify presence in evidence
        # We check if numbers claimed in text can be matched against numbers in tool outputs
        numbers_in_text = re.findall(r"\b\d+\.?\d*\b", all_text)
        tool_data_str = " ".join([str(t.data) for t in tool_results])
        for num in numbers_in_text:
            if float(num) > 10.0 and num not in tool_data_str:
                # Flag large numbers not grounded in any tool output
                # (Ignoring common small numbers like 1, 2, 7, 14 days)
                unsupported.append(f"Numerical claim '{num}' not found in any tool output data.")

        # Determine verification status
        is_verified = (len(unsupported) == 0)

        # Build sanitized summary if needed
        sanitized = summary
        if not is_verified:
            sanitized += "\n\n[Verification Notice: Certain assertions could not be fully grounded in telemetry evidence.]"

        return VerificationFindings(
            is_verified=is_verified,
            unsupported_claims=unsupported,
            disclosed_limitations=limitations,
            missing_evidence=missing_evidence,
            sanitized_response=sanitized,
        )
