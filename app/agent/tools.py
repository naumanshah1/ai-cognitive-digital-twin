"""Registered ML and behavioural analytics tools for Milestone 8 agent."""

import time
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import torch

from app.data_pipeline.feature_engineering import engineer_features
from app.data_pipeline.splitting import chronological_split
from app.ml.drift import DriftDetectionConfig, DriftStatus, detect_user_drift
from app.ml.recommendations import generate_recommendations as run_rec_engine
from app.ml.simulation import (
    SimulationScenario,
    SimulationTaskType,
    WhatIfSimulator,
)
from app.ml.temporal import (
    ProductivityLSTM,
    TemporalPreprocessor,
    build_temporal_sequences,
    train_lstm_forecaster,
)
from app.services.preprocessing import BehavioralDataPreprocessor
from app.services.synthetic_data import generate_synthetic_data


class ToolExecutionContext:
    """Lazy-loaded, cached context for synthetic data and fitted ML models."""

    _instance: Optional["ToolExecutionContext"] = None

    def __init__(self, n_users: int = 50, n_days: int = 90, seed: int = 42):
        self.seed = seed
        self.n_users = n_users
        self.n_days = n_days

        # 1. Generate baseline dataset and engineer features
        self.df_raw = generate_synthetic_data(n_users=n_users, n_days=n_days, seed=seed, scenario="baseline")
        self.df_eng = engineer_features(self.df_raw, include_target_derived=False)

        # 2. Chronological splits
        train_raw, val_raw, test_raw, split_rep = chronological_split(self.df_eng, 0.70, 0.15, 0.15)
        self.split_rep = split_rep

        # 3. Fit Retrospective Model & Preprocessor
        self.retro_prep = BehavioralDataPreprocessor(target_col="productivity_score", clip_outliers=True)
        train_prep = self.retro_prep.fit_transform(train_raw)
        self.retro_model = LinearRegression()
        self.retro_model.fit(train_prep.X, train_prep.y)

        # Precompute IQR bounds
        self.iqr_bounds = {
            k: {"lower": v[0], "upper": v[1]}
            for k, v in self.retro_prep.outlier_bounds_.items()
        }

        # 4. Fit Prospective Temporal Forecaster & Preprocessor
        self.seq_features = [
            "sleep_hours", "sleep_quality", "focus_duration_hours", "screen_time_hours",
            "tasks_planned", "tasks_completed", "task_difficulty_avg",
            "work_session_duration_hours", "inactivity_duration_hours", "interruption_count",
            "mood_score", "perceived_stress", "task_completion_rate",
            "work_session_utilization", "inactivity_ratio", "day_of_week", "is_weekend",
            "rolling_focus_std_7d", "work_session_frequency_7d", "productivity_score",
        ]
        self.seqs = build_temporal_sequences(
            df=self.df_eng,
            feature_cols=self.seq_features,
            target_col="productivity_score",
            lookback=7,
            val_start_date=split_rep.validation.min_date,
            val_end_date=split_rep.validation.max_date,
            test_start_date=split_rep.test.min_date,
            test_end_date=split_rep.test.max_date,
        )
        self.temporal_prep = TemporalPreprocessor(scale_target=True)
        self.temporal_prep.fit(train_raw, feature_names=self.seq_features, target_col="productivity_score")

        lstm_arch = ProductivityLSTM(input_dim=len(self.seq_features), hidden_dim=32, num_layers=1, dropout=0.1)
        self.forecasting_lstm, _, _ = train_lstm_forecaster(
            model=lstm_arch,
            train_data=self.seqs["train"],
            val_data=self.seqs["val"],
            preprocessor=self.temporal_prep,
            epochs=5,
            patience=3,
            seed=seed,
        )

        # 5. Build WhatIfSimulator
        self.simulator = WhatIfSimulator(
            retrospective_model=self.retro_model,
            retrospective_preprocessor=self.retro_prep,
            forecasting_model=self.forecasting_lstm,
            forecasting_preprocessor=self.temporal_prep,
            iqr_bounds=self.iqr_bounds,
        )

    @classmethod
    def get_instance(cls) -> "ToolExecutionContext":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None


def _resolve_user_id(df: pd.DataFrame, user_id: str) -> str:
    """Resolve user_id gracefully to handle formats like synthetic_user_00, user_00, synthetic_0001."""
    if user_id in df["user_id"].values:
        return user_id
    import re
    match = re.search(r"(\d+)", user_id)
    if match:
        num = int(match.group(1))
        candidates = [
            f"synthetic_{num + 1:04d}",
            f"synthetic_{num:04d}",
            f"synthetic_{num:02d}",
            f"user_{num:02d}",
            f"synthetic_user_{num:02d}",
        ]
        for cand in candidates:
            if cand in df["user_id"].values:
                return cand
    return user_id


def get_behavioral_summary(user_id: str, days: int = 14) -> Dict[str, Any]:
    """Retrieve statistical behavioral summary for a synthetic user over recent days."""
    ctx = ToolExecutionContext.get_instance()
    resolved_id = _resolve_user_id(ctx.df_eng, user_id)
    user_rows = ctx.df_eng[ctx.df_eng["user_id"] == resolved_id].sort_values("record_date")
    if user_rows.empty:
        return {
            "user_id": user_id,
            "record_count": 0,
            "error": f"No telemetry records found for user {user_id}.",
        }

    recent_df = user_rows.tail(days)
    count = len(recent_df)

    summary = {
        "user_id": user_id,
        "window_days_requested": days,
        "records_analyzed": count,
        "date_range": {
            "start": str(recent_df["record_date"].iloc[0]),
            "end": str(recent_df["record_date"].iloc[-1]),
        },
        "averages": {
            "focus_duration_hours": round(float(recent_df["focus_duration_hours"].mean()), 2),
            "sleep_hours": round(float(recent_df["sleep_hours"].mean()), 2),
            "interruption_count": round(float(recent_df["interruption_count"].mean()), 1),
            "work_session_duration_hours": round(float(recent_df["work_session_duration_hours"].mean()), 2),
            "task_completion_rate": round(float(recent_df["task_completion_rate"].mean()), 3),
            "perceived_stress": round(float(recent_df["perceived_stress"].mean()), 2),
            "mood_score": round(float(recent_df["mood_score"].mean()), 2),
            "actual_productivity_score": round(float(recent_df["productivity_score"].mean()), 2),
        },
        "data_completeness": round(count / max(days, 1), 3),
        "limitations": "Observational summary of synthetic telemetry; does not represent clinical evaluation.",
    }
    return summary


def detect_behavioral_drift(user_id: str, ref_window: int = 14, cmp_window: int = 7) -> Dict[str, Any]:
    """Evaluate longitudinal behavioral drift across features for a user using FDR control."""
    ctx = ToolExecutionContext.get_instance()
    resolved_id = _resolve_user_id(ctx.df_raw, user_id)
    user_rows = ctx.df_raw[ctx.df_raw["user_id"] == resolved_id].sort_values("record_date")
    if user_rows.empty:
        return {"user_id": user_id, "error": f"No telemetry records found for user {user_id}."}

    dates = sorted(user_rows["record_date"].unique())
    eval_date = dates[-1]

    cfg = DriftDetectionConfig(reference_window_days=ref_window, comparison_window_days=cmp_window)
    drift_res = detect_user_drift(user_rows, evaluation_date=str(eval_date), config=cfg)

    features_drifted = [
        {
            "feature": f.feature_name,
            "status": f.status.value,
            "effect_size_d": round(float(f.cohens_d), 3),
            "adjusted_p_value": round(float(f.p_value_adjusted), 4),
            "psi": round(float(f.psi), 3) if f.psi is not None else None,
        }
        for f in drift_res.feature_results.values()
        if f.status in [DriftStatus.STRONG_DRIFT, DriftStatus.TENTATIVE_DRIFT]
    ]

    return {
        "user_id": user_id,
        "evaluation_date": str(eval_date),
        "overall_status": drift_res.overall_status.value,
        "total_features_evaluated": len(drift_res.feature_results),
        "features_flagged_count": len(features_drifted),
        "flagged_features": features_drifted,
        "narrative": drift_res.summary_narrative,
        "safeguard_disclaimer": "Drift alerts reflect statistical distribution shifts, not clinical diagnoses.",
    }


def generate_recommendations(user_id: str) -> Dict[str, Any]:
    """Generate prioritized, evidence-based behavioral recommendations for a user."""
    ctx = ToolExecutionContext.get_instance()
    resolved_id = _resolve_user_id(ctx.df_raw, user_id)
    user_rows = ctx.df_raw[ctx.df_raw["user_id"] == resolved_id].sort_values("record_date")
    if user_rows.empty:
        return {"user_id": user_id, "error": f"No telemetry records found for user {user_id}."}

    dates = sorted(user_rows["record_date"].unique())
    eval_date = dates[-1]

    cfg = DriftDetectionConfig(reference_window_days=14, comparison_window_days=7)
    drift_res = detect_user_drift(user_rows, evaluation_date=str(eval_date), config=cfg)

    report = run_rec_engine(
        user_telemetry_df=user_rows,
        evaluation_date=str(eval_date),
        user_drift_report=drift_res,
        cluster_profile=None,
    )

    items = [
        {
            "id": r.recommendation_id,
            "category": r.category.value,
            "priority_score": round(float(r.priority_score), 3),
            "confidence": r.confidence.value,
            "title": r.title,
            "explanation": r.explanation,
            "proposed_action": r.proposed_action,
            "evidence": r.evidence,
            "rationale": r.rationale,
        }
        for r in report.recommendations
    ]

    disclaimer_str = (
        "This suggestion is an exploratory heuristic derived from synthetic telemetry patterns. "
        "It is optional and does not constitute a clinical, psychological, or medical recommendation."
    )
    return {
        "user_id": user_id,
        "total_recommendations": len(items),
        "recommendations": items,
        "safeguard_notice": disclaimer_str,
    }


def run_what_if_simulation(
    user_id: str,
    modifications: Dict[str, float],
    task_type: str = "retrospective",
) -> Dict[str, Any]:
    """Execute counterfactual what-if simulation for a user under explicit feature changes."""
    ctx = ToolExecutionContext.get_instance()
    resolved_id = _resolve_user_id(ctx.df_eng, user_id)
    user_rows = ctx.df_eng[ctx.df_eng["user_id"] == resolved_id].sort_values("record_date")
    if user_rows.empty:
        return {"user_id": user_id, "error": f"No telemetry records found for user {user_id}."}

    baseline_record = user_rows.iloc[-1].to_dict()

    if task_type == "retrospective":
        sc = SimulationScenario(
            scenario_id=f"AGENT-SIM-{int(time.time())}",
            name="Agent Retrospective Simulation",
            task_type=SimulationTaskType.RETROSPECTIVE_ESTIMATION,
            modifications=modifications,
            description="Agent-invoked retrospective counterfactual scenario.",
        )
        sim_res = ctx.simulator.simulate_retrospective(baseline_record, sc)
    elif task_type == "forecasting":
        sc = SimulationScenario(
            scenario_id=f"AGENT-SIM-FC-{int(time.time())}",
            name="Agent Forecasting Simulation",
            task_type=SimulationTaskType.FUTURE_FORECASTING,
            modifications=modifications,
            description="Agent-invoked next-day prospective counterfactual scenario.",
        )
        sample_seq = ctx.seqs["test"].X[0:1]
        sim_res = ctx.simulator.simulate_forecasting(
            sequence=sample_seq,
            scenario=sc,
            feature_names=ctx.seq_features,
            target_col="productivity_score",
        )
    else:
        return {"error": f"Unsupported task_type: {task_type}"}

    return {
        "user_id": user_id,
        "task_type": str(getattr(sim_res.task_type, "value", sim_res.task_type)),
        "baseline_prediction": round(float(sim_res.baseline_prediction), 2),
        "simulated_prediction": round(float(sim_res.simulated_prediction), 2),
        "prediction_delta": round(float(sim_res.prediction_delta), 2),
        "features_modified": sim_res.features_modified,
        "is_out_of_distribution": sim_res.is_out_of_distribution,
        "warnings": sim_res.warnings,
        "non_causal_disclaimer": sim_res.non_causal_disclaimer,
    }


def predict_productivity(user_id: str, task_type: str = "retrospective") -> Dict[str, Any]:
    """Generate baseline productivity prediction (retrospective estimation or prospective forecast)."""
    ctx = ToolExecutionContext.get_instance()
    resolved_id = _resolve_user_id(ctx.df_eng, user_id)
    user_rows = ctx.df_eng[ctx.df_eng["user_id"] == resolved_id].sort_values("record_date")
    if user_rows.empty:
        return {"user_id": user_id, "error": f"No telemetry records found for user {user_id}."}

    latest_record = user_rows.iloc[-1:].copy()

    if task_type == "retrospective":
        prep_res = ctx.retro_prep.transform(latest_record)
        pred = float(ctx.retro_model.predict(prep_res.X)[0])
        pred = float(np.clip(pred, 0.0, 100.0))
        return {
            "user_id": user_id,
            "task_type": "retrospective_estimation",
            "model_type": "LinearRegression (Milestone 4 Champion)",
            "predicted_productivity_score": round(pred, 2),
            "target_semantics": "Same-day retrospective productivity score estimation.",
            "limitations": "Associational statistical estimate based on contemporaneous synthetic features.",
        }
    elif task_type == "forecasting":
        sample_seq = ctx.seqs["test"].X[0:1]
        X_scaled = ctx.simulator.forecasting_preprocessor.transform_X(sample_seq)
        ctx.simulator.forecasting_model.eval()
        with torch.no_grad():
            t_base = torch.from_numpy(X_scaled).float()
            pred_scaled = ctx.simulator.forecasting_model(t_base).numpy().ravel()
            pred = float(ctx.simulator.forecasting_preprocessor.inverse_transform_y(pred_scaled)[0])
        pred = float(np.clip(pred, 0.0, 100.0))
        return {
            "user_id": user_id,
            "task_type": "prospective_forecasting",
            "model_type": "ProductivityLSTM (Milestone 5 Forecaster)",
            "predicted_next_day_score": round(pred, 2),
            "target_semantics": "Day-ahead prospective forecasting using strictly historical sequence.",
            "limitations": "Model reflects synthetic temporal dynamics; future observations were strictly isolated.",
        }
    else:
        return {"error": f"Unsupported task_type: {task_type}"}


# Registry of callable tools
TOOL_REGISTRY = {
    "get_behavioral_summary": get_behavioral_summary,
    "detect_behavioral_drift": detect_behavioral_drift,
    "generate_recommendations": generate_recommendations,
    "run_what_if_simulation": run_what_if_simulation,
    "predict_productivity": predict_productivity,
}

# Machine-readable schemas for LLM tool binding
TOOL_SCHEMAS = [
    {
        "name": "get_behavioral_summary",
        "description": "Retrieve observational behavioral summary statistics for a synthetic user over recent days.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Synthetic user identifier (e.g., 'synthetic_0001')",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of recent days to summarize (default: 14)",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "detect_behavioral_drift",
        "description": "Evaluate longitudinal behavioral drift across 12 telemetry features using Mann-Whitney U test and FDR control.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Synthetic user identifier (e.g., 'synthetic_0001')",
                },
                "ref_window": {
                    "type": "integer",
                    "description": "Baseline reference window in days (default: 14)",
                },
                "cmp_window": {
                    "type": "integer",
                    "description": "Recent monitoring comparison window in days (default: 7)",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "generate_recommendations",
        "description": "Generate prioritized, evidence-based operational behavioral recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Synthetic user identifier (e.g., 'synthetic_0001')",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "run_what_if_simulation",
        "description": "Simulate counterfactual productivity changes for hypothetical behavioral modifications.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Synthetic user identifier (e.g., 'synthetic_0001')",
                },
                "modifications": {
                    "type": "object",
                    "description": "Dictionary of feature perturbations (e.g., {'focus_duration_hours': 1.0, 'interruption_count': -2.0})",
                },
                "task_type": {
                    "type": "string",
                    "enum": ["retrospective", "forecasting"],
                    "description": "Prediction task to simulate: 'retrospective' (same-day regression) or 'forecasting' (next-day LSTM)",
                },
            },
            "required": ["user_id", "modifications"],
        },
    },
    {
        "name": "predict_productivity",
        "description": "Obtain baseline productivity score prediction for retrospective or prospective forecasting.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Synthetic user identifier (e.g., 'synthetic_0001')",
                },
                "task_type": {
                    "type": "string",
                    "enum": ["retrospective", "forecasting"],
                    "description": "Prediction task semantics: 'retrospective' or 'forecasting'",
                },
            },
            "required": ["user_id"],
        },
    },
]
