"""Unit tests for behavioural clustering pipeline, feature selection, and model evaluation."""

import numpy as np
import pandas as pd
import pytest

from app.data_pipeline.schema import (
    IDENTIFIER_COLUMNS,
    TARGET_COLUMNS,
    TARGET_DERIVED_COLUMNS,
    TIMESTAMP_COLUMNS,
)
from app.ml.clustering import (
    BehavioralKMeansPipeline,
    evaluate_candidate_k,
    evaluate_clustering_stability,
)
from app.ml.feature_selection import (
    DAILY_CLUSTERING_FEATURES,
    USER_AGGREGATED_CLUSTERING_FEATURES,
    prepare_daily_clustering_data,
    prepare_user_level_clustering_data,
)
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    return generate_synthetic_data(n_users=5, n_days=20, seed=42)


# --- 1. Feature Selection Tests ---

def test_daily_clustering_feature_selection_excludes_forbidden_columns(sample_dataset):
    daily = prepare_daily_clustering_data(sample_dataset)

    # 1. Assert target, target-derived, IDs, and timestamps are NOT in feature matrix
    for col in TARGET_COLUMNS:
        assert col not in daily.X.columns
    for col in TARGET_DERIVED_COLUMNS:
        assert col not in daily.X.columns
    for col in IDENTIFIER_COLUMNS:
        assert col not in daily.X.columns
    for col in TIMESTAMP_COLUMNS:
        assert col not in daily.X.columns

    # 2. Assert no remaining NaNs in clustering X
    assert not daily.X.isna().any().any()
    assert list(daily.X.columns) == DAILY_CLUSTERING_FEATURES
    assert len(daily.X) == len(sample_dataset)


def test_user_level_clustering_aggregation(sample_dataset):
    user_data = prepare_user_level_clustering_data(sample_dataset)

    assert len(user_data.X) == 5
    assert list(user_data.X.columns) == USER_AGGREGATED_CLUSTERING_FEATURES
    assert "user_id" not in user_data.X.columns
    assert "user_id" in user_data.metadata.columns
    assert not user_data.X.isna().any().any()


def test_leakage_attempt_in_daily_clustering_raises_error(sample_dataset):
    bad_features = ["sleep_hours", "productivity_score"]
    with pytest.raises(ValueError) as exc:
        prepare_daily_clustering_data(sample_dataset, feature_cols=bad_features)
    assert "Target leakage violation" in str(exc.value)


# --- 2. BehavioralKMeansPipeline Tests ---

def test_kmeans_pipeline_fit_predict(sample_dataset):
    daily = prepare_daily_clustering_data(sample_dataset)
    pipeline = BehavioralKMeansPipeline(n_clusters=3, random_state=42)

    labels = pipeline.fit_predict(daily.X)

    assert len(labels) == len(daily.X)
    assert set(np.unique(labels)) == {0, 1, 2}
    assert pipeline.inertia_ > 0.0
    assert 0.0 < pipeline.silhouette_score_ <= 1.0


def test_kmeans_pipeline_unscaled_cluster_centers(sample_dataset):
    daily = prepare_daily_clustering_data(sample_dataset)
    pipeline = BehavioralKMeansPipeline(n_clusters=3, random_state=42)
    pipeline.fit(daily.X)

    centers_unscaled = pipeline.cluster_centers_unscaled_
    assert centers_unscaled is not None
    assert centers_unscaled.shape == (3, len(DAILY_CLUSTERING_FEATURES))

    # Centers should be within plausible domain ranges (e.g., sleep in [4, 11] hours)
    assert (centers_unscaled["sleep_hours"] >= 3.0).all()
    assert (centers_unscaled["sleep_hours"] <= 12.0).all()


def test_kmeans_pipeline_cluster_profiling(sample_dataset):
    daily = prepare_daily_clustering_data(sample_dataset)
    pipeline = BehavioralKMeansPipeline(n_clusters=3, random_state=42)
    pipeline.fit(daily.X)

    profiles = pipeline.compute_cluster_profiles(daily.X)

    assert len(profiles) == 3
    assert set(profiles["cluster"]) == {"Cluster_0", "Cluster_1", "Cluster_2"}
    assert sum(profiles["size"]) == len(daily.X)
    assert abs(sum(profiles["percentage"]) - 100.0) < 0.1
    assert "focus_duration_hours_mean" in profiles.columns


def test_kmeans_pipeline_save_and_reload(sample_dataset, tmp_path):
    daily = prepare_daily_clustering_data(sample_dataset)
    pipeline = BehavioralKMeansPipeline(n_clusters=3, random_state=42)
    pipeline.fit(daily.X)

    model_file = tmp_path / "test_kmeans.joblib"
    pipeline.save(model_file)
    assert model_file.exists()

    loaded = BehavioralKMeansPipeline.load(model_file)
    assert loaded.n_clusters == 3
    assert loaded.inertia_ == pipeline.inertia_

    orig_preds = pipeline.predict(daily.X)
    loaded_preds = loaded.predict(daily.X)
    np.testing.assert_array_equal(orig_preds, loaded_preds)


def test_kmeans_invalid_k_raises_error(sample_dataset):
    daily = prepare_daily_clustering_data(sample_dataset)
    with pytest.raises(ValueError):
        BehavioralKMeansPipeline(n_clusters=1)

    # Sample size < k
    tiny_X = daily.X.iloc[:2]
    with pytest.raises(ValueError):
        BehavioralKMeansPipeline(n_clusters=5).fit(tiny_X)


# --- 3. Model Selection & Stability Tests ---

def test_evaluate_candidate_k(sample_dataset, tmp_path):
    daily = prepare_daily_clustering_data(sample_dataset)
    results = evaluate_candidate_k(
        daily.X,
        k_range=range(2, 5),
        random_state=42,
        output_dir=tmp_path,
        prefix="test_daily",
    )

    evals = results["k_evaluations"]
    assert len(evals) == 3
    assert [e["k"] for e in evals] == [2, 3, 4]
    # Inertia should strictly decrease as k increases
    assert evals[0]["inertia"] > evals[1]["inertia"] > evals[2]["inertia"]

    # Verify plots were saved
    for plot_p in results["plots"]:
        assert (tmp_path / plot_p).exists()


def test_evaluate_clustering_stability(sample_dataset):
    daily = prepare_daily_clustering_data(sample_dataset)
    stability = evaluate_clustering_stability(daily.X, n_clusters=3, seeds=[42, 101, 202])

    assert "mean_adjusted_rand_index" in stability
    assert "stability_verdict" in stability
    assert 0.0 <= stability["mean_adjusted_rand_index"] <= 1.0


def test_kmeans_model_selection_k2_vs_k3(sample_dataset):
    daily = prepare_daily_clustering_data(sample_dataset)
    pipe_k2 = BehavioralKMeansPipeline(n_clusters=2, random_state=42).fit(daily.X)
    pipe_k3 = BehavioralKMeansPipeline(n_clusters=3, random_state=42).fit(daily.X)

    # In continuous behavioral data, k=2 typically yields higher silhouette than k=3
    assert pipe_k2.silhouette_score_ > 0.0
    assert pipe_k3.silhouette_score_ > 0.0
    assert pipe_k2.inertia_ > pipe_k3.inertia_  # Inertia strictly decreases with higher k


def test_user_level_clustering_stability_audit(sample_dataset):
    user_data = prepare_user_level_clustering_data(sample_dataset)
    assert len(user_data.X) == 5

    # k=2 on user level with 5 samples
    stability_k2 = evaluate_clustering_stability(user_data.X, n_clusters=2, seeds=[42, 101, 202])
    assert "mean_adjusted_rand_index" in stability_k2
    assert len(stability_k2["pairwise_aris"]) == 3
