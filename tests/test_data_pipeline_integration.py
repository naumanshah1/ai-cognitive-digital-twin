"""Integration test for the entire end-to-end Milestone 2 data pipeline."""

import json
from pathlib import Path
import pandas as pd
import pytest

from app.data_pipeline.pipeline import run_data_pipeline
from app.data_pipeline.schema import (
    IDENTIFIER_COLUMNS,
    TARGET_COLUMNS,
    TARGET_DERIVED_COLUMNS,
    TIMESTAMP_COLUMNS,
)


def test_end_to_end_pipeline_execution(tmp_path):
    summary = run_data_pipeline(
        n_users=4,
        n_days=20,
        seed=42,
        output_dir=tmp_path,
        overwrite=True,
    )

    # 1. Summary assertions
    assert summary["input_rows"] == 80
    assert summary["validation_passed"] is True
    assert summary["engineered_columns"] > summary["input_columns"]
    assert summary["predictor_features_count"] > 10

    # 2. File existence assertions
    synthetic_csv = tmp_path / "synthetic" / "behavioral_records.csv"
    synthetic_meta = tmp_path / "synthetic" / "behavioral_records.metadata.json"
    assert synthetic_csv.exists()
    assert synthetic_meta.exists()

    train_X = pd.read_csv(tmp_path / "processed" / "train_features.csv")
    train_y = pd.read_csv(tmp_path / "processed" / "train_target.csv")
    train_meta = pd.read_csv(tmp_path / "processed" / "train_metadata.csv")

    val_X = pd.read_csv(tmp_path / "processed" / "val_features.csv")
    val_y = pd.read_csv(tmp_path / "processed" / "val_target.csv")
    val_meta = pd.read_csv(tmp_path / "processed" / "val_metadata.csv")

    test_X = pd.read_csv(tmp_path / "processed" / "test_features.csv")
    test_y = pd.read_csv(tmp_path / "processed" / "test_target.csv")
    test_meta = pd.read_csv(tmp_path / "processed" / "test_metadata.csv")

    # 3. Shape and alignment assertions
    assert len(train_X) == len(train_y) == len(train_meta)
    assert len(val_X) == len(val_y) == len(val_meta)
    assert len(test_X) == len(test_y) == len(test_meta)
    assert len(train_X) + len(val_X) + len(test_X) == 80

    # 4. Strict leakage assertions across all feature matrices
    for df_features, partition_name in [(train_X, "train"), (val_X, "val"), (test_X, "test")]:
        for col in TARGET_COLUMNS:
            assert col not in df_features.columns, f"Target '{col}' leaked into {partition_name} features!"
        for col in TARGET_DERIVED_COLUMNS:
            assert col not in df_features.columns, f"Target-derived '{col}' leaked into {partition_name} features!"
        for col in IDENTIFIER_COLUMNS:
            assert col not in df_features.columns, f"Identifier '{col}' leaked into {partition_name} features!"
        for col in TIMESTAMP_COLUMNS:
            assert col not in df_features.columns, f"Timestamp '{col}' leaked into {partition_name} features!"

        # Ensure no NaNs remaining in preprocessed features
        assert not df_features.isna().any().any(), f"Found NaNs in preprocessed {partition_name} features!"

    # 5. Chronological partition ordering assertions
    train_max_date = train_meta["record_date"].max()
    val_min_date = val_meta["record_date"].min()
    val_max_date = val_meta["record_date"].max()
    test_min_date = test_meta["record_date"].min()

    assert train_max_date < val_min_date
    assert val_min_date <= val_max_date
    assert val_max_date < test_min_date

    # 6. Metadata and report validity
    with open(tmp_path / "processed" / "data_quality_report.json", encoding="utf-8") as f:
        qr = json.load(f)
    assert qr["is_valid"] is True
    assert qr["total_rows"] == 80

    with open(tmp_path / "processed" / "data_split_report.json", encoding="utf-8") as f:
        sr = json.load(f)
    assert sr["date_overlap_detected"] is False


def test_pipeline_reproducibility(tmp_path):
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    run_data_pipeline(n_users=3, n_days=10, seed=42, output_dir=dir1)
    run_data_pipeline(n_users=3, n_days=10, seed=42, output_dir=dir2)

    df1 = pd.read_csv(dir1 / "processed" / "train_features.csv")
    df2 = pd.read_csv(dir2 / "processed" / "train_features.csv")

    pd.testing.assert_frame_equal(df1, df2)
