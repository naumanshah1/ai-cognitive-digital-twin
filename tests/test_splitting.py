"""Unit tests for chronological and user-grouped dataset splitting."""

import pandas as pd
import pytest

from app.data_pipeline.splitting import chronological_split, unseen_user_split
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    return generate_synthetic_data(n_users=5, n_days=30, seed=42)


def test_chronological_split_strict_date_ordering(sample_dataset):
    train_df, val_df, test_df, report = chronological_split(
        sample_dataset,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
    )

    # Dates must not overlap
    train_max = pd.to_datetime(train_df["record_date"]).max()
    val_min = pd.to_datetime(val_df["record_date"]).min()
    val_max = pd.to_datetime(val_df["record_date"]).max()
    test_min = pd.to_datetime(test_df["record_date"]).min()

    assert train_max < val_min
    assert val_min <= val_max
    assert val_max < test_min
    assert not report.date_overlap_detected


def test_chronological_split_preserves_all_rows(sample_dataset):
    train_df, val_df, test_df, report = chronological_split(sample_dataset)
    total_split_rows = len(train_df) + len(val_df) + len(test_df)
    assert total_split_rows == len(sample_dataset)
    assert report.total_rows == len(sample_dataset)


def test_chronological_split_ratios(sample_dataset):
    train_df, val_df, test_df, _ = chronological_split(
        sample_dataset,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
    )

    n_total = len(sample_dataset)
    # Proportions should be approximately 70%, 15%, 15% (within 5% tolerance due to discrete dates)
    assert abs((len(train_df) / n_total) - 0.70) < 0.05
    assert abs((len(val_df) / n_total) - 0.15) < 0.05
    assert abs((len(test_df) / n_total) - 0.15) < 0.05


def test_small_dataset_rejection():
    # Only 2 rows
    small_df = pd.DataFrame({
        "user_id": ["u1", "u1"],
        "record_date": ["2026-01-01", "2026-01-02"],
        "productivity_score": [50.0, 60.0],
    })
    with pytest.raises(ValueError):
        chronological_split(small_df)


def test_invalid_ratio_sum_rejection(sample_dataset):
    with pytest.raises(ValueError):
        chronological_split(sample_dataset, train_ratio=0.80, val_ratio=0.20, test_ratio=0.10)


def test_unseen_user_split_no_user_overlap(sample_dataset):
    train_df, val_df, test_df, report = unseen_user_split(
        sample_dataset,
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
    )

    train_users = set(train_df["user_id"])
    val_users = set(val_df["user_id"])
    test_users = set(test_df["user_id"])

    # Disjoint user sets
    assert train_users.isdisjoint(val_users)
    assert val_users.isdisjoint(test_users)
    assert train_users.isdisjoint(test_users)
    assert report["train_users"] + report["val_users"] + report["test_users"] == sample_dataset["user_id"].nunique()
