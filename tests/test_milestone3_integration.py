"""End-to-end integration tests for Milestone 3 (EDA and Behavioural Clustering)."""

import json
from pathlib import Path
import pandas as pd
import pytest

from scripts.run_milestone3 import run_milestone3_experiments


def test_milestone3_end_to_end_pipeline_execution(tmp_path):
    # Execute full Milestone 3 pipeline with small dataset into temporary directory
    metadata = run_milestone3_experiments(
        n_users=4,
        n_days=15,
        seed=42,
        output_root=tmp_path,
    )

    # 1. Metadata structure assertions
    assert metadata["dataset"]["n_users"] == 4
    assert metadata["dataset"]["n_days"] == 15
    assert metadata["dataset"]["total_records"] == 60
    assert "experiment_a_daily" in metadata
    assert "experiment_b_user_level" in metadata

    # 2. File and report existence assertions
    exp_dir = tmp_path / "research" / "experiments" / "milestone3"
    results_dir = exp_dir / "results"
    artifacts_dir = tmp_path / "artifacts"

    eda_report = exp_dir / "eda_report.md"
    feat_sel_report = exp_dir / "feature_selection.md"
    clustering_report = exp_dir / "clustering_report.md"
    metadata_file = exp_dir / "experiment_metadata.json"

    assert eda_report.exists()
    assert feat_sel_report.exists()
    assert clustering_report.exists()
    assert metadata_file.exists()

    # 3. Model artifact existence
    assert (artifacts_dir / "daily_kmeans_k2.joblib").exists()
    assert (artifacts_dir / "daily_kmeans_k3.joblib").exists()
    assert (artifacts_dir / "user_kmeans_k2.joblib").exists()
    assert (artifacts_dir / "user_kmeans_k3.joblib").exists()

    # 4. Check generated plots
    expected_plots = [
        "feature_distributions.png",
        "correlation_matrix.png",
        "missingness_overview.png",
        "temporal_trends.png",
        "user_heterogeneity.png",
        "daily_elbow_and_silhouette.png",
        "daily_pca_clusters_k2.png",
        "daily_pca_clusters_k3.png",
        "user_elbow_and_silhouette.png",
        "user_pca_clusters_k2.png",
        "user_pca_clusters_k3.png",
    ]
    for plot_name in expected_plots:
        assert (results_dir / plot_name).exists(), f"Plot {plot_name} was not generated!"

    # 5. Verify zero target leakage in clustering metadata
    with open(metadata_file, encoding="utf-8") as f:
        saved_meta = json.load(f)

    daily_features = saved_meta["experiment_a_daily"]["features"]
    user_features = saved_meta["experiment_b_user_level"]["features"]

    assert "productivity_score" not in daily_features
    assert "productivity_score" not in user_features
    assert "user_id" not in daily_features
    assert "record_date" not in daily_features
