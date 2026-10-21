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
  - Complete command-line interface (`app.data_pipeline.cli`) and full test coverage (52 tests).

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

Run the full automated test suite (52 tests):

```powershell
python -m pytest -v
```

---

## Data Pipeline CLI Usage

The data engineering pipeline provides an integrated CLI for data generation, validation, and end-to-end preprocessing:

### 1. Generate Synthetic Behavioural Records

```powershell
python -m app.data_pipeline.cli generate --users 50 --days 90 --seed 42 --output data/synthetic/behavioral_records.csv --overwrite
```

Supported scenarios:
- `--scenario baseline` (default): Standard behavioural distribution.
- `--scenario stress_spike`: Elevated interruptions and stress levels in the final 30% of days.
- `--scenario focus_drop`: Reduced focus duration and increased screen time in the final 30% of days.

### 2. Validate Dataset and View Quality Report

```powershell
python -m app.data_pipeline.cli validate --input data/synthetic/behavioral_records.csv --report data/data_quality_report.json
```

### 3. Run End-to-End Pipeline

Executes generation, validation, feature engineering, chronological splitting, and preprocessing in a single command:

```powershell
python -m app.data_pipeline.cli run-all --users 50 --days 90 --seed 42 --output-dir data --overwrite
```

This exports:
- `data/synthetic/behavioral_records.csv` + metadata sidecar
- `data/processed/train_features.csv`, `train_target.csv`, `train_metadata.csv`
- `data/processed/val_features.csv`, `val_target.csv`, `val_metadata.csv`
- `data/processed/test_features.csv`, `test_target.csv`, `test_metadata.csv`
- `data/processed/preprocessing_parameters.json`
- `data/processed/data_split_report.json`
- `data/processed/data_quality_report.json`

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

> **Statement of Academic Integrity:**
> Synthetic experiments, real observations, predictions, and causal claims are documented and reported separately. Performance metrics obtained on synthetic datasets demonstrate pipeline correctness and rule recovery, not validated human psychology.
