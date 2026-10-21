"""Bounded live verification script for Google Gemini LLM tool calling via LangGraph."""

import json
from pathlib import Path
import sys
import time

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.agent.agent import CognitiveTwinAgent
from app.agent.models import AgentRequest, ExecutionStatus
from app.agent.providers.gemini import GeminiProvider
from app.core.config import get_settings


def run_live_gemini_verification() -> dict:
    """Execute bounded live Gemini integration test using configured credentials."""
    settings = get_settings()
    model_id = settings.llm_model
    has_key = bool(settings.effective_gemini_api_key)

    report = {
        "timestamp": time.time(),
        "provider": settings.llm_provider,
        "configured_model": model_id,
        "api_key_configured": has_key,
        "success": False,
        "latency_seconds": None,
        "tool_executed": None,
        "execution_status": None,
        "verification_passed": False,
        "findings_count": 0,
        "error_category": None,
        "error_message": None,
    }

    if not has_key:
        report["error_category"] = "missing_api_key"
        report["error_message"] = "No GEMINI_API_KEY found in environment or .env."
        return report

    print(f"[Live Gemini Verification] Initializing configured model: {model_id}...")
    start_time = time.perf_counter()

    try:
        # Bounded single-call agent with Gemini provider
        gemini_provider = GeminiProvider(model_id=model_id)
        agent = CognitiveTwinAgent(provider=gemini_provider, mode="llm", max_steps=4, max_tool_calls=2)

        req = AgentRequest(
            request_id=f"live-gemini-{int(time.time())}",
            query="Summarize recent behavioral telemetry for user synthetic_0001 over the last 14 days.",
            user_id="synthetic_0001",
        )

        resp = agent.run(req)
        duration = round(time.perf_counter() - start_time, 2)
        report["latency_seconds"] = duration
        report["execution_status"] = resp.status.value
        report["findings_count"] = len(resp.findings)
        report["verification_passed"] = resp.verification.is_verified if resp.verification else False

        # Check executed tools
        tools_executed = [
            s.get("tool") for s in resp.execution_trace if s.get("step") == "execute_tools" and "tool" in s
        ]
        report["tool_executed"] = tools_executed

        if resp.status in [ExecutionStatus.COMPLETED, ExecutionStatus.PARTIAL] and len(tools_executed) > 0:
            report["success"] = True
            print(f"  Live Test PASSED in {duration}s! Tool executed: {tools_executed}. Findings: {len(resp.findings)}")
        else:
            report["error_category"] = "execution_incomplete"
            report["error_message"] = f"Response status: {resp.status.value}, summary: {resp.summary[:150]}"
            print(f"  Live Test completed with status: {resp.status.value}")

    except Exception as ex:
        duration = round(time.perf_counter() - start_time, 2)
        report["latency_seconds"] = duration
        err_str = str(ex)
        report["error_message"] = err_str

        if "404" in err_str or "not found" in err_str.lower():
            report["error_category"] = "model_not_found"
        elif "429" in err_str or "quota" in err_str.lower():
            report["error_category"] = "quota_exceeded"
        elif "403" in err_str or "authentication" in err_str.lower():
            report["error_category"] = "authentication_failed"
        elif "timeout" in err_str.lower():
            report["error_category"] = "timeout"
        else:
            report["error_category"] = "general_exception"

        print(f"  Live Test FAILED ({report['error_category']}): {err_str[:200]}")

    # Export report artifact
    out_dir = repo_root / "research" / "experiments" / "milestone8"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "live_gemini_verification.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved live test report to: {out_path}")

    return report


if __name__ == "__main__":
    run_live_gemini_verification()
