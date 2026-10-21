"""Unit tests for feature engineering and target leakage prevention."""

import numpy as np
import pandas as pd
import pytest

from app.data_pipeline.feature_engineering import (
    TargetLeakageError,
    audit_feature_leakage,
    engineer_features,
    get_safe_predictor_matrix,
)
from app.data_pipeline.schema import TARGET_DERIVED_COLUMNS
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    return generate_synthetic_data(n_users=3, n_days=10, seed=42)


def test_task_completion_rate_calculation(sample_raw_df):
    df = engineer_features(sample_raw_df)
    assert "task_completion_rate" in df.columns
    # Check bounded within [0, 1] for planned > 0
    valid_rates = df["task_completion_rate"].dropna()
    assert (valid_rates >= 0.0).all()
    assert (valid_rates <= 1.0).all()


def test_zero_planned_tasks_handled_without_division_by_zero(sample_raw_df):
    df = sample_raw_df.copy()
    df.loc[0, "tasks_planned"] = 0
    df.loc[0, "tasks_completed"] = 0
    res = engineer_features(df)
    assert np.isnan(res.loc[0, "task_completion_rate"])


def test_work_session_utilization_edge_cases(sample_raw_df):
    df = sample_raw_df.copy()
    df.loc[0, "work_session_duration_hours"] = 0.0
    df.loc[0, "focus_duration_hours"] = 0.0
    res = engineer_features(df)
    assert res.loc[0, "work_session_utilization"] == 0.0
    assert res.loc[0, "inactivity_ratio"] == 0.0


def test_calendar_features(sample_raw_df):
    df = engineer_features(sample_raw_df)
    assert "day_of_week" in df.columns
    assert "is_weekend" in df.columns
    assert df["day_of_week"].between(0, 6).all()
    assert df["is_weekend"].isin([0, 1]).all()


def test_rolling_historical_features_use_prior_records_only(sample_raw_df):
    # Sort and engineer
    df = engineer_features(sample_raw_df, min_history_periods=3, rolling_window_days=7)

    # For day 0 of any user, prior history is 0 days -> rolling std must be NaN
    user_first_day = df.groupby("user_id").nth(0)
    assert user_first_day["rolling_focus_std_7d"].isna().all()

    # For day 1 and 2, history is 1 and 2 days, which is < min_history_periods (3) -> must be NaN
    user_day_1 = df.groupby("user_id").nth(1)
    assert user_day_1["rolling_focus_std_7d"].isna().all()

    # Once history reaches 3 days (by day 3, index 3), rolling std should be numeric
    user_day_3 = df.groupby("user_id").nth(3)
    assert user_day_3["rolling_focus_std_7d"].notna().all()


def test_grouped_calculations_isolated_between_users():
    # User 1 has focus = 1.0 every day, User 2 has focus = 10.0 every day
    df1 = generate_synthetic_data(n_users=1, n_days=5, seed=1)
    df2 = generate_synthetic_data(n_users=1, n_days=5, seed=2)
    df2["user_id"] = "synthetic_0002"

    df1["focus_duration_hours"] = 1.0
    df2["focus_duration_hours"] = 10.0

    combined = pd.concat([df1, df2], ignore_index=True)
    res = engineer_features(combined, min_history_periods=2, rolling_window_days=5)

    # Standard deviation of constant series is 0.0 (if users cross-contaminated, std would be > 0)
    user1_stds = res[res["user_id"] == "synthetic_0001"]["rolling_focus_std_7d"].dropna()
    user2_stds = res[res["user_id"] == "synthetic_0002"]["rolling_focus_std_7d"].dropna()
    assert (user1_stds == 0.0).all()
    assert (user2_stds == 0.0).all()


def test_target_leakage_audit_rejects_target_column():
    bad_features = ["sleep_hours", "focus_duration_hours", "productivity_score"]
    with pytest.raises(TargetLeakageError) as exc_info:
        audit_feature_leakage(bad_features, target_col="productivity_score")
    assert "Target column 'productivity_score'" in str(exc_info.value)


def test_target_leakage_audit_rejects_target_derived_features():
    for derived in TARGET_DERIVED_COLUMNS:
        bad_features = ["sleep_hours", derived]
        with pytest.raises(TargetLeakageError) as exc_info:
            audit_feature_leakage(bad_features, target_col="productivity_score")
        assert derived in str(exc_info.value)


def test_target_leakage_audit_rejects_identifiers_and_timestamps():
    with pytest.raises(TargetLeakageError):
        audit_feature_leakage(["user_id", "sleep_hours"])
    with pytest.raises(TargetLeakageError):
        audit_feature_leakage(["record_date", "sleep_hours"])


def test_get_safe_predictor_matrix_excludes_forbidden_columns(sample_raw_df):
    eng = engineer_features(sample_raw_df)
    X, y, meta = get_safe_predictor_matrix(eng, target_col="productivity_score")

    assert "productivity_score" not in X.columns
    assert "user_id" not in X.columns
    assert "record_date" not in X.columns
    for derived in TARGET_DERIVED_COLUMNS:
        assert derived not in X.columns

    assert y is not None
    assert len(X) == len(sample_raw_df)
    assert len(y) == len(sample_raw_df)
    assert "user_id" in meta.columns
    assert "record_date" in meta.columns
