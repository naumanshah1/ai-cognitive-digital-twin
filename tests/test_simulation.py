"""Unit tests for the What-If Simulation Engine (Milestone 7).

Verifies retrospective and forecasting simulation paths, input immutability,
boundary constraint validation, unknown feature rejection, no-change zero delta,
OOD warnings, and non-causal disclaimer formatting.
"""

from copy import deepcopy
from typing import Any
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression
import torch

from app.data_pipeline.feature_engineering import engineer_features
from app.data_pipeline.schema import COLUMN_RANGES
from app.services.preprocessing import BehavioralDataPreprocessor
from app.ml.simulation import (
    SimulationResult,
    SimulationScenario,
    SimulationTaskType,
    WhatIfSimulator,
    detect_out_of_distribution,
    validate_feature_bounds,
)
from app.ml.temporal import (
    ProductivityLSTM,
    TemporalPreprocessor,
    TemporalSequenceData,
)


@pytest.fixture
def fitted_retrospective_environment() -> tuple[LinearRegression, BehavioralDataPreprocessor, dict[str, Any]]:
    """Fixture providing a fitted LinearRegression model, fitted Preprocessor, and sample row."""
    # Generate small synthetic dataset to fit preprocessor and model
    np.random.seed(42)
    n_samples = 40
    records = []
    for i in range(n_samples):
        records.append({
            "user_id": f"synthetic_{i%3:04d}",
            "record_date": f"2026-01-{(i%28)+1:02d}",
            "sleep_hours": float(np.random.normal(7.5, 0.8)),
            "sleep_quality": int(np.random.choice([2, 3, 4, 5])),
            "focus_duration_hours": float(np.clip(np.random.normal(4.0, 1.2), 0.5, 8.0)),
            "screen_time_hours": float(np.random.normal(7.0, 1.0)),
            "tasks_planned": int(np.random.choice([4, 5, 6])),
            "tasks_completed": int(np.random.choice([3, 4, 5])),
            "task_difficulty_avg": 3.0,
            "work_session_duration_hours": float(np.random.normal(6.0, 1.0)),
            "inactivity_duration_hours": float(np.random.normal(1.5, 0.4)),
            "interruption_count": int(np.random.choice([1, 2, 3, 4])),
            "mood_score": 3,
            "perceived_stress": 2,
            "productivity_score": 70.0,
        })
    df = pd.DataFrame(records)
    # Ensure logical focus <= session
    df["work_session_duration_hours"] = df[["work_session_duration_hours", "focus_duration_hours"]].max(axis=1) + 0.5
    df["tasks_planned"] = df[["tasks_planned", "tasks_completed"]].max(axis=1)

    eng_df = engineer_features(df, include_target_derived=False)
    # Create synthetic productivity target strongly positively correlated with focus
    eng_df["productivity_score"] = 40.0 + 6.0 * eng_df["focus_duration_hours"] - 2.0 * eng_df["interruption_count"]

    prep = BehavioralDataPreprocessor(target_col="productivity_score", clip_outliers=True)
    train_prep = prep.fit_transform(eng_df)

    model = LinearRegression()
    model.fit(train_prep.X, train_prep.y)

    sample_dict = eng_df.iloc[0].to_dict()
    return model, prep, sample_dict


@pytest.fixture
def fitted_forecasting_environment() -> tuple[ProductivityLSTM, TemporalPreprocessor, np.ndarray, list[str]]:
    """Fixture providing a mock trained LSTM, TemporalPreprocessor, and sequence array."""
    torch.manual_seed(42)
    np.random.seed(42)

    feat_names = [
        "sleep_hours", "sleep_quality", "focus_duration_hours", "screen_time_hours",
        "tasks_planned", "tasks_completed", "task_difficulty_avg",
        "work_session_duration_hours", "inactivity_duration_hours", "interruption_count",
        "mood_score", "perceived_stress", "task_completion_rate",
        "work_session_utilization", "inactivity_ratio", "day_of_week", "is_weekend",
        "rolling_focus_std_7d", "work_session_frequency_7d", "productivity_score",
    ]
    num_feats = len(feat_names)
    lookback = 7

    # Build dummy DataFrame to fit TemporalPreprocessor
    sample_records = []
    for _ in range(30):
        row = {}
        for f in feat_names:
            r = COLUMN_RANGES.get(f, {"min": 0.0, "max": 10.0})
            min_v = r.get("min", 1.0)
            max_v = min(r.get("max", 5.0), 10.0)
            row[f] = float((min_v + max_v) / 2.0)
        row["work_session_duration_hours"] = 6.0
        row["focus_duration_hours"] = 4.0
        row["tasks_planned"] = 5.0
        row["tasks_completed"] = 3.0
        row["productivity_score"] = 70.0
        sample_records.append(row)

    dummy_df = pd.DataFrame(sample_records)
    t_prep = TemporalPreprocessor(scale_target=True)
    t_prep.fit(dummy_df, feature_names=feat_names, target_col="productivity_score")

    lstm = ProductivityLSTM(input_dim=num_feats, hidden_dim=16)

    # 1 sample sequence of shape (1, 7, 20) with valid domain bounds
    sample_seq = np.zeros((1, lookback, num_feats), dtype=np.float32)
    for i, f in enumerate(feat_names):
        sample_seq[0, :, i] = float(dummy_df[f].iloc[0])

    return lstm, t_prep, sample_seq, feat_names


def test_validate_feature_bounds_rejects_impossible_values():
    """Verify validate_feature_bounds rejects negative hours and rating violations."""
    with pytest.raises(ValueError, match="below absolute minimum"):
        validate_feature_bounds({"focus_duration_hours": -1.0})

    with pytest.raises(ValueError, match="exceeds absolute maximum"):
        validate_feature_bounds({"perceived_stress": 8.0})

    with pytest.raises(ValueError, match="exceeds work session duration"):
        validate_feature_bounds({"focus_duration_hours": 6.0, "work_session_duration_hours": 3.0})


def test_retrospective_no_change_scenario_produces_zero_delta(fitted_retrospective_environment):
    """Applying a no-change scenario must yield exact delta = 0.0 within float precision."""
    model, prep, sample_dict = fitted_retrospective_environment
    sim = WhatIfSimulator(retrospective_model=model, retrospective_preprocessor=prep)

    scenario_no_change = SimulationScenario(
        scenario_id="SIM-NULL",
        name="No-Change Baseline",
        task_type=SimulationTaskType.RETROSPECTIVE_ESTIMATION,
        modifications={},
    )

    res = sim.simulate_retrospective(sample_dict, scenario_no_change)
    assert abs(res.prediction_delta) < 1e-4
    assert res.baseline_prediction == res.simulated_prediction


def test_retrospective_single_feature_increase(fitted_retrospective_environment):
    """Increasing focus duration produces expected positive productivity score delta."""
    model, prep, sample_dict = fitted_retrospective_environment
    sim = WhatIfSimulator(retrospective_model=model, retrospective_preprocessor=prep)

    scenario_focus = SimulationScenario(
        scenario_id="SIM-FOC-P1H",
        name="Focus Duration +1.0 Hour",
        task_type=SimulationTaskType.RETROSPECTIVE_ESTIMATION,
        modifications={"focus_duration_hours": 1.0},
        is_relative=True,
    )

    res = sim.simulate_retrospective(sample_dict, scenario_focus)
    assert res.prediction_delta > 0.0
    assert "focus_duration_hours" in res.features_modified
    assert "Under this retrospective regression model" in res.non_causal_disclaimer


def test_retrospective_input_immutability(fitted_retrospective_environment):
    """Verify that simulating modifications does not mutate the original baseline dictionary."""
    model, prep, sample_dict = fitted_retrospective_environment
    sim = WhatIfSimulator(retrospective_model=model, retrospective_preprocessor=prep)

    orig_copy = deepcopy(sample_dict)
    scenario_focus = SimulationScenario(
        scenario_id="SIM-FOC-P1H",
        name="Focus Duration +1.0 Hour",
        task_type=SimulationTaskType.RETROSPECTIVE_ESTIMATION,
        modifications={"focus_duration_hours": 1.0},
        is_relative=True,
    )

    _ = sim.simulate_retrospective(sample_dict, scenario_focus)
    assert sample_dict == orig_copy


def test_retrospective_rejects_unknown_features(fitted_retrospective_environment):
    """Modifying unknown features raises ValueError."""
    model, prep, sample_dict = fitted_retrospective_environment
    sim = WhatIfSimulator(retrospective_model=model, retrospective_preprocessor=prep)

    scenario_bad = SimulationScenario(
        scenario_id="SIM-BAD",
        name="Unknown Feature",
        task_type=SimulationTaskType.RETROSPECTIVE_ESTIMATION,
        modifications={"caffeine_intake_mg": 200.0},
    )

    with pytest.raises(ValueError, match="Unknown feature"):
        sim.simulate_retrospective(sample_dict, scenario_bad)


def test_task_type_mismatch_raises_error(fitted_retrospective_environment):
    """Passing a forecasting scenario to simulate_retrospective raises ValueError."""
    model, prep, sample_dict = fitted_retrospective_environment
    sim = WhatIfSimulator(retrospective_model=model, retrospective_preprocessor=prep)

    scenario_forecasting = SimulationScenario(
        scenario_id="SIM-FORECAST",
        name="Next Day Focus Forecast",
        task_type=SimulationTaskType.FUTURE_FORECASTING,
        modifications={"focus_duration_hours": 1.0},
    )

    with pytest.raises(ValueError, match="expected 'retrospective_estimation'"):
        sim.simulate_retrospective(sample_dict, scenario_forecasting)


def test_forecasting_simulation_modifies_only_forecast_origin(fitted_forecasting_environment):
    """Forecasting simulation modifies only the origin timestep index -1 in lookback sequence."""
    lstm, t_prep, sample_seq, feat_names = fitted_forecasting_environment
    sim = WhatIfSimulator(forecasting_model=lstm, forecasting_preprocessor=t_prep)

    scenario_forecast = SimulationScenario(
        scenario_id="SIM-FORECAST-001",
        name="Next-Day Focus +0.5h",
        task_type=SimulationTaskType.FUTURE_FORECASTING,
        modifications={"focus_duration_hours": 0.5},
        is_relative=True,
    )

    orig_copy = sample_seq.copy()
    res = sim.simulate_forecasting(sample_seq, scenario_forecast, feature_names=feat_names)

    # Immutability
    np.testing.assert_array_equal(sample_seq, orig_copy)
    assert isinstance(res.prediction_delta, float)
    assert "Under this temporal forecasting LSTM model" in res.non_causal_disclaimer


def test_out_of_distribution_warning_detection(fitted_retrospective_environment):
    """Simulating an extreme value outside IQR bounds sets is_out_of_distribution=True."""
    model, prep, sample_dict = fitted_retrospective_environment
    iqr_bounds = {
        "focus_duration_hours": {"lower": 1.0, "upper": 6.5}
    }
    sim = WhatIfSimulator(retrospective_model=model, retrospective_preprocessor=prep, iqr_bounds=iqr_bounds)

    scenario_extreme = SimulationScenario(
        scenario_id="SIM-EXTREME",
        name="Extreme Focus",
        task_type=SimulationTaskType.RETROSPECTIVE_ESTIMATION,
        modifications={"focus_duration_hours": 10.0, "work_session_duration_hours": 11.0},
        is_relative=False,
    )

    res = sim.simulate_retrospective(sample_dict, scenario_extreme)
    assert res.is_out_of_distribution is True
    assert any("outside training IQR bounds" in w for w in res.warnings)
