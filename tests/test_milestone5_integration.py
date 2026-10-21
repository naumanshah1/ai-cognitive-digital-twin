"""Integration tests for Milestone 5 end-to-end temporal modeling & LSTM execution."""

from pathlib import Path
import pytest

from scripts.run_milestone5 import run_milestone5_experiments


def test_milestone5_end_to_end_pipeline_execution(tmp_path):
    """Execute full Milestone 5 workflow on small reproducible dataset."""
    metadata = run_milestone5_experiments(
        n_users=3,
        n_days=20,
        seed=42,
        lookback=5,
        compare_lookback=10,
        hidden_dim=16,
        epochs=5,
        lr=0.01,
        output_root=tmp_path,
    )

    # 1. Assert metadata structure
    assert "task_definition" in metadata
    assert metadata["task_definition"]["forecast_horizon_days"] == 1
    assert "candidate_evaluations" in metadata
    assert "model_selection" in metadata

    candidates = metadata["candidate_evaluations"]
    assert "training_mean" in candidates
    assert "persistence" in candidates
    assert "lagged_ridge" in candidates
    assert "lstm_l5" in candidates
    assert "lstm_l10" in candidates

    # 2. Assert generated files and directories
    exp_dir = tmp_path / "research" / "experiments" / "milestone5"
    results_dir = exp_dir / "results"
    artifacts_dir = tmp_path / "artifacts"

    report_file = exp_dir / "temporal_modeling_report.md"
    metadata_file = exp_dir / "experiment_metadata.json"

    assert report_file.exists()
    assert metadata_file.exists()

    # 3. Assert diagnostic plots
    expected_plots = [
        "loss_curves.png",
        "forecasting_model_comparison.png",
        "actual_vs_predicted.png",
        "residuals_distribution.png",
    ]
    for plot_name in expected_plots:
        assert (results_dir / plot_name).exists(), f"Plot {plot_name} was not generated!"

    # 4. Assert model artifacts
    assert (artifacts_dir / "lstm_forecaster_l5.pt").exists()
    assert (artifacts_dir / "lstm_forecaster_l10.pt").exists()

    # 5. Assert strict test metrics exist for selected champion
    sel_metrics = metadata["model_selection"]["test_metrics"]
    assert sel_metrics is not None
    assert sel_metrics["sample_count"] > 0
    assert sel_metrics["rmse"] > 0.0
