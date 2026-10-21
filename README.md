# AI Cognitive Digital Twin

An AI/ML research project for behavioural pattern analysis, productivity estimation, behavioural drift detection, personalized recommendations, and conditional what-if simulation.

- **Institution:** Nagarjuna College of Engineering and Technology, Bengaluru, Karnataka, India
- **Research Team:** Anas Mirza Baig, Arcot Sadiq Basha, Atharv Bhardwaj, Nauman Shah
- **Working Paper Title:** *AI Cognitive Digital Twin: An Agentic Framework for Behavioural Intelligence and Productivity Prediction*

---

## Current Status

- **Milestone 1 (Completed):** Initial environment, FastAPI application, configuration, and testing setup.
- **Milestone 2 (Completed):** Complete Dataset Engineering Pipeline:
  - Dataset schema definition (`0.1.0`) and Pydantic validation models.
  - Reproducible synthetic behavioural data generator with simulated baselines and shift scenarios.
  - Comprehensive data validation and markdown/JSON quality reporting.
  - Leakage-safe feature engineering (task completion, session utilization, 7-day lagged rolling metrics).
  - Strict chronological train/validation/test splitting (70% / 15% / 15%) without date overlap.
  - Preprocessing pipeline with training-fitted median imputation, IQR outlier clipping, and StandardScaler.
- **Milestone 3 (Completed):** Exploratory Data Analysis and Research-Grade Behavioural Clustering:
  - Statistical profiling across 4,500 records and 50 users (univariate, bivariate, temporal, and user heterogeneity).
  - Unsupervised feature selection strictly excluding targets (`productivity_score`), target-derived metrics, and identifiers.
  - Experiment A: Daily Behavioural Pattern Clustering ($N = 4,500$, candidate $k=2..8$; metric-optimal baseline $k=2$ with silhouette 0.1942, exploratory 3-state operational model $k=3$ with silhouette 0.1600 and mean ARI 1.0000).
  - Experiment B: User-Level Behavioural Profile Clustering ($N = 50$, candidate $k=2..6$; recommended primary model $k=2$ with silhouette 0.2997 and mean ARI 1.0000; exploratory candidate $k=3$ with silhouette 0.2170 and mean ARI 0.7910).
  - Neutral cluster profiling in original physical units (no clinical or psychological diagnostic claims).
  - Multi-seed stability analysis and publication-quality visualization exports.
- **Milestone 4 (Completed):** Regression-Based Productivity Prediction:
  - Strict leakage-safe continuous modeling excluding ground truth `productivity_score` and target-derived rolling aggregates.
  - Chronological 70% / 15% / 15% date splitting (Train: 3,150, Val: 650, Test: 700) with train-only preprocessing.
  - Evaluated Baselines: `DummyRegressor(strategy='mean')` (Val RMSE: 11.183, Val $R^2$: -0.0058) and Lag-1 Persistence Baseline $\hat{y}_{u,t} = y_{u,t-1}$ (Val RMSE: 14.687, Val $R^2$: -0.7349) with strict causal split boundary handling.
  - Evaluated Candidates: Linear Regression (Val RMSE: 7.369, $R^2$: 0.5633), Ridge Regression (Val RMSE: 7.369), Random Forest (Val RMSE: 7.667, $R^2$: 0.5272), Gradient Boosting (Val RMSE: 7.607, $R^2$: 0.5346).
  - Validation-based selection chose Linear Regression; final test evaluation achieved Test MAE: 5.645, Test RMSE: 6.965, Test $R^2$: 0.5862 (closely aligning with the empirical finite-sample Oracle benchmark of RMSE = 6.956).
  - Full automated test suite (90 passing tests).
- **Milestone 5 (Completed):** Temporal Modelling and LSTM Evaluation:
  - Genuine future-prediction task definition: day-ahead forecasting ($t \to t+1$) strictly isolating future contemporaneous features and preventing target leakage.
  - Leakage-safe chronological sliding sequence construction ($L=7$d default, $L=14$d comparative) with daily continuity enforcement and causal boundary context.
  - Fair, matched evaluation across Training-Mean (Val RMSE: 11.182, Test RMSE: 10.842), Lag-1 Persistence (Val RMSE: 14.687, Test RMSE: 13.799), and Lagged Ridge Regression (Val RMSE: 10.579, Test RMSE: 10.141).
  - Compact PyTorch LSTM architecture trained with Adam, MSE loss, early stopping, and checkpoint restoration on unseen validation loss.
  - Rigorous scientific assessment: Champion LSTM (14d lookback) achieved Test RMSE = 10.123 ($R^2$: 0.1259) vs. Lagged Ridge Test RMSE = 10.141 ($R^2$: 0.1227), demonstrating that recurrent architectures add no material benefit over simpler regularized linear models due to the conditional independence of daily fluctuations in the synthetic generator.
  - Full automated test suite (103 passing tests).
- **Milestone 6 (Completed):** Behavioural Drift Detection:
  - Longitudinal, per-user drift detection pipeline operating across 12 behavioural telemetry features (focus, sleep, interruptions, work sessions, task completion, stress, mood).
  - Strict causal sliding window formulation: 14-day historical reference baseline ($W_{\text{ref}}$) vs. 7-day recent comparison window ($W_{\text{cmp}}$) with causal isolation preventing future-data leakage.
  - Distribution metrics & hypothesis testing: Two-sample Mann-Whitney $U$ test, standardized effect size (Cohen's $d$), Earth Mover's Distance (Wasserstein metric), and Population Stability Index (PSI).
  - Multi-hypothesis safety: Benjamini–Hochberg False Discovery Rate (FDR) adjustment controlling multiple testing across all candidate features at $\alpha = 0.05$.
  - Explicit multi-tier decision policy: `STRONG_DRIFT` ($p_{\text{adj}} < 0.05$ with $|d| \ge 0.50$), `TENTATIVE_DRIFT` (moderate shift or large magnitude under review), `NO_DRIFT`, and `INSUFFICIENT_DATA`.
  - Controlled scenario benchmarking ($N=50$ users, $T=90$ days):
    - Stable Control: 3.50% false alarm rate (21/600 tests), strictly conforming to the theoretical $\alpha = 0.05$ limit.
    - Focus-Drop Scenario: 60.0% sensitivity (30/50 users flagged, Cohen's $d \approx -1.5$), with unaffected features maintaining 16.60% FPR.
    - Stress-Spike Scenario: 84.0% sensitivity (42/50 users flagged), with unrelated features maintaining 3.78% FPR.
    - Recovery Scenario: 64.0% shift detection during active perturbation, with 66.0% returning verified normalized to baseline upon withdrawal.
  - Responsible AI guardrails: strictly non-clinical framing (no burnout/depression diagnosis), neutral directionality, no causal assertions, and explicit sample sufficiency gating.
  - Full automated test suite (118 passing tests).
- **Milestone 7 (Completed):** Personalized Recommendations & What-If Simulation:
  - Evidence-based, deterministic recommendation engine (`app/ml/recommendations.py`) synthesizing multi-signal behavioral telemetry, detected drift alerts, and unsupervised cluster context across 7 operational categories: interruption management, session pacing, focus optimization, sleep recovery, stress pacing, task calibration, and data collection.
  - Explainable multi-factor priority scoring formula ($S = 0.35M + 0.30E + 0.20C + 0.15P$) combining effect magnitude, statistical evidence quality, goal relevance, and telemetry completeness into a transparent $[0.0, 1.0]$ score.
  - Responsible AI guardrails: deterministic duplicate suppression, cautious data collection prompts for insufficient observations ($N < 5$), non-clinical language safeguards (strictly prohibiting burnout/depression claims), and prominent disclaimers that suggestions are exploratory and non-diagnostic.
  - Transparent what-if simulation engine (`app/ml/simulation.py`) enabling counterfactual feature explorations with input validation, strict domain bounds checking, out-of-distribution (OOD) flagging, and source input immutability.
  - Task and target separation: explicit support for both retrospective productivity score estimation (Milestone 4 Linear Regression) and prospective day-ahead forecasting (Milestone 5 LSTM), strictly enforcing the forecast origin boundary to prevent future-data leakage.
  - Controlled experimental evaluation ($N=50$ users, $T=90$ days): baseline cohort produced 37 structured recommendations with 60.0% sensitivity on focus-drop cohorts; simulation scenarios demonstrated exact reproduction of baseline predictions ($\Delta = +0.00$), realistic sensitivity to focus, interruption, and sleep interventions, and appropriate OOD warnings for extreme modifications.
  - Non-causal counterfactual framing: model-generated differences are explicitly presented as conditional predictions under model assumptions, never as proven causal effects of real-world behavioral changes.
  - Full automated test suite (136 passing tests).
- **Milestone 8 (Completed):** Autonomous Behavioural Intelligence Agent via LangGraph & Google Gemini:
  - Genuine LLM-driven autonomous agent architecture orchestrated with **LangGraph** as the state machine execution engine, **LangChain** as the model integration layer, and **Google Gemini** (`gemini-2.5-flash`) as the LLM provider.
  - Graph State Machine Architecture: Request Validation $\to$ LLM Planning $\to$ Policy Check $\to$ Tool Execution $\to$ Progress Evaluation $\to$ Evidence Verification $\to$ Final Response Synthesis, using real LangGraph nodes, typed state, and conditional edges.
  - Real Tool Integration: 5 registered tools wrapping existing project capabilities (`get_behavioral_summary`, `detect_behavioral_drift`, `generate_recommendations`, `run_what_if_simulation`, `predict_productivity`).
  - Security & Safety Policy Layer: hard tool allowlist, strict cross-user data isolation (preventing unauthorized cross-user access), prompt injection defense (blocking `eval`, `exec`, `os.system`, `DROP TABLE`), non-overridable step/call budgets (`AGENT_MAX_STEPS=8`, `AGENT_MAX_TOOL_CALLS=5`), non-clinical guardrails (blocking burnout/depression claims), and non-causal simulation disclaimers.
  - Evidence-Grounded Verification: application-side `EvidenceVerifier` auditing all generated response claims against execution traces and tool outputs.
  - Transparent Dual Modes: supports both live Google Gemini execution (`AGENT_MODE=llm`) and pure deterministic rule fallback (`AGENT_MODE=deterministic`), with explicit response provenance labeling.
  - Live Gemini Tool Calling Verified: passed live Gemini connectivity and LangGraph tool execution test in 6.66s without exposing credentials.
  - 14-scenario controlled evaluation suite achieving 100.0% benchmark pass rate.
  - Full automated test suite (177 passing tests).

---

## Requirements

- Python 3.11+
- Git
- VS Code
- Node.js/npm (for the future React frontend)

---

## Setup

Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create local configuration:

```powershell
Copy-Item .env.example .env
```

---

## Run Tests

Run the full automated test suite (177 tests):

```powershell
python -m pytest -v
```

---

## Data Pipeline CLI Usage (Milestone 2)

The data engineering pipeline provides an integrated CLI for data generation, validation, and end-to-end preprocessing:

### 1. Generate Synthetic Behavioural Records

```powershell
python -m app.data_pipeline.cli generate --users 50 --days 90 --seed 42 --output data/synthetic/behavioral_records.csv --overwrite
```

### 2. Validate Dataset and View Quality Report

```powershell
python -m app.data_pipeline.cli validate --input data/synthetic/behavioral_records.csv --report data/data_quality_report.json
```

### 3. Run End-to-End Pipeline

```powershell
python -m app.data_pipeline.cli run-all --users 50 --days 90 --seed 42 --output-dir data --overwrite
```

---

## EDA & Behavioural Clustering (Milestone 3)

Execute the complete EDA, feature selection, daily clustering, and user-level clustering workflow:

```powershell
python scripts/run_milestone3.py --users 50 --days 90 --seed 42
```

This generates:
- Research Reports:
  - `research/experiments/milestone3/eda_report.md`
  - `research/experiments/milestone3/feature_selection.md`
  - `research/experiments/milestone3/clustering_report.md`
  - `research/experiments/milestone3/experiment_metadata.json`
- Visualization Charts (`research/experiments/milestone3/results/`):
  - `feature_distributions.png`, `correlation_matrix.png`, `missingness_overview.png`, `temporal_trends.png`, `user_heterogeneity.png`
  - `daily_elbow_and_silhouette.png`, `daily_pca_clusters_k2.png`, `daily_pca_clusters_k3.png`
  - `user_elbow_and_silhouette.png`, `user_pca_clusters_k2.png`, `user_pca_clusters_k3.png`
- Trained Model Artifacts:
  - `artifacts/daily_kmeans_k2.joblib`, `artifacts/daily_kmeans_k3.joblib`
  - `artifacts/user_kmeans_k2.joblib`, `artifacts/user_kmeans_k3.joblib`

---

## Productivity Regression (Milestone 4)

Execute the complete chronological regression training, candidate selection, test evaluation, and diagnostic reporting:

```powershell
python scripts/run_milestone4.py --users 50 --days 90 --seed 42
```

This generates:
- Research Reports:
  - `research/experiments/milestone4/regression_report.md`
  - `research/experiments/milestone4/experiment_metadata.json`
- Diagnostic Charts (`research/experiments/milestone4/results/`):
  - `actual_vs_predicted.png` (validation scatter plot against 1:1 diagonal)
  - `residuals_vs_predicted.png` (heteroscedasticity inspection)
  - `residuals_distribution.png` (residual normality fit)
  - `feature_importance_or_coefficients.png` (standardized predictor weights)
  - `model_comparison_metrics.png` (train vs. validation RMSE and $R^2$)
- Trained Model Artifacts:
  - `artifacts/dummy_mean_baseline.joblib`
  - `artifacts/linear_regression.joblib`
  - `artifacts/ridge_regression_l2.joblib`
  - `artifacts/random_forest_regressor.joblib`
  - `artifacts/gradient_boosting_regressor.joblib`
  - `artifacts/selected_productivity_regressor.joblib`

---

## Temporal Modelling & LSTM Evaluation (Milestone 5)

Execute the complete chronological sliding-window dataset construction, baseline benchmarking, PyTorch LSTM training, validation-based model selection, and test evaluation:

```powershell
python scripts/run_milestone5.py --users 50 --days 90 --seed 42 --lookback 7 --compare_lookback 14
```

This generates:
- Research Report:
  - `research/experiments/milestone5/temporal_modeling_report.md`
  - `research/experiments/milestone5/experiment_metadata.json`
- Publication Diagnostic Charts (`research/experiments/milestone5/results/`):
  - `loss_curves.png` (PyTorch train/validation MSE loss trajectory and early stopping checkpoint)
  - `forecasting_model_comparison.png` (Validation and test RMSE across Mean, Persistence, Ridge, and LSTMs)
  - `actual_vs_predicted.png` (Test set actual vs. forecasted productivity scores)
  - `residuals_distribution.png` (Test forecast error distribution and mean zero alignment)
- Trained PyTorch Model Artifacts:
  - `artifacts/lstm_forecaster_l7.pt`
  - `artifacts/lstm_forecaster_l14.pt`

---

## Behavioural Drift Detection (Milestone 6)

Execute the end-to-end multi-scenario behavioural drift detection experiments across Stable Control, Focus-Drop, Stress-Spike, and Recovery scenarios:

```powershell
python scripts/run_milestone6.py --users 50 --days 90 --seed 42 --ref-window 14 --cmp-window 7
```

This generates:
- Research Report & Metadata:
  - `research/experiments/milestone6/behavioural_drift_report.md`
  - `research/experiments/milestone6/experiment_metadata.json`
- Publication Diagnostic Charts (`research/experiments/milestone6/results/`):
  - `reference_vs_monitoring_distributions.png` (Kernel density and histogram comparison across baseline and monitoring windows)
  - `drift_timeline.png` (Longitudinal Cohen's $d$ trajectory and drift state transitions for sample user)
  - `scenario_performance_summary.png` (Target detection sensitivity vs. false alarm rates across all evaluated scenarios)

---

## Personalized Recommendations & What-If Simulation (Milestone 7)

Execute the end-to-end recommendation engine evaluation and what-if simulation suite across baseline and perturbed cohorts:

```powershell
python scripts/run_milestone7.py --users 50 --days 90 --seed 42
```

This generates:
- Research Report & Metadata:
  - `research/experiments/milestone7/recommendation_simulation_report.md`
  - `research/experiments/milestone7/experiment_metadata.json`
- Publication Diagnostic Charts (`research/experiments/milestone7/results/`):
  - `recommendations_by_category.png` (Distribution of generated recommendations and mean priority scores across categories)
  - `simulated_productivity_deltas.png` (Before-and-after predicted productivity scores across counterfactual scenarios)
  - `what_if_sensitivity_tornado.png` (Sensitivity analysis of productivity predictions to behavioral modifications)

---

## Autonomous Agentic AI System (Milestone 8)

The system features an autonomous agent orchestrated with **LangGraph** and powered by **Google Gemini** (`gemini-2.5-flash`), with transparent deterministic fallback.

### 1. Execute Benchmark Evaluation (14 Controlled Scenarios)

```powershell
python scripts/run_milestone8.py --users 50 --days 90 --seed 42
```

### 2. Verify Live Gemini Tool Calling (Bounded Connectivity Check)

```powershell
python scripts/verify_live_gemini.py
```

### 3. Programmatic Usage (Python)

```python
from app.agent import CognitiveTwinAgent, AgentRequest

# Instantiate agent (defaults to live Gemini if GEMINI_API_KEY is configured, or mode="deterministic")
agent = CognitiveTwinAgent(mode="llm")

# Execute natural-language request through LangGraph
response = agent.run(AgentRequest(
    request_id="demo-001",
    query="Review longitudinal drift and simulate what happens if focus duration increases by 1 hour",
    user_id="synthetic_0001",
    simulation_params={"focus_duration_hours": 1.0},
))

print("Status:", response.status.value)
print("Summary:", response.summary)
print("Findings:", response.findings)
print("Trace Steps:", len(response.execution_trace))
```

---

## Run the API

```powershell
python -m uvicorn app.main:app --reload
```

Open:
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Research Integrity & Documentation

Detailed experimental documentation is located in `research/experiments/`:
- [Data Dictionary](file:///research/experiments/data_dictionary.md): Field definitions, data types, valid ranges, nullability, and leakage roles.
- [Dataset Provenance](file:///research/experiments/dataset_provenance.md): Simulation parameters, heuristic formulas, missingness mechanisms, and scientific limitations.
- [Experiment Protocol](file:///research/experiments/experiment_protocol.md): Experimental baseline parameters, chronological split protocols, and reproducibility standards.
- [EDA Report](file:///research/experiments/milestone3/eda_report.md): Statistical profiling, correlation matrices, and heterogeneity metrics.
- [Feature Selection Rationale](file:///research/experiments/milestone3/feature_selection.md): Unsupervised feature configurations and exclusion justifications.
- [Clustering Report](file:///research/experiments/milestone3/clustering_report.md): Candidate $k$ evaluation, unscaled cluster profiles, stability audits, and responsible AI limitations.
- [Productivity Regression Report](file:///research/experiments/milestone4/regression_report.md): Regression modeling, validation model selection, test evaluation against theoretical noise floor, and causal disclaimers.
- [Temporal Modelling & LSTM Evaluation Report](file:///research/experiments/milestone5/temporal_modeling_report.md): Day-ahead chronological forecasting, leakage-safe sequence sliding windows, matched baselines vs. PyTorch LSTM, and empirical value-add findings.
- [Behavioural Drift Detection Report](file:///research/experiments/milestone6/behavioural_drift_report.md): Longitudinal per-user drift detection, multi-window causal isolation, Mann-Whitney U testing with FDR correction, controlled perturbation sensitivity, and return-to-baseline normalization.
- [Recommendation & Simulation Report](file:///research/experiments/milestone7/recommendation_simulation_report.md): Evidence-based recommendation engine, multi-factor priority scoring, non-clinical safeguards, what-if counterfactual simulation, out-of-distribution detection, and non-causal research limitations.
- [Agentic AI Framework Report](file:///research/experiments/milestone8/agent_framework_report.md): Autonomous agent architecture, LangGraph state machine workflow, Google Gemini integration, application-level policy enforcement, 14-scenario evaluation results, and ethical AI guardrails.

> **Statement of Academic Integrity:**
> Synthetic experiments, real observations, predictions, and causal claims are documented and reported separately. Performance metrics obtained on synthetic datasets demonstrate pipeline correctness and rule recovery, not validated human psychology. Cluster assignments represent objective numerical groupings of behavioral proxies, never psychological or psychiatric diagnoses. Standardized regression coefficients and recurrent neural weights reflect statistical associations, not causal guarantees. Forecasters must never be used as measures of an individual's intrinsic worth, capability, or clinical state. What-if simulation prediction differences represent hypothetical model calculations under specific assumptions, not established real-world intervention outcomes. Autonomous agent plans and outputs are bounded by application-side security policies and evidence verification.
