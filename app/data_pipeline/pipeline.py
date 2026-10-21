"""End-to-end data pipeline orchestrator for AI Cognitive Digital Twin."""

from pathlib import Path
from typing import Any, Optional
import pandas as pd

from app.data_pipeline.feature_engineering import engineer_features, get_safe_predictor_matrix
from app.data_pipeline.quality_report import DataQualityReport
from app.data_pipeline.schema import SCHEMA_VERSION
from app.data_pipeline.splitting import DataSplitReport, chronological_split
from app.services.data_validation import validate_behavioral_data
from app.services.preprocessing import BehavioralDataPreprocessor
from app.services.synthetic_data import generate_synthetic_data, save_synthetic_data


def run_data_pipeline(
    n_users: int = 50,
    n_days: int = 90,
    seed: int = 42,
    output_dir: str | Path = "data",
    scenario: str = "baseline",
    overwrite: bool = True,
    strict_validation: bool = True,
) -> dict[str, Any]:
    """Execute the complete Milestone 2 data pipeline end-to-end.

    Steps:
    1. Generate reproducible synthetic dataset
    2. Validate against schema and domain constraints
    3. Export raw synthetic data with provenance metadata
    4. Engineer features with chronological protection (no future leakage)
    5. Split into non-overlapping chronological train/val/test partitions
    6. Fit preprocessor on train set ONLY
    7. Preprocess train, validation, and test partitions
    8. Export processed datasets and reproducibility artifacts

    Returns a comprehensive execution summary dictionary.
    """
    out_path = Path(output_dir)
    synthetic_dir = out_path / "synthetic"
    processed_dir = out_path / "processed"
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generation
    raw_df = generate_synthetic_data(
        n_users=n_users,
        n_days=n_days,
        seed=seed,
        scenario=scenario,
    )

    # 2. Validation
    quality_report = validate_behavioral_data(raw_df, strict=strict_validation)

    # 3. Save raw synthetic dataset
    raw_csv_path = synthetic_dir / "behavioral_records.csv"
    save_synthetic_data(
        raw_df,
        output_path=raw_csv_path,
        overwrite=overwrite,
        save_metadata=True,
    )

    # 4. Feature engineering
    engineered_df = engineer_features(raw_df)

    # 5. Chronological splitting
    train_raw, val_raw, test_raw, split_report = chronological_split(
        engineered_df,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
    )

    # 6. Fit preprocessor on training data only
    preprocessor = BehavioralDataPreprocessor(
        target_col="productivity_score",
        clip_outliers=True,
    )
    train_prep = preprocessor.fit_transform(train_raw)

    # 7. Transform validation and test data using training parameters
    val_prep = preprocessor.transform(val_raw)
    test_prep = preprocessor.transform(test_raw)

    # 8. Export processed partitions
    train_prep.X.to_csv(processed_dir / "train_features.csv", index=False)
    if train_prep.y is not None:
        train_prep.y.to_csv(processed_dir / "train_target.csv", index=False)
    train_prep.metadata.to_csv(processed_dir / "train_metadata.csv", index=False)

    val_prep.X.to_csv(processed_dir / "val_features.csv", index=False)
    if val_prep.y is not None:
        val_prep.y.to_csv(processed_dir / "val_target.csv", index=False)
    val_prep.metadata.to_csv(processed_dir / "val_metadata.csv", index=False)

    test_prep.X.to_csv(processed_dir / "test_features.csv", index=False)
    if test_prep.y is not None:
        test_prep.y.to_csv(processed_dir / "test_target.csv", index=False)
    test_prep.metadata.to_csv(processed_dir / "test_metadata.csv", index=False)

    preprocessor.save_parameters(processed_dir / "preprocessing_parameters.json")

    with open(processed_dir / "data_split_report.json", "w", encoding="utf-8") as f:
        f.write(split_report.to_json())

    with open(processed_dir / "data_quality_report.json", "w", encoding="utf-8") as f:
        f.write(quality_report.to_json())

    return {
        "schema_version": SCHEMA_VERSION,
        "input_rows": len(raw_df),
        "input_columns": len(raw_df.columns),
        "engineered_columns": len(engineered_df.columns),
        "predictor_features_count": len(preprocessor.feature_names_),
        "predictor_feature_names": preprocessor.feature_names_,
        "validation_passed": quality_report.is_valid,
        "missing_values_detected": quality_report.missing_counts,
        "split_summary": {
            "train_rows": len(train_prep.X),
            "train_dates": [split_report.train.min_date, split_report.train.max_date],
            "val_rows": len(val_prep.X),
            "val_dates": [split_report.validation.min_date, split_report.validation.max_date],
            "test_rows": len(test_prep.X),
            "test_dates": [split_report.test.min_date, split_report.test.max_date],
        },
        "artifacts_saved": [
            str(raw_csv_path),
            str(raw_csv_path.with_suffix(".metadata.json")),
            str(processed_dir / "train_features.csv"),
            str(processed_dir / "val_features.csv"),
            str(processed_dir / "test_features.csv"),
            str(processed_dir / "preprocessing_parameters.json"),
            str(processed_dir / "data_split_report.json"),
            str(processed_dir / "data_quality_report.json"),
        ],
    }
