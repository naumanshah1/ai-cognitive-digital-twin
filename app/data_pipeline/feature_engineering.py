"""Feature engineering and target leakage audit for behavioural records.

Computes task completion rates, session utilization, rolling historical metrics
using strictly prior observations, and performs target leakage audits.
"""

from typing import Iterable, Optional
import numpy as np
import pandas as pd

from app.data_pipeline.schema import (
    ENGINEERED_FEATURE_COLUMNS,
    EXCLUDED_FROM_PREDICTORS,
    IDENTIFIER_COLUMNS,
    PREDICTOR_COLUMNS,
    TARGET_COLUMNS,
    TARGET_DERIVED_COLUMNS,
    TIMESTAMP_COLUMNS,
)


class TargetLeakageError(ValueError):
    """Raised when target or target-derived columns are illegally included in predictors."""
    pass


def engineer_features(
    df: pd.DataFrame,
    min_history_periods: int = 3,
    rolling_window_days: int = 7,
    include_target_derived: bool = True,
) -> pd.DataFrame:
    """Engineer behavioural and temporal features with strict leakage prevention.

    Historical rolling statistics are calculated grouped by user_id and strictly
    shifted by 1 day so that current or future observations never leak into the feature.

    Args:
        df: Input DataFrame containing raw behavioural records.
        min_history_periods: Minimum prior days required before computing rolling stats.
        rolling_window_days: Window size in days for historical aggregates.
        include_target_derived: If True, computes historical target-derived features
            (for separate research analyses), which must be excluded from predictive modeling.

    Returns:
        DataFrame with original columns plus engineered features.
    """
    out = df.copy()

    # Ensure record_date is parsed as datetime for correct chronological sorting
    if "record_date" in out.columns:
        date_series = pd.to_datetime(out["record_date"], errors="coerce")
    else:
        raise ValueError("Missing 'record_date' column for feature engineering.")

    # Sort strictly by (user_id, date) to ensure temporal integrity
    if "user_id" in out.columns:
        out = out.assign(_dt=date_series).sort_values(["user_id", "_dt"]).drop(columns=["_dt"])
    else:
        out = out.assign(_dt=date_series).sort_values(["_dt"]).drop(columns=["_dt"])

    # 1. Task completion rate
    if "tasks_completed" in out.columns and "tasks_planned" in out.columns:
        # Zero planned tasks has a mathematically undefined completion rate -> np.nan
        planned = out["tasks_planned"].astype(float)
        completed = out["tasks_completed"].astype(float)
        completion_rate = np.where(
            planned > 0,
            np.clip(completed / planned, 0.0, 1.0),
            np.nan,
        )
        out["task_completion_rate"] = np.round(completion_rate, 4)

    # 2. Work session utilization & Inactivity ratio
    if "focus_duration_hours" in out.columns and "work_session_duration_hours" in out.columns:
        session = out["work_session_duration_hours"].astype(float)
        focus = out["focus_duration_hours"].astype(float)
        utilization = np.where(
            session > 0,
            np.clip(focus / session, 0.0, 1.0),
            0.0,
        )
        out["work_session_utilization"] = np.round(utilization, 4)

    if "inactivity_duration_hours" in out.columns and "work_session_duration_hours" in out.columns:
        session = out["work_session_duration_hours"].astype(float)
        inactivity = out["inactivity_duration_hours"].astype(float)
        inactivity_ratio = np.where(
            session > 0,
            np.clip(inactivity / session, 0.0, 1.0),
            0.0,
        )
        out["inactivity_ratio"] = np.round(inactivity_ratio, 4)

    # 3. Calendar & Temporal features
    dt_index = pd.to_datetime(out["record_date"])
    out["day_of_week"] = dt_index.dt.dayofweek.astype(int)
    out["is_weekend"] = dt_index.dt.dayofweek.isin([5, 6]).astype(int)

    # 4. Grouped historical features (prior records only: shift(1) avoids same-day leakage)
    if "user_id" in out.columns:
        grouped = out.groupby("user_id", group_keys=False)

        # 4.1 Prior focus stability (rolling std of previous days)
        if "focus_duration_hours" in out.columns:
            prior_focus = grouped["focus_duration_hours"].shift(1)
            rolling_focus_std = (
                prior_focus.groupby(out["user_id"])
                .rolling(window=rolling_window_days, min_periods=min_history_periods)
                .std()
                .reset_index(level=0, drop=True)
            )
            out["rolling_focus_std_7d"] = np.round(rolling_focus_std, 4)

        # 4.2 Work session frequency (fraction of past 7 days with >0 work sessions)
        if "work_session_duration_hours" in out.columns:
            has_session = (out["work_session_duration_hours"] > 0).astype(float)
            prior_session = has_session.groupby(out["user_id"]).shift(1)
            rolling_freq = (
                prior_session.groupby(out["user_id"])
                .rolling(window=rolling_window_days, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )
            out["work_session_frequency_7d"] = np.round(rolling_freq, 4)

        # 4.3 Target-derived features (clearly marked for exclusion from predictors)
        if include_target_derived and "productivity_score" in out.columns:
            prior_prod = grouped["productivity_score"].shift(1)
            rolling_prod_mean = (
                prior_prod.groupby(out["user_id"])
                .rolling(window=rolling_window_days, min_periods=min_history_periods)
                .mean()
                .reset_index(level=0, drop=True)
            )
            out["rolling_productivity_mean_7d"] = np.round(rolling_prod_mean, 4)
            # Change vs prior rolling mean
            out["productivity_change_7d"] = np.round(prior_prod - rolling_prod_mean, 4)

    return out


def audit_feature_leakage(
    candidate_features: Iterable[str],
    target_col: str = "productivity_score",
    allow_target_derived: bool = False,
) -> list[str]:
    """Verify that candidate predictors do not contain target, target-derived, or ID columns.

    Raises TargetLeakageError if leakage is detected.
    Returns the verified list of safe predictor features.
    """
    candidates = list(candidate_features)
    leaked_items: list[str] = []

    for feat in candidates:
        # Check target
        if feat == target_col or feat in TARGET_COLUMNS:
            leaked_items.append(f"Target column '{feat}'")
        # Check target-derived
        elif not allow_target_derived and feat in TARGET_DERIVED_COLUMNS:
            leaked_items.append(f"Target-derived historical feature '{feat}'")
        # Check identifiers
        elif feat in IDENTIFIER_COLUMNS:
            leaked_items.append(f"Identifier column '{feat}'")
        # Check timestamps
        elif feat in TIMESTAMP_COLUMNS:
            leaked_items.append(f"Timestamp column '{feat}'")

    if leaked_items:
        raise TargetLeakageError(
            f"Target leakage violation detected in predictor features: {leaked_items}. "
            f"These columns must be strictly excluded from model input matrices."
        )

    return candidates


def get_safe_predictor_matrix(
    df: pd.DataFrame,
    target_col: str = "productivity_score",
) -> tuple[pd.DataFrame, Optional[pd.Series], pd.DataFrame]:
    """Split DataFrame into safe predictor matrix X, target y, and metadata DataFrame.

    Ensures no leakage occurs into X.
    """
    # Exclude all forbidden columns from predictors
    forbidden = set(EXCLUDED_FROM_PREDICTORS)
    forbidden.add(target_col)

    predictor_cols = [c for c in df.columns if c not in forbidden]
    audit_feature_leakage(predictor_cols, target_col=target_col)

    X = df[predictor_cols].copy()
    y = df[target_col].copy() if target_col in df.columns else None

    meta_cols = [c for c in df.columns if c in IDENTIFIER_COLUMNS or c in TIMESTAMP_COLUMNS]
    metadata = df[meta_cols].copy()

    return X, y, metadata
