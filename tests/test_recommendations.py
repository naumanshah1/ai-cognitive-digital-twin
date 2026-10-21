"""Unit tests for the evidence-based recommendation engine (Milestone 7).

Verifies rule triggering, duplicate suppression, priority score calculation,
insufficient data handling, non-clinical phrasing safeguards, and serialization.
"""

import pandas as pd
import numpy as np
import pytest

from app.ml.drift import (
    DistributionSummary,
    DriftDirection,
    DriftStatus,
    FeatureDriftResult,
    UserDriftReport,
    compute_distribution_summary,
)
from app.ml.recommendations import (
    ConfidenceLevel,
    RecommendationCategory,
    RecommendationItem,
    RecommendationReport,
    compute_priority_score,
    generate_recommendations,
)


@pytest.fixture
def base_user_telemetry() -> pd.DataFrame:
    """Fixture providing 14 days of realistic synthetic telemetry for a single user."""
    dates = pd.date_range("2026-03-01", periods=14, freq="D").strftime("%Y-%m-%d")
    data = {
        "user_id": ["synthetic_0001"] * 14,
        "record_date": dates,
        "sleep_hours": [7.5] * 14,
        "sleep_quality": [4] * 14,
        "focus_duration_hours": [4.0] * 14,
        "screen_time_hours": [6.5] * 14,
        "tasks_planned": [5] * 14,
        "tasks_completed": [4] * 14,
        "task_difficulty_avg": [3.0] * 14,
        "work_session_duration_hours": [5.5] * 14,
        "inactivity_duration_hours": [1.5] * 14,
        "interruption_count": [3] * 14,
        "mood_score": [3] * 14,
        "perceived_stress": [2] * 14,
        "productivity_score": [72.0] * 14,
    }
    return pd.DataFrame(data)


def test_priority_score_calculation_bounds_and_weights():
    """Verify compute_priority_score clamps to [0, 1] and respects custom weights."""
    score_mid = compute_priority_score(0.5, 0.5, 0.5, 0.5)
    assert 0.0 <= score_mid <= 1.0
    assert abs(score_mid - 0.5) < 1e-4

    # Extreme bounds
    assert abs(compute_priority_score(2.0, 3.0, 1.5, 2.0) - 1.0) < 1e-5
    assert compute_priority_score(-1.0, -0.5, 0.0, 0.0) == 0.0

    # Custom weights
    custom_score = compute_priority_score(
        magnitude_norm=1.0,
        evidence_quality=0.0,
        data_completeness=0.0,
        persistence=0.0,
        weights=(1.0, 0.0, 0.0, 0.0),
    )
    assert abs(custom_score - 1.0) < 1e-4


def test_insufficient_data_generates_cautious_logging_recommendation(base_user_telemetry):
    """Verify that fewer than min_monitoring_days triggers REC-DAT-001."""
    # Pass only 2 days of telemetry
    sparse_df = base_user_telemetry.iloc[:2].copy()
    report = generate_recommendations(
        user_telemetry_df=sparse_df,
        evaluation_date="2026-03-02",
        min_monitoring_days=4,
        monitoring_window_days=7,
    )

    assert report.insufficient_data is True
    assert len(report.recommendations) == 1
    rec = report.recommendations[0]
    assert rec.recommendation_id == "REC-DAT-001"
    assert rec.category == RecommendationCategory.DATA_COLLECTION
    assert "telemetry" in rec.explanation.lower() or "observation" in rec.explanation.lower()


def test_no_recommendations_on_optimal_unperturbed_telemetry(base_user_telemetry):
    """When telemetry is balanced and unperturbed, no urgent recommendations fire."""
    report = generate_recommendations(
        user_telemetry_df=base_user_telemetry,
        evaluation_date="2026-03-14",
    )
    # Balanced baseline: focus=4h, interruptions=3, sleep=7.5h, stress=2, completion=80%
    assert report.insufficient_data is False
    assert len(report.recommendations) == 0
    assert report.audit_summary["observations_count"] == 7


def test_interruption_rule_trigger_and_evidence(base_user_telemetry):
    """High interruptions in recent window trigger REC-INT-001 with verified evidence."""
    df = base_user_telemetry.copy()
    # Spike interruptions in the last 7 days to 9 per day
    df.loc[7:13, "interruption_count"] = 9

    report = generate_recommendations(
        user_telemetry_df=df,
        evaluation_date="2026-03-14",
    )

    int_recs = [r for r in report.recommendations if r.recommendation_id == "REC-INT-001"]
    assert len(int_recs) == 1
    rec = int_recs[0]
    assert rec.category == RecommendationCategory.INTERRUPTION_MANAGEMENT
    assert rec.observed_evidence["mean_interruption_count"] == 9.0
    assert "context switch" in rec.rationale.lower()


def test_focus_drop_drift_integration_trigger(base_user_telemetry):
    """Providing a UserDriftReport with focus reduction triggers REC-FOC-001."""
    df = base_user_telemetry.copy()
    df.loc[7:13, "focus_duration_hours"] = 1.8

    mock_drift_report = UserDriftReport(
        user_id="synthetic_0001",
        evaluation_date="2026-03-14",
        reference_start_date="2026-03-01",
        reference_end_date="2026-03-07",
        comparison_start_date="2026-03-08",
        comparison_end_date="2026-03-14",
        feature_results={
            "focus_duration_hours": FeatureDriftResult(
                feature_name="focus_duration_hours",
                status=DriftStatus.STRONG_DRIFT,
                direction=DriftDirection.DECREASE,
                reference_summary=compute_distribution_summary(np.array([4.0] * 7)),
                comparison_summary=compute_distribution_summary(np.array([1.8] * 7)),
                mean_difference=-2.2,
                median_difference=-2.2,
                cohens_d=-1.65,
                wasserstein_distance=2.2,
                psi=0.45,
                p_value_raw=0.001,
                p_value_adjusted=0.008,
                is_statistically_significant=True,
                is_practically_meaningful=True,
                rationale="Significant downward drift detected in focus duration.",
            )
        },
        overall_status=DriftStatus.STRONG_DRIFT,
        drifted_features_count=1,
        strong_drift_features=["focus_duration_hours"],
        tentative_drift_features=[],
        insufficient_data_features=[],
        summary_narrative="Strong downward drift in focus duration.",
    )

    report = generate_recommendations(
        user_telemetry_df=df,
        evaluation_date="2026-03-14",
        user_drift_report=mock_drift_report,
    )

    foc_recs = [r for r in report.recommendations if r.recommendation_id == "REC-FOC-001"]
    assert len(foc_recs) == 1
    rec = foc_recs[0]
    assert rec.confidence == ConfidenceLevel.HIGH
    assert rec.observed_evidence["drift_detected"] is True
    assert rec.observed_evidence["cohens_d"] == -1.65


def test_stress_spike_trigger_and_non_clinical_guardrails(base_user_telemetry):
    """Stress spike triggers REC-STR-001 and strictly avoids clinical diagnostic terms."""
    df = base_user_telemetry.copy()
    df.loc[7:13, "perceived_stress"] = 5

    report = generate_recommendations(
        user_telemetry_df=df,
        evaluation_date="2026-03-14",
    )

    str_recs = [r for r in report.recommendations if r.recommendation_id == "REC-STR-001"]
    assert len(str_recs) == 1
    rec = str_recs[0]
    assert rec.category == RecommendationCategory.STRESS_PACING

    full_text = (
        rec.explanation + " " + rec.proposed_action + " " + rec.rationale + " " + rec.limitations + " " + rec.disclaimer
    ).lower()

    # Guardrails: verify no clinical claims or diagnoses
    assert "burnout" not in full_text
    assert "depression" not in full_text
    assert "anxiety" not in full_text
    assert "guarantee" not in full_text
    assert "clinical" in full_text  # Should state "does not constitute a clinical ... recommendation"


def test_duplicate_suppression_and_priority_sorting(base_user_telemetry):
    """When multiple rules trigger, ensure category deduplication and descending priority sorting."""
    df = base_user_telemetry.copy()
    # Trigger interruptions (9), focus drop (1.5h), low sleep (5.0h)
    df.loc[7:13, "interruption_count"] = 9
    df.loc[7:13, "focus_duration_hours"] = 1.5
    df.loc[7:13, "sleep_hours"] = 5.0

    report = generate_recommendations(
        user_telemetry_df=df,
        evaluation_date="2026-03-14",
    )

    assert len(report.recommendations) >= 2
    # Verify no duplicate categories
    categories = [r.category for r in report.recommendations]
    assert len(categories) == len(set(categories))

    # Verify descending priority sort
    scores = [r.priority_score for r in report.recommendations]
    assert scores == sorted(scores, reverse=True)


def test_missing_and_nullable_feature_handling(base_user_telemetry):
    """Verify engine handles NaNs in optional fields (e.g. perceived_stress) gracefully."""
    df = base_user_telemetry.copy()
    df["perceived_stress"] = np.nan
    df["sleep_quality"] = np.nan

    report = generate_recommendations(
        user_telemetry_df=df,
        evaluation_date="2026-03-14",
    )
    assert report.insufficient_data is False


def test_recommendation_report_serialization(base_user_telemetry):
    """Verify clean dictionary serialization via to_dict()."""
    df = base_user_telemetry.copy()
    df.loc[7:13, "interruption_count"] = 8

    report = generate_recommendations(
        user_telemetry_df=df,
        evaluation_date="2026-03-14",
    )
    rep_dict = report.to_dict()

    assert rep_dict["user_id"] == "synthetic_0001"
    assert rep_dict["evaluation_date"] == "2026-03-14"
    assert isinstance(rep_dict["recommendations"], list)
    assert len(rep_dict["recommendations"]) >= 1
    assert "priority_score" in rep_dict["recommendations"][0]
