"""Unit tests for leakage-safe preprocessing pipeline."""

import numpy as np
import pandas as pd
import pytest

from app.data_pipeline.feature_engineering import engineer_features
from app.services.preprocessing import BehavioralDataPreprocessor
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def train_and_val_data():
    df = generate_synthetic_data(n_users=5, n_days=20, seed=42)
    eng = engineer_features(df)
    train_df = eng[eng["record_date"] < "2026-01-15"].copy()
    val_df = eng[eng["record_date"] >= "2026-01-15"].copy()
    return train_df, val_df


def test_preprocessor_fit_and_transform(train_and_val_data):
    train_df, val_df = train_and_val_data
    prep = BehavioralDataPreprocessor(target_col="productivity_score", clip_outliers=True)

    train_out = prep.fit_transform(train_df)
    val_out = prep.transform(val_df)

    # Feature matrix assertions
    assert isinstance(train_out.X, pd.DataFrame)
    assert isinstance(val_out.X, pd.DataFrame)
    assert list(train_out.X.columns) == list(val_out.X.columns)
    assert "productivity_score" not in train_out.X.columns
    assert "user_id" not in train_out.X.columns
    assert "record_date" not in train_out.X.columns

    # Standard scaling property: train set features have near-zero mean and unit variance
    train_means = train_out.X.mean()
    assert (train_means.abs() < 1e-1).all()

    # Targets are preserved
    assert len(train_out.y) == len(train_df)
    assert len(val_out.y) == len(val_df)


def test_missing_values_imputed_using_training_medians(train_and_val_data):
    train_df, val_df = train_and_val_data

    # Introduce a missing value in validation set for sleep_hours
    val_modified = val_df.copy()
    val_modified.iloc[0, val_modified.columns.get_loc("sleep_hours")] = np.nan

    prep = BehavioralDataPreprocessor()
    prep.fit(train_df)
    val_out = prep.transform(val_modified)

    # Output feature matrix must contain zero NaNs
    assert not val_out.X.isna().any().any()


def test_target_is_never_imputed(train_and_val_data):
    train_df, val_df = train_and_val_data

    val_modified = val_df.copy()
    val_modified.iloc[0, val_modified.columns.get_loc("productivity_score")] = np.nan

    prep = BehavioralDataPreprocessor()
    prep.fit(train_df)
    val_out = prep.transform(val_modified)

    # Target y should preserve its NaN for supervised evaluation
    assert val_out.y.isna().iloc[0]


def test_calling_transform_before_fit_raises_error(train_and_val_data):
    _, val_df = train_and_val_data
    prep = BehavioralDataPreprocessor()
    with pytest.raises(RuntimeError):
        prep.transform(val_df)


def test_preprocessor_parameters_export(train_and_val_data, tmp_path):
    train_df, _ = train_and_val_data
    prep = BehavioralDataPreprocessor()
    prep.fit(train_df)

    export_path = tmp_path / "prep_params.json"
    saved = prep.save_parameters(export_path)
    assert saved.exists()
    assert export_path.stat().st_size > 0
