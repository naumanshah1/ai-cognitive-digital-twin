# Milestone 8 Research Report: Autonomous Behavioural Intelligence Agent via LangGraph and Google Gemini

**Project:** AI Cognitive Digital Twin — An Autonomous Behavioural Intelligence System
**Framework:** LangGraph (State Machine Orchestration) + LangChain + Google Gemini API
**Environment:** Python 3.14.3, PyTorch 2.11+, Scikit-learn 1.8+, Windows
**Evaluation Date:** 2026-10-21 07:56:06 UTC

---

## 1. Executive Summary

Milestone 8 advances the AI Cognitive Digital Twin from static analytics pipelines into a genuine autonomous agent. Using **LangGraph** as the execution state machine, the agent coordinates natural language intent interpretation, tool selection, policy authorization, evidence retrieval, and evidence-grounded response synthesis.

The system integrates real machine learning and analytical capabilities from Milestones 1–7 without logic duplication:
1. `get_behavioral_summary`: Longitudinal summary statistics across observational dimensions.
2. `detect_behavioral_drift`: Benjamini–Hochberg FDR-corrected non-parametric hypothesis testing.
3. `generate_recommendations`: Deterministic multi-factor priority-scored operational action items.
4. `run_what_if_simulation`: Counterfactual feature interventions with IQR out-of-distribution detection.
5. `predict_productivity`: Retrospective Linear Regression estimation and prospective LSTM sequence forecasting.

---

## 2. LangGraph Architecture & Graph State Transitions

Execution is structured as a directed cyclic state graph with strict node boundaries:

```
[User Request]
      │
      ▼
validate_request ──(valid)──► plan_step (LLM / Rule)
      │                            │
  (invalid)                 (proposes tools)
      │                            │
      │                            ▼
      │                       policy_check (Allowlist & Scope)
      │                            │
      │                     (approved tools)
      │                            │
      │                            ▼
      │                       execute_tools (ToolExecutor)
      │                            │
      │                            ▼
      │                       evaluate_progress ──(within budget)──► [Loop to plan_step]
      │                            │
      │                      (audit complete)
      │                            │
      │                            ▼
      │                       verify_results (EvidenceVerifier)
      │                            │
      ▼                            ▼
generate_final_response ◄──────────┘
      │
      ▼
    [END]
```

### Core Safety Safeguards Enforced Outside the LLM:
- **Application-Side Allowlist:** Only the 5 approved analytical tools can be executed.
- **Cross-User Scope Isolation:** User ID format and authorization boundaries are enforced prior to tool execution; cross-user telemetry access is blocked.
- **Prompt Injection Defense:** Code injection patterns (`eval`, `exec`, `os.system`, `DROP TABLE`) are blocked at the planner boundary before any model call.
- **Resource Budgets:** `AGENT_MAX_STEPS` (default: 8) and `AGENT_MAX_TOOL_CALLS` (default: 5) are hard application limits that cannot be overridden by model outputs.
- **Non-Clinical Guardrails:** Language containing clinical diagnostic claims (burnout, clinical depression, anxiety disorders) or derogatory judgements is flagged and sanitized by the EvidenceVerifier.
- **Non-Causal Disclaimer:** All simulated prediction differences are strictly framed as hypothetical model calculations rather than real-world causal intervention outcomes.

---

## 3. Live Google Gemini Integration Verification

A minimal, bounded live Gemini API call was executed using credentials loaded securely from the existing `.env` file:

- **Live Provider:** `gemini`
- **Configured Model ID:** `gemini-2.5-flash`
- **Live Connectivity Result:** `SUCCESS`
- **Measured Network Latency:** `6.66 s`
- **Tools Executed via Live LLM:** `['get_behavioral_summary']`
- **Evidence Verification Passed:** `True`


*Secret Protection Note: The API key is loaded via `Settings.effective_gemini_api_key` and passed directly to the constructor parameter without printing, echoing, logging, or committing.*

---

## 4. Controlled Benchmark Scenarios (14 Scenarios Evaluated)

| Scenario ID | Name | Category | Actual Status | Executed Tools | Result | Latency |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| `SC-01-SUMMARY` | Observational Telemetry Summary | `core_analytics` | `completed` | `get_behavioral_summary` | **PASS** | 1531.64 ms |
| `SC-02-DRIFT` | Longitudinal Drift Assessment | `core_analytics` | `completed` | `detect_behavioral_drift` | **PASS** | 24.11 ms |
| `SC-03-RECOMMEND` | Evidence-Based Recommendations | `core_analytics` | `completed` | `generate_recommendations` | **PASS** | 23.88 ms |
| `SC-04-SIM-VALID` | Valid What-If Simulation (+1h Focus) | `simulation` | `completed` | `run_what_if_simulation` | **PASS** | 45.46 ms |
| `SC-05-SIM-INVALID` | Invalid Simulation Arguments (Empty Mods) | `robustness` | `partial` | `None (Blocked/Halted)` | **PASS** | 3.65 ms |
| `SC-06-INSUFF-DATA` | Insufficient Data Handling (sparse user) | `robustness` | `completed` | `get_behavioral_summary` | **PASS** | 5.05 ms |
| `SC-07-UNSUPPORTED` | Out-of-Domain Query Clarification | `dialogue` | `partial` | `None (Blocked/Halted)` | **PASS** | 2.0 ms |
| `SC-08-UNKNOWN-TOOL` | Adversarial Unknown Tool Blocked | `security` | `partial` | `None (Blocked/Halted)` | **PASS** | 3.54 ms |
| `SC-09-PROVIDER-FAIL` | Provider Quota Failure Handling | `fault_tolerance` | `completed` | `get_behavioral_summary` | **PASS** | 6.94 ms |
| `SC-10-MALFORMED` | Malformed Response Fallback Handling | `fault_tolerance` | `completed` | `get_behavioral_summary` | **PASS** | 6.82 ms |
| `SC-11-MULTI-TOOL` | Multi-Tool Comprehensive Audit | `core_analytics` | `completed` | `get_behavioral_summary, detect_behavioral_drift, generate_recommendations` | **PASS** | 43.38 ms |
| `SC-12-INJECTION` | Prompt Injection Blocked at Planner | `security` | `partial` | `None (Blocked/Halted)` | **PASS** | 1.72 ms |
| `SC-13-STEP-LIMIT` | Maximum Step Budget Enforcement | `resource_limits` | `completed` | `None (Blocked/Halted)` | **PASS** | 2.25 ms |
| `SC-14-DETERMINISTIC` | Pure Deterministic Rule Execution | `deterministic` | `completed` | `detect_behavioral_drift` | **PASS** | 20.22 ms |

**Overall Benchmark Success Rate:** 14 / 14 (100.0%)

---

## 5. Research Validity & Limitations

1. **Synthetic Telemetry Origin:** The agent operates upon synthetic behavioral telemetry. The agent's tool execution and reasoning correctness reflect computational reliability, not validated clinical psychology.
2. **Associational Modeling vs Causal Inferences:** Model outputs reflect statistical associations within the synthetic data generating process. Predicted counterfactual deltas are hypothetical estimates under model assumptions, not empirical causal guarantees.
3. **Strictly Non-Clinical Operational Scope:** Recommendations are operational work-pacing heuristics. The system does not diagnose mental health disorders, psychological conditions, or occupational burnout.
4. **Deterministic Fallback Transparency:** The system provides transparent labeling (`provider_mode: "llm:gemini"` vs `provider_mode: "deterministic"`) to prevent misleading users regarding when an LLM vs a deterministic rule processed a query.
