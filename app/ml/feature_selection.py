"""Feature selection configuration and transformation for behavioural clustering.

Defines strictly unsupervised feature sets for daily-record and user-level clustering,
guaranteeing complete exclusion of targets, target-derived metrics, and identifiers.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd

from app.data_pipeline.feature_engineering import engineer_features
from app.data_pipeline.schema import (
    EXCLUDED_FROM_PREDICTORS,
    IDENTIFIER_COLUMNS,
    TARGET_COLUMNS,
    TARGET_DERIVED_COLUMNS,
    TIMESTAMP_COLUMNS,
)

# Core behavioural telemetries for daily-record clustering (unsupervised)
DAILY_CLUSTERING_FEATURES = [
    "sleep_hours",
    "focus_duration_hours",
    "screen_time_hours",
    "task_difficulty_avg",
    "work_session_duration_hours",
    "inactivity_duration_hours",
    "interruption_count",
    "task_completion_rate",
    "work_session_utilization",
    "inactivity_ratio",
]

# Longitudinal aggregates per user for user-profile clustering (unsupervised)
USER_AGGREGATED_CLUSTERING_FEATURES = [
    "mean_focus_hours",
    "mean_sleep_hours",
    "mean_screen_time_hours",
    "mean_work_session_hours",
    "mean_task_completion_rate",
    "mean_interruption_count",
    "focus_variability_std",
    "work_session_consistency",
]

# Explicit documentation of rejected columns with scientific justifications
FEATURE_EXCLUSION_REGISTRY = {
    "productivity_score": (
        "Ground-truth prediction target. Including it in unsupervised clustering "
        "would cause catastrophic target leakage and circular cluster validation."
    ),
    "rolling_productivity_mean_7d": (
        "Derived from historical productivity scores. Excluded to prevent target leakage."
    ),
    "productivity_change_7d": (
        "Derived from historical productivity scores. Excluded to prevent target leakage."
    ),
    "user_id": (
        "Pseudonymous categorical identifier. Treating user IDs as numerical metrics "
        "would artificially group users by arbitrary string order."
    ),
    "record_date": (
        "Temporal timestamp. Excluded from clustering space to ensure clusters reflect "
        "behavioural patterns rather than calendar dates."
    ),
    "day_of_week": (
        "Calendar feature. Excluded from core behavioural distance metric to cluster "
        "intrinsic behavioural intensity rather than weekday/weekend scheduling."
    ),
    "is_weekend": (
        "Binary calendar feature. Excluded for same reason as day_of_week."
    ),
    "mood_score": (
        "Subjective self-report with 15% missingness. Excluded from baseline clustering "
        "to prevent distortion from synthetic MCAR imputation in distance metrics."
    ),
    "perceived_stress": (
        "Subjective self-report with 15% missingness. Excluded from baseline clustering "
        "to ensure distance metrics reflect objective telemetries."
    ),
    "sleep_quality": (
        "Subjective self-report rating. Excluded from distance metric in favor of objective sleep_hours."
    ),
}


@dataclass
class ClusteringDataset:
    """Prepared clustering data containing numerical feature matrix, metadata, and column names."""

    X: pd.DataFrame
    metadata: pd.DataFrame
    feature_names: list[str]
    experiment_type: str


def prepare_daily_clustering_data(
    df: pd.DataFrame,
    feature_cols: Optional[list[str]] = None,
) -> ClusteringDataset:
    """Prepare daily user-day observations for Experiment A clustering.

    Engineers features if missing, imputes missing feature values using median,
    and segregates identifiers/dates into metadata.
    """
    # Ensure engineered features exist
    if "task_completion_rate" not in df.columns:
        processed_df = engineer_features(df, include_target_derived=False)
    else:
        processed_df = df.copy()

    features = feature_cols or DAILY_CLUSTERING_FEATURES

    # Verify no forbidden target/identifier columns are included
    for col in features:
        if col in TARGET_COLUMNS or col in TARGET_DERIVED_COLUMNS:
            raise ValueError(f"Target leakage violation: '{col}' cannot be used in clustering.")
        if col in IDENTIFIER_COLUMNS or col in TIMESTAMP_COLUMNS:
            raise ValueError(f"Identifier/timestamp violation: '{col}' cannot be used in clustering.")
        if col not in processed_df.columns:
            raise ValueError(f"Required clustering feature '{col}' is missing from DataFrame.")

    # Extract X and impute any remaining NaNs with column medians
    X_raw = processed_df[features].copy()
    medians = X_raw.median(skipna=True).to_dict()
    X = X_raw.fillna(medians)

    # Extract metadata
    meta_cols = [c for c in ["user_id", "record_date", "productivity_score"] if c in processed_df.columns]
    metadata = processed_df[meta_cols].copy()

    return ClusteringDataset(
        X=X,
        metadata=metadata,
        feature_names=list(features),
        experiment_type="daily_records",
    )


def prepare_user_level_clustering_data(
    df: pd.DataFrame,
) -> ClusteringDataset:
    """Aggregate daily records by user_id for Experiment B user-level clustering.

    Computes longitudinal mean and variability metrics per simulated user.
    """
    if "user_id" not in df.columns:
        raise ValueError("Missing 'user_id' column required for user-level aggregation.")

    # Ensure engineered features exist
    if "task_completion_rate" not in df.columns:
        processed_df = engineer_features(df, include_target_derived=False)
    else:
        processed_df = df.copy()

    # Compute user-level aggregates
    user_rows = []
    for user_id, u_df in processed_df.groupby("user_id"):
        mean_focus = float(u_df["focus_duration_hours"].mean())
        mean_sleep = float(u_df["sleep_hours"].mean())
        mean_screen = float(u_df["screen_time_hours"].mean())
        mean_session = float(u_df["work_session_duration_hours"].mean())
        mean_comp = float(u_df["task_completion_rate"].dropna().mean()) if u_df["task_completion_rate"].notna().any() else 0.5
        mean_interrupt = float(u_df["interruption_count"].mean())
        focus_var = float(u_df["focus_duration_hours"].std()) if len(u_df) > 1 else 0.0
        consistency = float((u_df["work_session_duration_hours"] > 0).mean())

        user_rows.append({
            "user_id": user_id,
            "mean_focus_hours": round(mean_focus, 3),
            "mean_sleep_hours": round(mean_sleep, 3),
            "mean_screen_time_hours": round(mean_screen, 3),
            "mean_work_session_hours": round(mean_session, 3),
            "mean_task_completion_rate": round(mean_comp, 3),
            "mean_interruption_count": round(mean_interrupt, 3),
            "focus_variability_std": round(focus_var, 3),
            "work_session_consistency": round(consistency, 3),
            "total_observed_days": len(u_df),
        })

    agg_df = pd.DataFrame(user_rows)

    X = agg_df[USER_AGGREGATED_CLUSTERING_FEATURES].copy()
    metadata = agg_df[["user_id", "total_observed_days"]].copy()

    return ClusteringDataset(
        X=X,
        metadata=metadata,
        feature_names=list(USER_AGGREGATED_CLUSTERING_FEATURES),
        experiment_type="user_aggregated",
    )


def generate_feature_selection_markdown_report() -> str:
    """Generate Markdown report documenting clustering feature selection and exclusion rationale."""
    lines = [
        "# Behavioural Clustering — Feature Selection & Leakage Rationale",
        "",
        "## 1. Unsupervised Clustering Philosophy",
        "Clustering in the AI Cognitive Digital Twin is purely unsupervised exploratory discovery.",
        "Its objective is to uncover latent, natural behavioural regimes (in daily records) and",
        "phenotypical working styles (in user-level profiles) without any supervision from target labels.",
        "",
        "## 2. Selected Feature Sets",
        "",
        "### 2.1 Experiment A: Daily Record Clustering Features (10 Features)",
        "| Feature Name | Theoretical Role | Range | Handling |",
        "|---|---|---|---|",
        "| `sleep_hours` | Recovery & rest proxy | [3.0, 11.0] | Standardized |",
        "| `focus_duration_hours` | Deep work volume | [0.0, 12.0] | Standardized |",
        "| `screen_time_hours` | Digital exposure | [0.0, 16.0] | Standardized |",
        "| `task_difficulty_avg` | Cognitive complexity | [1.0, 5.0] | Standardized |",
        "| `work_session_duration_hours` | Gross work window | [0.0, 16.0] | Standardized |",
        "| `inactivity_duration_hours` | Idleness/fatigue proxy | [0.0, 16.0] | Standardized |",
        "| `interruption_count` | Context-switching friction | [0, 20+] | Standardized |",
        "| `task_completion_rate` | Daily execution efficiency | [0.0, 1.0] | Standardized (median imputed) |",
        "| `work_session_utilization` | Proportion of session in deep focus | [0.0, 1.0] | Standardized |",
        "| `inactivity_ratio` | Proportion of session inactive | [0.0, 1.0] | Standardized |",
        "",
        "### 2.2 Experiment B: User-Level Aggregated Features (8 Features)",
        "| Feature Name | Aggregation Method | Behavioural Interpretation |",
        "|---|---|---|",
        "| `mean_focus_hours` | Mean over 90 days | Baseline sustained focus capacity |",
        "| `mean_sleep_hours` | Mean over 90 days | Baseline physiological recovery |",
        "| `mean_screen_time_hours` | Mean over 90 days | Chronic digital exposure baseline |",
        "| `mean_work_session_hours` | Mean over 90 days | Habitual work session length |",
        "| `mean_task_completion_rate`| Mean over 90 days | Characteristic execution reliability |",
        "| `mean_interruption_count` | Mean over 90 days | Characteristic disruption vulnerability |",
        "| `focus_variability_std` | Standard deviation over 90 days | Routine stability vs. volatility |",
        "| `work_session_consistency`| Proportion of days with >0 sessions | Routine commitment / discipline |",
        "",
        "## 3. Excluded Columns & Leakage Rationale",
        "| Excluded Column | Reason for Exclusion |",
        "|---|---|",
    ]

    for col, reason in FEATURE_EXCLUSION_REGISTRY.items():
        lines.append(f"| `{col}` | {reason} |")

    return "\n".join(lines)
