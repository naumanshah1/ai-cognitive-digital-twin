"""Unit tests for agent registered tools wrapping ML and behavioural pipelines."""

import pytest

from app.agent.tools import (
    TOOL_REGISTRY,
    TOOL_SCHEMAS,
    detect_behavioral_drift,
    generate_recommendations,
    get_behavioral_summary,
    predict_productivity,
    run_what_if_simulation,
)


def test_tool_registry_and_schemas_alignment():
    """Verify registry has all 5 required tools and schemas match."""
    expected_tools = {
        "get_behavioral_summary",
        "detect_behavioral_drift",
        "generate_recommendations",
        "run_what_if_simulation",
        "predict_productivity",
    }
    assert set(TOOL_REGISTRY.keys()) == expected_tools

    schema_names = {s["name"] for s in TOOL_SCHEMAS}
    assert schema_names == expected_tools


def test_get_behavioral_summary():
    """Verify get_behavioral_summary returns valid statistical telemetry."""
    res = get_behavioral_summary(user_id="synthetic_0001", days=14)
    assert res["user_id"] == "synthetic_0001"
    assert res["records_analyzed"] == 14
    assert "averages" in res
    assert "focus_duration_hours" in res["averages"]
    assert "sleep_hours" in res["averages"]
    assert "actual_productivity_score" in res["averages"]
    assert res["data_completeness"] == 1.0


def test_get_behavioral_summary_unknown_user():
    """Verify get_behavioral_summary handles unknown users gracefully."""
    res = get_behavioral_summary(user_id="synthetic_9999", days=14)
    assert res["record_count"] == 0
    assert "error" in res


def test_detect_behavioral_drift_tool():
    """Verify detect_behavioral_drift executes multi-feature drift testing."""
    res = detect_behavioral_drift(user_id="synthetic_0001", ref_window=14, cmp_window=7)
    assert res["user_id"] == "synthetic_0001"
    assert "overall_status" in res
    assert "total_features_evaluated" in res
    assert res["total_features_evaluated"] >= 8
    assert "safeguard_disclaimer" in res


def test_generate_recommendations_tool():
    """Verify generate_recommendations returns prioritized operational action items."""
    res = generate_recommendations(user_id="synthetic_0001")
    assert res["user_id"] == "synthetic_0001"
    assert "total_recommendations" in res
    assert "recommendations" in res
    assert "safeguard_notice" in res
    if res["total_recommendations"] > 0:
        first_rec = res["recommendations"][0]
        assert "priority_score" in first_rec
        assert "evidence" in first_rec
        assert "proposed_action" in first_rec


def test_run_what_if_simulation_retrospective():
    """Verify retrospective simulation computes prediction deltas without mutation."""
    res = run_what_if_simulation(
        user_id="synthetic_0001",
        modifications={"focus_duration_hours": 1.0},
        task_type="retrospective",
    )
    assert res["user_id"] == "synthetic_0001"
    assert res["task_type"] == "retrospective_estimation"
    assert "baseline_prediction" in res
    assert "simulated_prediction" in res
    assert "prediction_delta" in res
    assert res["prediction_delta"] > 0.0  # focus increase yields positive delta
    assert "non_causal_disclaimer" in res
    assert "hypothetical" in res["non_causal_disclaimer"].lower() or "model" in res["non_causal_disclaimer"].lower()


def test_run_what_if_simulation_out_of_distribution_flag():
    """Verify extreme feature change triggers out-of-distribution warning."""
    res = run_what_if_simulation(
        user_id="synthetic_0001",
        modifications={
            "focus_duration_hours": 8.0,
            "work_session_duration_hours": 8.5,
        },
        task_type="retrospective",
    )
    assert res["is_out_of_distribution"] is True
    assert len(res["warnings"]) > 0


def test_predict_productivity_retrospective_and_prospective():
    """Verify baseline productivity prediction for both modeling tasks."""
    # Retrospective estimation
    retro_res = predict_productivity(user_id="synthetic_0001", task_type="retrospective")
    assert retro_res["task_type"] == "retrospective_estimation"
    assert "predicted_productivity_score" in retro_res
    assert 0.0 <= retro_res["predicted_productivity_score"] <= 100.0

    # Prospective forecasting
    fore_res = predict_productivity(user_id="synthetic_0001", task_type="forecasting")
    assert fore_res["task_type"] == "prospective_forecasting"
    assert "predicted_next_day_score" in fore_res
    assert 0.0 <= fore_res["predicted_next_day_score"] <= 100.0
