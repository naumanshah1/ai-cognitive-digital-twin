"""Unit tests for dataset schema validation and quality reporting."""

import numpy as np
import pandas as pd
import pytest

from app.data_pipeline.schema import RAW_COLUMNS
from app.services.data_validation import (
    DataValidationError,
    validate_behavioral_data,
)
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def sample_valid_df() -> pd.DataFrame:
    return generate_synthetic_data(n_users=3, n_days=5, seed=42)


def test_valid_data_passes_validation(sample_valid_df):
    report = validate_behavioral_data(sample_valid_df, strict=True)
    assert report.is_valid
    assert len(report.errors) == 0
    assert report.valid_row_count == len(sample_valid_df)
    assert report.invalid_row_count == 0


def test_missing_required_column_detected(sample_valid_df):
    df = sample_valid_df.drop(columns=["sleep_hours"])
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("sleep_hours" in err for err in report.errors)


def test_missing_required_value_detected(sample_valid_df):
    df = sample_valid_df.copy()
    df.loc[0, "sleep_hours"] = np.nan
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("sleep_hours" in err for err in report.errors)
    assert report.invalid_row_count >= 1


def test_empty_user_id_detected(sample_valid_df):
    df = sample_valid_df.copy()
    df.loc[0, "user_id"] = "   "
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("user_id" in err for err in report.errors)


def test_duplicate_user_date_pairs_detected(sample_valid_df):
    # Duplicate first row
    df = pd.concat([sample_valid_df, sample_valid_df.iloc[[0]]], ignore_index=True)
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert report.duplicate_count >= 2
    assert any("duplicate" in err.lower() for err in report.errors)


def test_invalid_date_format_detected(sample_valid_df):
    df = sample_valid_df.copy()
    df.loc[0, "record_date"] = "not-a-valid-date"
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("malformed date" in err.lower() for err in report.errors)


def test_out_of_range_values_detected(sample_valid_df):
    df = sample_valid_df.copy()
    # Negative sleep hours
    df.loc[0, "sleep_hours"] = -1.5
    # Productivity score > 100
    df.loc[1, "productivity_score"] = 105.0
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("sleep_hours" in err for err in report.errors)
    assert any("productivity_score" in err for err in report.errors)


def test_non_integer_counts_detected(sample_valid_df):
    df = sample_valid_df.copy()
    df["tasks_completed"] = df["tasks_completed"].astype(float)
    df.loc[0, "tasks_completed"] = 2.7
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("non-integer" in err.lower() for err in report.errors)


def test_infinite_values_detected(sample_valid_df):
    df = sample_valid_df.copy()
    df.loc[0, "focus_duration_hours"] = np.inf
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("infinite" in err.lower() for err in report.errors)


def test_tasks_completed_exceeding_planned_detected(sample_valid_df):
    df = sample_valid_df.copy()
    df.loc[0, "tasks_planned"] = 3
    df.loc[0, "tasks_completed"] = 5
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("tasks_completed > tasks_planned" in err for err in report.errors)


def test_inactivity_exceeding_session_detected(sample_valid_df):
    df = sample_valid_df.copy()
    df.loc[0, "work_session_duration_hours"] = 4.0
    df.loc[0, "inactivity_duration_hours"] = 6.0
    report = validate_behavioral_data(df)
    assert not report.is_valid
    assert any("inactivity_duration_hours > work_session_duration_hours" in err for err in report.errors)


def test_optional_ratings_can_be_missing(sample_valid_df):
    # Optional ratings null values should not trigger errors
    df = sample_valid_df.copy()
    df.loc[0, "sleep_quality"] = np.nan
    df.loc[0, "mood_score"] = np.nan
    df.loc[0, "perceived_stress"] = np.nan
    report = validate_behavioral_data(df, strict=True)
    assert report.is_valid
    assert report.missing_counts["sleep_quality"] >= 1


def test_strict_mode_raises_exception_on_error(sample_valid_df):
    df = sample_valid_df.copy()
    df.loc[0, "sleep_hours"] = -5.0
    with pytest.raises(DataValidationError):
        validate_behavioral_data(df, strict=True)


def test_quality_report_formatting(sample_valid_df):
    report = validate_behavioral_data(sample_valid_df)
    markdown = report.to_markdown()
    assert "# Data Quality Report" in markdown
    assert "**Validation Status:** PASSED" in markdown
    json_str = report.to_json()
    assert '"is_valid": true' in json_str
