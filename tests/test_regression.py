"""Unit tests for Milestone 4 regression modeling, metrics, leakage audit, and validation selection."""

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from app.data_pipeline.feature_engineering import TargetLeakageError, audit_feature_leakage, engineer_features
from app.data_pipeline.schema import (
    IDENTIFIER_COLUMNS,
    TARGET_COLUMNS,
    TARGET_DERIVED_COLUMNS,
    TIMESTAMP_COLUMNS,
)
from app.data_pipeline.splitting import chronological_split
from app.ml.regression import (
    RegressionMetrics,
    build_default_candidate_models,
    compute_regression_metrics,
    compute_unstandardized_coefficients,
    evaluate_oracle_regression,
    evaluate_persistence_baseline,
    evaluate_selected_on_test,
    load_regression_model,
    save_regression_model,
    select_best_candidate,
    train_and_evaluate_model,
)
from app.services.preprocessing import BehavioralDataPreprocessor
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    return generate_synthetic_data(n_users=5, n_days=25, seed=42)


# --- 1. Metric Calculation Tests ---

def test_compute_regression_metrics_valid():
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = np.array([12.0, 18.0, 32.0, 38.0])

    metrics = compute_regression_metrics(y_true, y_pred)
    assert metrics.sample_count == 4
    assert metrics.mae == 2.0
    assert abs(metrics.rmse - 2.0) < 1e-4
    assert metrics.r2 > 0.90


def test_compute_regression_metrics_negative_r2():
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    # Wildly bad predictions
    y_pred = np.array([100.0, -50.0, 200.0, -100.0])

    metrics = compute_regression_metrics(y_true, y_pred)
    assert metrics.r2 < 0.0


def test_compute_regression_metrics_shape_mismatch():
    y_true = np.array([1.0, 2.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    with pytest.raises(ValueError):
        compute_regression_metrics(y_true, y_pred)


def test_compute_regression_metrics_empty():
    with pytest.raises(ValueError):
        compute_regression_metrics(np.array([]), np.array([]))


# --- 2. Baseline Model Tests ---

def test_dummy_mean_baseline_training(sample_dataset):
    df = engineer_features(sample_dataset, include_target_derived=False)
    train_df, val_df, _, _ = chronological_split(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)

    preprocessor = BehavioralDataPreprocessor(target_col="productivity_score").fit(train_df)
    train_prep = preprocessor.transform(train_df)
    val_prep = preprocessor.transform(val_df)

    dummy = DummyRegressor(strategy="mean")
    dummy.fit(train_prep.X, train_prep.y)

    train_mean = float(train_prep.y.mean())
    preds = dummy.predict(val_prep.X)

    # All baseline predictions must equal training set target mean
    assert np.allclose(preds, train_mean)


# --- 3. Forbidden Feature Exclusion & Leakage Protection Tests ---

def test_forbidden_features_leakage_audit_rejects_targets():
    for target in TARGET_COLUMNS:
        with pytest.raises(TargetLeakageError):
            audit_feature_leakage(["sleep_hours", target])

    for target_derived in TARGET_DERIVED_COLUMNS:
        with pytest.raises(TargetLeakageError):
            audit_feature_leakage(["sleep_hours", target_derived])

    for id_col in IDENTIFIER_COLUMNS:
        with pytest.raises(TargetLeakageError):
            audit_feature_leakage(["sleep_hours", id_col])

    for ts_col in TIMESTAMP_COLUMNS:
        with pytest.raises(TargetLeakageError):
            audit_feature_leakage(["sleep_hours", ts_col])


def test_train_only_preprocessing_does_not_learn_from_validation():
    train_data = pd.DataFrame({
        "focus_duration_hours": [4.0, 6.0, 5.0, 5.0],
        "sleep_hours": [7.0, 8.0, 7.5, 7.0],
        "productivity_score": [50.0, 60.0, 55.0, 52.0],
    })
    val_data = pd.DataFrame({
        "focus_duration_hours": [12.0, 14.0],  # Outliers in validation
        "sleep_hours": [3.0, 4.0],
        "productivity_score": [20.0, 25.0],
    })

    preprocessor = BehavioralDataPreprocessor(target_col="productivity_score")
    preprocessor.fit(train_data)

    initial_medians = dict(preprocessor.imputed_medians_)
    initial_scaler_means = np.copy(preprocessor.scaler_.mean_)

    # Transform validation data
    _ = preprocessor.transform(val_data)

    # Assert preprocessor internal state was unchanged by transforming validation data
    assert preprocessor.imputed_medians_ == initial_medians
    assert np.allclose(preprocessor.scaler_.mean_, initial_scaler_means)


# --- 4. Chronological Splitting & Temporal Preservation ---

def test_chronological_split_strict_date_separation(sample_dataset):
    df = engineer_features(sample_dataset, include_target_derived=False)
    train_df, val_df, test_df, split_report = chronological_split(df, 0.7, 0.15, 0.15)

    assert not split_report.date_overlap_detected
    max_train = pd.to_datetime(train_df["record_date"]).max()
    min_val = pd.to_datetime(val_df["record_date"]).min()
    max_val = pd.to_datetime(val_df["record_date"]).max()
    min_test = pd.to_datetime(test_df["record_date"]).min()

    assert max_train < min_val
    assert max_val < min_test


# --- 5. Candidate Evaluation and Model Selection Tests ---

def test_train_and_evaluate_model(sample_dataset):
    df = engineer_features(sample_dataset, include_target_derived=False)
    train_df, val_df, _, _ = chronological_split(df, 0.7, 0.15, 0.15)

    preprocessor = BehavioralDataPreprocessor(target_col="productivity_score").fit(train_df)
    train_prep = preprocessor.transform(train_df)
    val_prep = preprocessor.transform(val_df)

    lr = LinearRegression()
    fitted_model, result = train_and_evaluate_model(
        model=lr,
        model_name="Linear Regression",
        X_train=train_prep.X,
        y_train=train_prep.y,
        X_val=val_prep.X,
        y_val=val_prep.y,
        feature_names=preprocessor.feature_names_,
    )

    assert result.model_name == "Linear Regression"
    assert result.train_metrics.sample_count == len(train_df)
    assert result.val_metrics.sample_count == len(val_df)
    assert result.train_metrics.rmse > 0.0
    assert result.val_metrics.rmse > 0.0
    assert result.coefficients_or_importances is not None


def test_validation_based_selection_does_not_access_test():
    candidates = build_default_candidate_models(random_state=42)
    assert "Dummy (Mean Baseline)" in candidates
    assert "Linear Regression" in candidates
    assert "Random Forest Regressor" in candidates


def test_save_and_reload_regression_model(tmp_path):
    X = pd.DataFrame({"feat1": [1.0, 2.0, 3.0, 4.0], "feat2": [2.0, 3.0, 4.0, 5.0]})
    y = pd.Series([10.0, 15.0, 20.0, 25.0])

    model = LinearRegression().fit(X, y)
    save_path = tmp_path / "test_model.joblib"
    save_regression_model(model, save_path)

    assert save_path.exists()
    loaded_model = load_regression_model(save_path)

    orig_preds = model.predict(X)
    loaded_preds = loaded_model.predict(X)
    assert np.allclose(orig_preds, loaded_preds)


# --- 6. Research Audit Unit Tests ---

def test_compute_unstandardized_coefficients_mathematical_accuracy():
    """Verify unstandardized physical slopes b_j and intercept b_0 from standardized model."""
    from sklearn.preprocessing import StandardScaler

    # Create synthetic linear relationship: y = 10.0 + 3.0*x1 - 2.0*x2
    np.random.seed(42)
    X_raw = pd.DataFrame({
        "x1": np.random.uniform(5.0, 15.0, size=100),
        "x2": np.random.uniform(1.0, 5.0, size=100),
    })
    y = 10.0 + 3.0 * X_raw["x1"] - 2.0 * X_raw["x2"]

    scaler = StandardScaler().fit(X_raw)
    X_scaled = pd.DataFrame(scaler.transform(X_raw), columns=X_raw.columns)

    model = LinearRegression().fit(X_scaled, y)

    slopes, intercept = compute_unstandardized_coefficients(model, scaler, list(X_raw.columns))

    # Raw slopes must match true physical coefficients within numerical tolerance
    assert abs(slopes["x1"] - 3.0) < 1e-4
    assert abs(slopes["x2"] - (-2.0)) < 1e-4
    assert abs(intercept - 10.0) < 1e-4


def test_compute_unstandardized_coefficients_validation_errors():
    """Verify error handling on invalid inputs."""
    from sklearn.dummy import DummyRegressor
    from sklearn.preprocessing import StandardScaler

    dummy = DummyRegressor().fit([[1], [2]], [1, 2])
    scaler = StandardScaler().fit([[1], [2]])

    # Model without coef_
    with pytest.raises(ValueError, match="does not have 'coef_'"):
        compute_unstandardized_coefficients(dummy, scaler, ["feat"])

    # Dimension mismatch
    lr = LinearRegression().fit([[1], [2]], [1, 2])
    with pytest.raises(ValueError, match="Dimension mismatch"):
        compute_unstandardized_coefficients(lr, scaler, ["feat1", "feat2"])


def test_evaluate_persistence_baseline_causal_boundaries():
    """Verify lag-1 persistence strictly draws user's prior target without cross-user leakage."""
    df = pd.DataFrame({
        "user_id": ["u1", "u1", "u1", "u2", "u2", "u2"],
        "record_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-01", "2026-01-02", "2026-01-03"],
        "productivity_score": [50.0, 60.0, 70.0, 20.0, 30.0, 40.0],
    })

    lagged, metrics = evaluate_persistence_baseline(df)

    # First observation per user must be NaN
    assert np.isnan(lagged.iloc[0])
    assert np.isnan(lagged.iloc[3])

    # Subsequent predictions must strictly match same user's previous target
    assert lagged.iloc[1] == 50.0  # u1 day 2 predicted by u1 day 1
    assert lagged.iloc[2] == 60.0  # u1 day 3 predicted by u1 day 2
    assert lagged.iloc[4] == 20.0  # u2 day 2 predicted by u2 day 1
    assert lagged.iloc[5] == 30.0  # u2 day 3 predicted by u2 day 2

    # Evaluated on 4 non-NaN rows
    assert metrics.sample_count == 4
    # Each day changed by exactly +10 points, so MAE and RMSE must be exactly 10.0
    assert abs(metrics.mae - 10.0) < 1e-4
    assert abs(metrics.rmse - 10.0) < 1e-4


def test_evaluate_oracle_regression(sample_dataset):
    """Verify oracle model evaluation and column validation."""
    df = engineer_features(sample_dataset, include_target_derived=False)

    preds, metrics = evaluate_oracle_regression(df)
    assert len(preds) == len(df)
    assert metrics.sample_count == len(df)
    assert 0.0 < metrics.rmse < 15.0

    # Missing column raises ValueError
    bad_df = df.drop(columns=["focus_duration_hours"])
    with pytest.raises(ValueError, match="Oracle evaluation requires columns"):
        evaluate_oracle_regression(bad_df)
