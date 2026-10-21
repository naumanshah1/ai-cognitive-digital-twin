"""Integration tests for Milestone 4 end-to-end regression pipeline execution."""

import json
from pathlib import Path
import pytest

from scripts.run_milestone4 import run_milestone4_experiments


def test_milestone4_end_to_end_pipeline_execution(tmp_path):
    # Execute full Milestone 4 workflow with a small reproducible dataset
    metadata = run_milestone4_experiments(
        n_users=4,
        n_days=18,
        seed=42,
        output_root=tmp_path,
        selection_criterion="val_rmse",
    )

    # 1. Assert metadata structure
    assert metadata["dataset"]["n_users"] == 4
    assert metadata["dataset"]["n_days"] == 18
    assert metadata["dataset"]["total_records"] == 72
    assert "candidate_evaluations" in metadata
    assert "model_selection" in metadata
    assert len(metadata["candidate_evaluations"]) >= 3

    # 2. Assert generated reports and directories
    exp_dir = tmp_path / "research" / "experiments" / "milestone4"
    results_dir = exp_dir / "results"
    artifacts_dir = tmp_path / "artifacts"

    report_file = exp_dir / "regression_report.md"
    metadata_file = exp_dir / "experiment_metadata.json"

    assert report_file.exists()
    assert metadata_file.exists()

    # 3. Assert diagnostic plots
    expected_plots = [
        "actual_vs_predicted.png",
        "residuals_vs_predicted.png",
        "residuals_distribution.png",
        "feature_importance_or_coefficients.png",
        "model_comparison_metrics.png",
    ]
    for plot_name in expected_plots:
        assert (results_dir / plot_name).exists(), f"Plot {plot_name} was not generated!"

    # 4. Assert model artifacts
    assert (artifacts_dir / "selected_productivity_regressor.joblib").exists()
    assert (artifacts_dir / "linear_regression.joblib").exists()

    # 5. Assert strict zero target leakage in metadata feature list
    feature_list = metadata["feature_set"]["features"]
    assert "productivity_score" not in feature_list
    assert "rolling_productivity_mean_7d" not in feature_list
    assert "productivity_change_7d" not in feature_list
    assert "user_id" not in feature_list
    assert "record_date" not in feature_list

    # 6. Assert test metrics were computed strictly for selected model
    test_metrics = metadata["model_selection"]["test_metrics"]
    assert test_metrics is not None
    assert test_metrics["sample_count"] > 0
    assert test_metrics["mae"] > 0.0
    assert test_metrics["rmse"] > 0.0
