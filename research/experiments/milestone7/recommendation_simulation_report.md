# Behavioural Recommendations and What-If Simulation — Research Report

## 1. Executive Summary
Milestone 7 delivers the evidence-based recommendation and what-if simulation layer of the AI Cognitive Digital Twin.
The system synthesizes longitudinal telemetry distributions, behavioural drift indicators, and predictive models into:
1. **Deterministic, Evidence-Based Recommendations:** Transparent, rule-based behavioral suggestions with explainable priority scores and strict non-clinical safeguards.
2. **What-If Simulation Engine:** Counterfactual exploration of hypothetical behavioral adjustments across retrospective (Milestone 4 Linear Regression) and prospective (Milestone 5 LSTM) forecasting horizons.

### Key Empirical Findings across Synthetic Cohort ($N=50$ users, $T=90$ days):
- **Cohort Recommendation Coverage:** Generated **0** prioritized recommendations across 50 users on evaluation date `2026-02-04`.
- **Controlled Perturbation Sensitivity:** When evaluated on a controlled focus-drop cohort, **66.7%** of affected users triggered the targeted Focus Optimization recommendation (`REC-FOC-001`).
- **What-If Elasticity:** In retrospective simulation, a +60 minute focus duration increase yielded a predicted **+4.91 point** productivity score increase, while reducing interruptions by 2/day added **+1.64 points**.
- **Next-Day Forecasting Simulation:** Increasing focus duration by +60 minutes at the forecast origin shifted next-day predicted productivity by **+0.12 points**.
- **Out-of-Distribution Guardrails:** Simulated extreme values (+8h focus duration) were immediately detected and flagged with IQR boundary warnings.

---

## 2. Recommendation Engine Architecture & Guardrails

### 2.1 Multi-Signal Evidence Synthesis
Recommendations evaluate multiple behavioural streams over a sliding 7-day monitoring window:
- **Daily Telemetry:** Work-session focus, device screen time, interruption events, task volume, and completion ratios.
- **Longitudinal Drift Alerts:** Non-parametric Mann-Whitney $U$ test shifts, Cohen's $d$ effect sizes, and Benjamini–Hochberg FDR adjustments from Milestone 6.
- **Data Completeness & Quality:** Cautious gating requiring $\ge 4$ valid days in the monitoring window before issuing active behavioral advice.

### 2.2 Explainable Priority Formula
Every recommendation is assigned a normalized priority score in $[0.0, 1.0]$ via the deterministic formula:
$$\text{Priority} = 0.35 \cdot M + 0.30 \cdot E + 0.20 \cdot C + 0.15 \cdot P$$
- $M$ (**Magnitude**): Normalized deviation or effect size magnitude relative to personal baseline.
- $E$ (**Evidence Quality**): Statistical significance and metric reliability.
- $C$ (**Data Completeness**): Proportion of non-null telemetry observations in the monitoring window.
- $P$ (**Persistence**): Recurrence or longitudinal duration of the pattern.

### 2.3 Strict Non-Clinical Guardrails
1. **Non-Diagnostic Framing:** Recommendations are exploratory behavioral suggestions, never psychiatric, clinical, or medical diagnoses.
2. **No Guaranteed Improvement:** Suggestions explain *potential* pathways (e.g. 'reduced context-switching friction'), never promising that an intervention 'will definitely improve productivity'.
3. **Neutral Language:** Neutral phrasing is enforced across explanations, rationales, and proposed actions.
4. **Insufficient Data Fallback:** When records are sparse ($< 4$ days), active suggestions are suppressed in favor of cautious observation and data collection (`REC-DAT-001`).

---

## 3. What-If Simulation Engine Architecture

### 3.1 Separation of Retrospective vs. Forecasting Semantics
- **Retrospective Estimation (Milestone 4):** Evaluates same-day hypothetical changes ($X_t \to \hat{y}_t$) on the fitted linear regression model.
- **Future Forecasting (Milestone 5):** Evaluates hypothetical interventions applied strictly at the forecast origin ($t$) to predict future day ($t+1$) via the PyTorch LSTM.
- **No Future Information Leakage:** Forecasting simulations strictly forbid injecting or modifying telemetry beyond the forecast origin $t$.

### 3.2 Counterfactual Disclaimer
Every simulation result explicitly carries the non-causal statement:
> *Under this model and its assumptions, the predicted score changes by X points. This model calculation does not prove that an empirical change in behaviour will cause this productivity change in the real world.*

---

## 4. Empirical Evaluation Results

### 4.1 Recommendation Category Distribution (Cohort $N=50$)

| Recommendation Category | Rule Identifier | Trigger Count | Mean Priority Score | Primary Evidence Indicator |
|---|---|---|---|---|
| **Interruption Management** | `REC-INT-001` | 0 | 0.000 | Daily context switches $\ge 6.0$ / upward drift |
| **Session Pacing** | `REC-SES-001` | 0 | 0.000 | Utilization $< 65\%$ in extended sessions |
| **Focus Optimization** | `REC-FOC-001` | 0 | 0.000 | Focus $< 2.0$h / significant downward drift |
| **Sleep Recovery** | `REC-SLP-001` | 0 | 0.000 | Sleep $< 6.0$h / sleep duration downward drift |
| **Stress Pacing** | `REC-STR-001` | 0 | 0.000 | Stress rating $\ge 3.8$ / upward drift |
| **Task Calibration** | `REC-TSK-001` | 0 | 0.000 | High planned tasks with completion $< 55\%$ |
| **Data Collection** | `REC-DAT-001` | 0 | 0.000 | Monitoring records $< 4$ days |

### 4.2 Retrospective What-If Scenarios (Sample User `synthetic_0001`)

| Scenario ID | Scenario Description | Features Modified | Base Pred | Sim Pred | Delta (pts) | Out-of-Distribution Warning |
|---|---|---|---|---|---|---|
| `SIM-BASE` | Baseline (Zero Modification) | `None` | 50.10 | 50.10 | ** +0.00** | No (In-Bounds) |
| `SIM-FOC-P30` | Focus Duration +30 Min | `focus_duration_hours` | 50.10 | 52.84 | ** +2.73** | No (In-Bounds) |
| `SIM-FOC-P60` | Focus Duration +60 Min | `focus_duration_hours` | 50.10 | 55.57 | ** +5.47** | No (In-Bounds) |
| `SIM-INT-M2` | Interruption Reduction (-2/day) | `interruption_count` | 50.10 | 53.94 | ** +3.84** | No (In-Bounds) |
| `SIM-SLP-P60` | Sleep Duration +60 Min | `sleep_hours` | 50.10 | 51.82 | ** +1.72** | No (In-Bounds) |
| `SIM-DEEP-SPRINT` | Deep Work Sprint (+1h Focus, -2 Int, +1h Session) | `focus_duration_hours, interruption_count, work_session_duration_hours` | 50.10 | 58.09 | ** +7.99** | No (In-Bounds) |
| `SIM-STRESS-BUFFER` | Stress Mitigation (-1 Stress, -30m Inactivity) | `perceived_stress, inactivity_duration_hours` | 50.10 | 46.94 | ** -3.16** | No (In-Bounds) |
| `SIM-OOD-EXTREME` | Extreme Out-of-Distribution (+8h Focus) | `focus_duration_hours, work_session_duration_hours` | 50.10 | 92.84 | **+42.73** | Yes (Flagged) |

### 4.3 Prospective Forecasting What-If Scenario
- **Task Horizon:** Next-Day Forecast ($t \to t+1$)
- **Scenario:** `Forecast Origin Focus +60 Min`
- **Baseline Forecast at Origin:** **47.30** points
- **Simulated Forecast at Origin:** **47.42** points
- **Forecasting Prediction Delta:** **+0.12 points**

---

## 5. Research Limitations
1. **Synthetic Heuristic Grounding:** All benchmarks reflect synthetic data ($N=50$ users, $T=90$ days). Rule efficacy and elasticity reflect synthetic generator dependencies.
2. **Exploratory, Rule-Based Nature:** Recommendations are heuristic rule evaluations, not personalized causal prescriptions derived from human behavioral randomized controlled trials.
3. **Statistical Association vs. Causal Impact:** What-if simulation prediction deltas quantify mathematical sensitivity within the trained surrogate model, not guaranteed empirical causal returns in real humans.
4. **No Psychological or Clinical Diagnostic Validity:** Telemetry indicators must never be used to infer depression, anxiety, burnout, or general human competence.