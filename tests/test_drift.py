"""Unit tests for Milestone 6 Behavioural Drift Detection pipeline and statistical estimators."""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from app.ml.drift import (
    DEFAULT_BEHAVIORAL_DRIFT_FEATURES,
    DistributionSummary,
    DriftDetectionConfig,
    DriftDirection,
    DriftStatus,
    FeatureDriftResult,
    UserDriftReport,
    benjamini_hochberg,
    compute_cohens_d,
    compute_distribution_summary,
    compute_population_stability_index,
    detect_cohort_drift,
    detect_feature_drift,
    detect_user_drift,
    generate_recovery_scenario_data,
)
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def drift_config() -> DriftDetectionConfig:
    return DriftDetectionConfig(
        reference_window_days=14,
        comparison_window_days=7,
        min_reference_samples=7,
        min_comparison_samples=4,
        significance_alpha=0.05,
        moderate_effect_threshold=0.50,
        strong_effect_threshold=0.80,
    )


# --- 1. Statistical Estimator Tests ---

def test_benjamini_hochberg_correction():
    """Verify Benjamini-Hochberg step-up procedure preserves bounds and ranks."""
    # Test empty and single-element inputs
    assert benjamini_hochberg([]) == []
    assert benjamini_hochberg([0.03]) == [0.03]

    # Test typical sequence of p-values: [0.01, 0.04, 0.03, 0.20]
    p_vals = [0.01, 0.04, 0.03, 0.20]
    adj = benjamini_hochberg(p_vals)
    assert len(adj) == 4
    # All adjusted p-values must be >= raw and <= 1.0
    for raw, q in zip(p_vals, adj):
        assert q >= raw
        assert 0.0 <= q <= 1.0

    # Test exact mathematical calculation:
    # m = 3, sorted: p1=0.01, p2=0.02, p3=0.05
    # q1 = 0.01 * 3 / 1 = 0.03
    # q2 = 0.02 * 3 / 2 = 0.03
    # q3 = 0.05 * 3 / 3 = 0.05
    exact_adj = benjamini_hochberg([0.01, 0.02, 0.05])
    assert np.allclose(exact_adj, [0.03, 0.03, 0.05], atol=1e-5)


def test_compute_distribution_summary():
    """Verify summary metrics computation and NaN handling."""
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0, np.nan])
    summary = compute_distribution_summary(arr)
    assert summary.count == 5
    assert summary.mean == 3.0
    assert summary.median == 3.0
    assert summary.min == 1.0
    assert summary.max == 5.0
    assert summary.iqr == 2.0  # Q75(4) - Q25(2)

    empty_summary = compute_distribution_summary(np.array([np.nan, np.nan]))
    assert empty_summary.count == 0
    assert empty_summary.mean == 0.0


def test_cohens_d_calculation():
    """Verify Cohen's d standardized effect size and edge cases."""
    # Identical samples -> d == 0.0
    s1 = np.array([4.0, 4.5, 5.0, 4.2, 4.8])
    assert compute_cohens_d(s1, s1) == 0.0

    # Known positive shift: reference mean=5, comp mean=7, std=1.0 -> d approx +2.0
    ref = np.array([4.0, 5.0, 6.0, 5.0, 5.0])  # mean=5.0, s=0.707
    cmp = np.array([6.0, 7.0, 8.0, 7.0, 7.0])  # mean=7.0, s=0.707
    d = compute_cohens_d(ref, cmp)
    assert d > 1.5
    assert d > 0

    # Negative shift
    d_neg = compute_cohens_d(cmp, ref)
    assert d_neg < -1.5

    # Degenerate zero-variance case
    const_ref = np.array([5.0, 5.0, 5.0])
    const_cmp = np.array([5.0, 5.0, 5.0])
    assert compute_cohens_d(const_ref, const_cmp) == 0.0


def test_population_stability_index():
    """Verify PSI calculation for identical and shifted samples."""
    np.random.seed(42)
    s1 = np.random.normal(5.0, 1.0, 100)
    s2 = np.random.normal(5.0, 1.0, 50)
    # Identical distribution should produce low PSI (< 0.10)
    psi_stable = compute_population_stability_index(s1, s2)
    assert psi_stable < 0.15

    # Shifted distribution should produce high PSI (> 0.25)
    s_shifted = np.random.normal(8.0, 1.0, 50)
    psi_shifted = compute_population_stability_index(s1, s_shifted)
    assert psi_shifted > 0.25


# --- 2. Feature Drift Detection Decision Logic ---

def test_no_drift_on_identical_distributions(drift_config):
    """Verify that identical distributions yield NO_DRIFT."""
    ref = np.array([5.0, 5.2, 4.8, 5.1, 4.9, 5.0, 5.3, 4.7, 5.0, 5.1])
    cmp = np.array([5.0, 5.2, 4.8, 5.1, 4.9, 5.0, 5.3])
    res = detect_feature_drift(ref, cmp, "focus_duration_hours", drift_config)
    assert res.status == DriftStatus.NO_DRIFT
    assert res.is_statistically_significant is False
    assert abs(res.cohens_d) < drift_config.moderate_effect_threshold


def test_known_distribution_shift_detection(drift_config):
    """Verify that a large, significant shift is classified as STRONG_DRIFT."""
    ref = np.array([6.0, 6.2, 5.8, 6.1, 5.9, 6.0, 6.3, 5.7, 6.0, 6.1, 5.9, 6.2, 6.0, 5.8])
    cmp = np.array([3.0, 3.2, 2.8, 3.1, 2.9, 3.0, 3.3])  # -3.0h shift
    res = detect_feature_drift(ref, cmp, "focus_duration_hours", drift_config)
    assert res.status == DriftStatus.STRONG_DRIFT
    assert res.direction == DriftDirection.DECREASE
    assert res.cohens_d < -drift_config.strong_effect_threshold
    assert res.p_value_raw < 0.01


def test_insufficient_data_handling(drift_config):
    """Verify that samples with fewer than minimum required observations return INSUFFICIENT_DATA."""
    ref = np.array([5.0, 5.1])  # Only 2 samples (min is 7)
    cmp = np.array([5.0, 5.2, 4.8, 5.1])
    res = detect_feature_drift(ref, cmp, "sleep_quality", drift_config)
    assert res.status == DriftStatus.INSUFFICIENT_DATA
    assert res.reference_summary is not None
    assert "Insufficient" in res.rationale


# --- 3. Windowing, Chronological Ordering, and Zero-Leakage Tests ---

def test_window_construction_and_chronological_ordering(drift_config):
    """Verify reference window strictly precedes comparison window with no date overlap."""
    dates = pd.date_range("2026-01-01", periods=30, freq="D").strftime("%Y-%m-%d").tolist()
    records = []
    for d in dates:
        records.append({
            "user_id": "u1",
            "record_date": d,
            "focus_duration_hours": 5.0,
            "sleep_hours": 7.5,
        })
    df = pd.DataFrame(records)

    eval_date = "2026-01-25"
    report = detect_user_drift(df, evaluation_date=eval_date, config=drift_config)

    assert report.evaluation_date == eval_date
    assert report.comparison_end_date == eval_date
    assert report.comparison_start_date == "2026-01-19"  # 7-day comparison [Jan 19..Jan 25]
    assert report.reference_end_date == "2026-01-18"    # strictly 1 day before cmp
    assert report.reference_start_date == "2026-01-05"  # 14-day reference [Jan 5..Jan 18]

    # Verify reference window strictly precedes comparison window
    assert pd.to_datetime(report.reference_end_date) < pd.to_datetime(report.comparison_start_date)


def test_no_future_data_leakage(drift_config):
    """Verify that records occurring after evaluation_date t never influence drift evaluation."""
    dates = pd.date_range("2026-01-01", periods=30, freq="D").strftime("%Y-%m-%d").tolist()
    records = []
    for d in dates:
        # Before or on evaluation date: stable focus (5.0h)
        # After evaluation date (Day 26+): extreme anomaly (0.0h)
        focus = 5.0 if d <= "2026-01-25" else 0.0
        records.append({
            "user_id": "u1",
            "record_date": d,
            "focus_duration_hours": focus,
            "sleep_hours": 7.5,
        })
    df = pd.DataFrame(records)

    # Evaluate at Jan 25
    report = detect_user_drift(df, evaluation_date="2026-01-25", config=drift_config)
    f_res = report.feature_results["focus_duration_hours"]

    # If future data did not leak, status must be NO_DRIFT because data up to Jan 25 was completely stable
    assert f_res.status == DriftStatus.NO_DRIFT
    assert f_res.mean_difference == 0.0
    assert f_res.comparison_summary.mean == 5.0


def test_per_user_isolation(drift_config):
    """Verify that drift detection for user A is completely isolated from user B."""
    records = []
    dates = pd.date_range("2026-01-01", periods=25, freq="D").strftime("%Y-%m-%d").tolist()

    for d in dates:
        # User 1 is completely stable (5.0h)
        records.append({"user_id": "u1", "record_date": d, "focus_duration_hours": 5.0})
        # User 2 has an extreme drop in the final 7 days (1.0h)
        u2_focus = 1.0 if d >= "2026-01-19" else 5.0
        records.append({"user_id": "u2", "record_date": d, "focus_duration_hours": u2_focus})

    df = pd.DataFrame(records)
    cohort = detect_cohort_drift(df, evaluation_date="2026-01-25", config=drift_config)

    # u1 must show NO_DRIFT
    assert cohort["u1"].overall_status == DriftStatus.NO_DRIFT
    assert cohort["u1"].feature_results["focus_duration_hours"].status == DriftStatus.NO_DRIFT

    # u2 must show STRONG_DRIFT
    assert cohort["u2"].overall_status == DriftStatus.STRONG_DRIFT
    assert cohort["u2"].feature_results["focus_duration_hours"].status == DriftStatus.STRONG_DRIFT
    assert cohort["u2"].feature_results["focus_duration_hours"].direction == DriftDirection.DECREASE


# --- 4. Controlled Scenario Integration Tests ---

def test_controlled_focus_drop_detection(drift_config):
    """Verify that synthetic focus_drop scenario is detected with high sensitivity."""
    df = generate_synthetic_data(n_users=5, n_days=80, seed=42, scenario="focus_drop")
    dates = sorted(df["record_date"].unique())
    shift_idx = int(0.70 * 80)
    # Comparison window immediately after shift onset: dates[shift_idx .. shift_idx + 6]
    eval_date = dates[shift_idx + drift_config.comparison_window_days - 1]

    cohort = detect_cohort_drift(df, evaluation_date=eval_date, config=drift_config)
    detected_count = sum(
        1 for r in cohort.values()
        if r.feature_results.get("focus_duration_hours")
        and r.feature_results["focus_duration_hours"].status in [DriftStatus.STRONG_DRIFT, DriftStatus.TENTATIVE_DRIFT]
        and r.feature_results["focus_duration_hours"].direction == DriftDirection.DECREASE
    )
    # At least 4 of 5 users should have detected shift
    assert detected_count >= 4


def test_controlled_stress_spike_detection(drift_config):
    """Verify that synthetic stress_spike scenario is detected on perceived_stress."""
    df = generate_synthetic_data(n_users=5, n_days=80, seed=42, scenario="stress_spike")
    dates = sorted(df["record_date"].unique())
    shift_idx = int(0.70 * 80)
    eval_date = dates[shift_idx + drift_config.comparison_window_days - 1]

    cohort = detect_cohort_drift(df, evaluation_date=eval_date, config=drift_config)
    detected_count = sum(
        1 for r in cohort.values()
        if r.feature_results.get("perceived_stress")
        and r.feature_results["perceived_stress"].status in [DriftStatus.STRONG_DRIFT, DriftStatus.TENTATIVE_DRIFT]
        and r.feature_results["perceived_stress"].direction == DriftDirection.INCREASE
    )
    # Stress spike should be detected across majority of users
    assert detected_count >= 3


def test_recovery_scenario_detection_and_normalization(drift_config):
    """Verify recovery scenario flags perturbation during Phase 2 and returns to baseline in Phase 3."""
    df_rec = generate_recovery_scenario_data(n_users=3, n_days=90, seed=42)
    dates = sorted(df_rec["record_date"].unique())
    shift_start_idx = int(0.60 * 90)
    shift_end_idx = int(0.75 * 90)

    # 1. At end of Phase 2 perturbation comparison window: should detect drift with decrease
    eval_perturbed = dates[shift_start_idx + drift_config.comparison_window_days - 1]
    cohort_perturbed = detect_cohort_drift(df_rec, evaluation_date=eval_perturbed, config=drift_config)
    perturbed_decreases = sum(
        1 for r in cohort_perturbed.values()
        if r.feature_results.get("focus_duration_hours")
        and r.feature_results["focus_duration_hours"].status in [DriftStatus.STRONG_DRIFT, DriftStatus.TENTATIVE_DRIFT]
        and r.feature_results["focus_duration_hours"].direction == DriftDirection.DECREASE
    )
    assert perturbed_decreases >= 2

    # 2. In Phase 3 recovery (final date): focus has recovered, so zero users show persistent strong decrease
    cohort_recovered = detect_cohort_drift(df_rec, evaluation_date=dates[-1], config=drift_config)
    persistent_decreases = sum(
        1 for r in cohort_recovered.values()
        if r.feature_results.get("focus_duration_hours")
        and r.feature_results["focus_duration_hours"].status == DriftStatus.STRONG_DRIFT
        and r.feature_results["focus_duration_hours"].direction == DriftDirection.DECREASE
    )
    assert persistent_decreases == 0


def test_user_drift_summary_serialization(drift_config):
    """Verify UserDriftReport serializes cleanly to dict."""
    df = generate_synthetic_data(n_users=1, n_days=30, seed=42, scenario="baseline")
    dates = sorted(df["record_date"].unique())
    rep = detect_user_drift(df, evaluation_date=dates[-1], config=drift_config)
    d = rep.to_dict()
    assert d["user_id"] == "synthetic_0001"
    assert "reference_window" in d
    assert "comparison_window" in d
    assert isinstance(d["feature_results"], dict)
    assert d["overall_status"] in ["no_drift", "tentative_drift", "strong_drift", "insufficient_data"]
