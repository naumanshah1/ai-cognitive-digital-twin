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
  - Full automated test suite (74 passing tests).

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

Run the full automated test suite (74 tests):

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

> **Statement of Academic Integrity:**
> Synthetic experiments, real observations, predictions, and causal claims are documented and reported separately. Performance metrics obtained on synthetic datasets demonstrate pipeline correctness and rule recovery, not validated human psychology. Cluster assignments represent objective numerical groupings of behavioral proxies, never psychological or psychiatric diagnoses.
