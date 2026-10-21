
# AI Cognitive Digital Twin

An AI/ML research project for behavioural pattern analysis,
productivity estimation, behavioural drift detection, personalized
recommendations, and conditional what-if simulation.

## Current status

Milestone 1: Initial environment and application setup.
Dataset generation and model training have not started.

## Requirements

- Python 3.11
- Git
- VS Code
- Node.js/npm for the future React frontend

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

## Run tests

```powershell
python -m pytest
```

## Run the API

```powershell
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/health for the health check and
http://127.0.0.1:8000/docs for interactive API documentation.

## Research integrity

Synthetic experiments, real observations, predictions, and
causal claims will be reported separately. Metrics will only be
reported after the corresponding experiments have been executed.
