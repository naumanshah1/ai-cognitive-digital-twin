"""What-If Simulation Engine for Behavioural Intervention Modeling.

Enables researchers and users to explore hypothetical changes to permitted
behavioural inputs and observe their effects on predictive model outputs
(retrospective productivity estimation and next-day forecasting).

Strict Methodological & Responsible AI Safeguards:
- Clear separation between Retrospective Estimation (Milestone 4, same-day)
  and Future Forecasting (Milestone 5, next-day t -> t+1).
- Non-Causal Framing: Model prediction differences represent hypothetical
  statistical calculations under model assumptions, NOT proof of causal efficacy.
- Input Immutability: Baseline observations are strictly preserved without mutation.
- Explicit Validation: Impossible or out-of-bounds values are rejected with
  explanatory errors rather than silently clipped.
- Out-of-Distribution (OOD) Warnings: Alerts when scenarios fall outside
  training data IQR bounds or violate domain constraints.
- No Future Leakage: Future forecasting simulations only permit modifications
  at or before the forecast origin date t.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Sequence, Union

import numpy as np
import pandas as pd
import torch

from app.data_pipeline.schema import COLUMN_RANGES, PREDICTOR_COLUMNS
from app.services.preprocessing import BehavioralDataPreprocessor
from app.ml.temporal import TemporalPreprocessor, ProductivityLSTM


class SimulationTaskType(str, Enum):
    """Prediction paradigm being simulated."""

    RETROSPECTIVE_ESTIMATION = "retrospective_estimation"  # Milestone 4 same-day model
    FUTURE_FORECASTING = "future_forecasting"             # Milestone 5 next-day model (t -> t+1)


@dataclass
class SimulationScenario:
    """Specification of a hypothetical behavioural scenario."""

    scenario_id: str
    name: str
    task_type: SimulationTaskType
    modifications: dict[str, float]  # Feature name -> modification value
    is_relative: bool = True         # True: delta added to baseline; False: absolute override
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "task_type": self.task_type.value,
            "modifications": self.modifications,
            "is_relative": self.is_relative,
            "description": self.description,
        }


@dataclass
class SimulationResult:
    """Output of a simulated hypothetical scenario compared against baseline."""

    scenario_id: str
    scenario_name: str
    task_type: str
    baseline_input: dict[str, Any]
    simulated_input: dict[str, Any]
    features_modified: list[str]
    baseline_prediction: float
    simulated_prediction: float
    prediction_delta: float
    warnings: list[str] = field(default_factory=list)
    is_out_of_distribution: bool = False
    non_causal_disclaimer: str = (
        "Under this model and its assumptions, the predicted score changes by this amount. "
        "This model calculation does not prove that an empirical change in behaviour will cause "
        "this productivity change in the real world."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "task_type": self.task_type,
            "features_modified": self.features_modified,
            "baseline_prediction": round(self.baseline_prediction, 4),
            "simulated_prediction": round(self.simulated_prediction, 4),
            "prediction_delta": round(self.prediction_delta, 4),
            "is_out_of_distribution": self.is_out_of_distribution,
            "warnings": self.warnings,
            "baseline_input": self.baseline_input,
            "simulated_input": self.simulated_input,
            "non_causal_disclaimer": self.non_causal_disclaimer,
        }


def validate_feature_bounds(
    feature_dict: dict[str, Any],
    custom_ranges: Optional[dict[str, dict[str, float]]] = None,
) -> list[str]:
    """Validate feature values against domain boundaries and logical consistency constraints.

    Args:
        feature_dict: Dictionary of feature names and values.
        custom_ranges: Optional dictionary overriding or extending domain bounds.

    Returns:
        List of warning strings for plausible boundary excursions.

    Raises:
        ValueError: If impossible or negative physical values are encountered.
    """
    ranges = custom_ranges or COLUMN_RANGES
    warnings: list[str] = []

    for feat_name, val in feature_dict.items():
        if val is None or pd.isna(val):
            continue

        try:
            num_val = float(val)
        except (ValueError, TypeError):
            continue

        # Check physical/domain bounds
        if feat_name in ranges:
            r = ranges[feat_name]
            min_val = r.get("min")
            max_val = r.get("max")
            warn_min = r.get("warn_min")
            warn_max = r.get("warn_max")

            if min_val is not None and num_val < min_val:
                raise ValueError(
                    f"Invalid value for '{feat_name}': {num_val} is below absolute minimum {min_val}."
                )
            if max_val is not None and num_val > max_val:
                raise ValueError(
                    f"Invalid value for '{feat_name}': {num_val} exceeds absolute maximum {max_val}."
                )

            if warn_min is not None and num_val < warn_min:
                warnings.append(
                    f"Feature '{feat_name}' = {num_val:.2f} is unusually low (plausible min: {warn_min})."
                )
            if warn_max is not None and num_val > warn_max:
                warnings.append(
                    f"Feature '{feat_name}' = {num_val:.2f} is unusually high (plausible max: {warn_max})."
                )

    # Cross-feature logical consistency checks
    focus = float(feature_dict.get("focus_duration_hours", 0.0) or 0.0)
    session = float(feature_dict.get("work_session_duration_hours", 0.0) or 0.0)
    screen = float(feature_dict.get("screen_time_hours", 0.0) or 0.0)
    inact = float(feature_dict.get("inactivity_duration_hours", 0.0) or 0.0)
    tasks_p = float(feature_dict.get("tasks_planned", 0.0) or 0.0)
    tasks_c = float(feature_dict.get("tasks_completed", 0.0) or 0.0)

    if session > 0 and focus > session + 1e-3:
        raise ValueError(
            f"Logical conflict: focus duration ({focus:.2f}h) exceeds work session duration ({session:.2f}h)."
        )

    if screen > 0 and session > screen + 1e-3:
        warnings.append(
            f"Work session duration ({session:.2f}h) exceeds device screen time ({screen:.2f}h)."
        )

    if tasks_p > 0 and tasks_c > tasks_p:
        warnings.append(
            f"Tasks completed ({int(tasks_c)}) exceeds tasks planned ({int(tasks_p)})."
        )

    if session > 0 and (focus + inact) > session + 0.5:
        warnings.append(
            f"Sum of focus ({focus:.2f}h) and inactivity ({inact:.2f}h) exceeds work session duration ({session:.2f}h)."
        )

    return warnings


def detect_out_of_distribution(
    feature_dict: dict[str, Any],
    iqr_bounds: Optional[dict[str, dict[str, float]]] = None,
) -> tuple[bool, list[str]]:
    """Detect whether simulated features fall outside training IQR bounds."""
    if not iqr_bounds:
        return False, []

    ood_warnings: list[str] = []
    is_ood = False

    for feat_name, val in feature_dict.items():
        if val is None or pd.isna(val):
            continue
        if feat_name in iqr_bounds:
            bounds = iqr_bounds[feat_name]
            lower = bounds.get("lower", -float("inf"))
            upper = bounds.get("upper", float("inf"))
            num_val = float(val)

            if num_val < lower or num_val > upper:
                is_ood = True
                ood_warnings.append(
                    f"Feature '{feat_name}' = {num_val:.2f} is outside training IQR bounds [{lower:.2f}, {upper:.2f}]."
                )

    return is_ood, ood_warnings


class WhatIfSimulator:
    """Simulation engine supporting both same-day retrospective and next-day forecasting models."""

    def __init__(
        self,
        retrospective_model: Optional[Any] = None,
        retrospective_preprocessor: Optional[BehavioralDataPreprocessor] = None,
        forecasting_model: Optional[ProductivityLSTM] = None,
        forecasting_preprocessor: Optional[TemporalPreprocessor] = None,
        iqr_bounds: Optional[dict[str, dict[str, float]]] = None,
    ):
        self.retro_model = retrospective_model
        self.retro_preprocessor = retrospective_preprocessor
        self.forecasting_model = forecasting_model
        self.forecasting_preprocessor = forecasting_preprocessor
        self.iqr_bounds = iqr_bounds or {}

    def simulate_retrospective(
        self,
        baseline_record: Union[dict[str, Any], pd.Series, pd.DataFrame],
        scenario: SimulationScenario,
    ) -> SimulationResult:
        """Run hypothetical what-if scenario on same-day retrospective model (Milestone 4).

        Args:
            baseline_record: Dictionary or single-row Series/DataFrame of baseline observations.
            scenario: SimulationScenario specifying feature modifications.

        Returns:
            SimulationResult comparing simulated prediction against baseline.
        """
        if self.retro_model is None or self.retro_preprocessor is None:
            raise RuntimeError("Retrospective model and preprocessor must be loaded before simulation.")

        if scenario.task_type != SimulationTaskType.RETROSPECTIVE_ESTIMATION:
            raise ValueError(
                f"Scenario '{scenario.scenario_id}' has task type '{scenario.task_type.value}', "
                f"expected '{SimulationTaskType.RETROSPECTIVE_ESTIMATION.value}'."
            )

        # 1. Extract clean baseline dictionary without mutating input
        if isinstance(baseline_record, pd.DataFrame):
            if len(baseline_record) != 1:
                raise ValueError(f"Expected single-row DataFrame, got {len(baseline_record)} rows.")
            base_dict = baseline_record.iloc[0].to_dict()
        elif isinstance(baseline_record, pd.Series):
            base_dict = baseline_record.to_dict()
        else:
            base_dict = deepcopy(baseline_record)

        # Validate baseline input
        base_warnings = validate_feature_bounds(base_dict)

        # 2. Apply modifications to create simulated input (immutable copy)
        sim_dict = deepcopy(base_dict)
        features_modified: list[str] = []

        for feat_name, mod_val in scenario.modifications.items():
            if feat_name not in base_dict and feat_name not in PREDICTOR_COLUMNS:
                raise ValueError(
                    f"Unknown feature '{feat_name}' in scenario modifications. "
                    f"Cannot modify unrecognized attributes."
                )

            orig_val = float(base_dict.get(feat_name, 0.0) or 0.0)
            if scenario.is_relative:
                new_val = orig_val + float(mod_val)
            else:
                new_val = float(mod_val)

            sim_dict[feat_name] = new_val
            features_modified.append(feat_name)

        # 3. Recalculate coupled engineered features if core inputs changed
        if "focus_duration_hours" in features_modified or "work_session_duration_hours" in features_modified:
            foc = float(sim_dict.get("focus_duration_hours", 0.0) or 0.0)
            ses = float(sim_dict.get("work_session_duration_hours", 0.0) or 0.0)
            sim_dict["work_session_utilization"] = min(1.0, (foc / ses)) if ses > 0 else 0.0

        if "tasks_completed" in features_modified or "tasks_planned" in features_modified:
            comp = float(sim_dict.get("tasks_completed", 0.0) or 0.0)
            plan = float(sim_dict.get("tasks_planned", 0.0) or 0.0)
            sim_dict["task_completion_rate"] = min(1.0, (comp / plan)) if plan > 0 else 1.0

        if "inactivity_duration_hours" in features_modified or "work_session_duration_hours" in features_modified:
            ina = float(sim_dict.get("inactivity_duration_hours", 0.0) or 0.0)
            ses = float(sim_dict.get("work_session_duration_hours", 0.0) or 0.0)
            sim_dict["inactivity_ratio"] = min(1.0, (ina / ses)) if ses > 0 else 0.0

        # 4. Validate simulated inputs
        sim_warnings = validate_feature_bounds(sim_dict)
        all_warnings = base_warnings + sim_warnings

        # Check OOD status
        is_ood, ood_warns = detect_out_of_distribution(sim_dict, self.iqr_bounds)
        all_warnings.extend(ood_warns)

        # 5. Format into single-row DataFrames and predict using preprocessor
        base_df = pd.DataFrame([base_dict])
        sim_df = pd.DataFrame([sim_dict])

        # Preprocess features
        base_prep = self.retro_preprocessor.transform(base_df)
        sim_prep = self.retro_preprocessor.transform(sim_df)

        base_pred = float(self.retro_model.predict(base_prep.X)[0])
        sim_pred = float(self.retro_model.predict(sim_prep.X)[0])
        delta = sim_pred - base_pred

        disclaimer = (
            f"Under this retrospective regression model, the predicted productivity score changes by {delta:+.2f} points "
            f"(from {base_pred:.2f} to {sim_pred:.2f}). This hypothetical model calculation does not demonstrate that a "
            f"real-world intervention will cause this change."
        )

        return SimulationResult(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            task_type=scenario.task_type.value,
            baseline_input={k: round(v, 4) if isinstance(v, float) else v for k, v in base_dict.items() if k in features_modified or k in ["focus_duration_hours", "productivity_score", "work_session_duration_hours"]},
            simulated_input={k: round(v, 4) if isinstance(v, float) else v for k, v in sim_dict.items() if k in features_modified or k in ["focus_duration_hours", "productivity_score", "work_session_duration_hours"]},
            features_modified=features_modified,
            baseline_prediction=base_pred,
            simulated_prediction=sim_pred,
            prediction_delta=delta,
            warnings=all_warnings,
            is_out_of_distribution=is_ood,
            non_causal_disclaimer=disclaimer,
        )

    def simulate_forecasting(
        self,
        baseline_sequence: np.ndarray,
        scenario: SimulationScenario,
        feature_names: Sequence[str],
        origin_date: Optional[str] = None,
    ) -> SimulationResult:
        """Run hypothetical what-if scenario on next-day forecasting model (Milestone 5).

        Strictly enforces that modifications only apply to the forecast origin
        timestep (index -1 in the lookback sequence). Future observations > t
        can never be passed into or modified by this interface.

        Args:
            baseline_sequence: Array of shape (1, lookback, num_features) or (lookback, num_features).
            scenario: SimulationScenario specifying modifications at the forecast origin.
            feature_names: Ordered list of feature names matching sequence columns.
            origin_date: Optional string identifier for forecast origin date.

        Returns:
            SimulationResult comparing forecasted next-day productivity.
        """
        if self.forecasting_model is None or self.forecasting_preprocessor is None:
            raise RuntimeError("Forecasting model and preprocessor must be loaded before simulation.")

        if scenario.task_type != SimulationTaskType.FUTURE_FORECASTING:
            raise ValueError(
                f"Scenario '{scenario.scenario_id}' has task type '{scenario.task_type.value}', "
                f"expected '{SimulationTaskType.FUTURE_FORECASTING.value}'."
            )

        seq_arr = np.asarray(baseline_sequence, dtype=np.float32)
        if seq_arr.ndim == 2:
            seq_arr = np.expand_dims(seq_arr, axis=0)
        elif seq_arr.ndim != 3 or seq_arr.shape[0] != 1:
            raise ValueError(f"Expected sequence array of shape (1, L, F) or (L, F), got {seq_arr.shape}.")

        L = seq_arr.shape[1]
        F = seq_arr.shape[2]

        if len(feature_names) != F:
            raise ValueError(f"Feature names count ({len(feature_names)}) does not match sequence dim ({F}).")

        feat_idx_map = {name: i for i, name in enumerate(feature_names)}

        # Extract origin timestep features (index -1)
        origin_feats_base = seq_arr[0, -1, :].copy()
        base_dict = {name: float(origin_feats_base[i]) for name, i in feat_idx_map.items()}
        base_warnings = validate_feature_bounds(base_dict)

        # Modify ONLY origin timestep (day t)
        sim_seq = seq_arr.copy()
        sim_dict = deepcopy(base_dict)
        features_modified: list[str] = []

        for feat_name, mod_val in scenario.modifications.items():
            if feat_name not in feat_idx_map:
                raise ValueError(
                    f"Unknown feature '{feat_name}' for forecasting sequence. "
                    f"Available sequence features: {list(feature_names)}"
                )

            idx = feat_idx_map[feat_name]
            orig_val = float(origin_feats_base[idx])
            new_val = orig_val + float(mod_val) if scenario.is_relative else float(mod_val)

            sim_seq[0, -1, idx] = np.float32(new_val)
            sim_dict[feat_name] = new_val
            features_modified.append(feat_name)

        # Validate simulated origin features
        sim_warnings = validate_feature_bounds(sim_dict)
        all_warnings = base_warnings + sim_warnings

        is_ood, ood_warns = detect_out_of_distribution(sim_dict, self.iqr_bounds)
        all_warnings.extend(ood_warns)

        # Preprocess both sequences through TemporalPreprocessor
        X_base_scaled = self.forecasting_preprocessor.transform_X(seq_arr)
        X_sim_scaled = self.forecasting_preprocessor.transform_X(sim_seq)

        # Predict using PyTorch model (evaluation mode)
        self.forecasting_model.eval()
        with torch.no_grad():
            t_base = torch.from_numpy(X_base_scaled.astype(np.float32))
            t_sim = torch.from_numpy(X_sim_scaled.astype(np.float32))

            pred_base_scaled = self.forecasting_model(t_base).numpy().reshape(-1, 1)
            pred_sim_scaled = self.forecasting_model(t_sim).numpy().reshape(-1, 1)

        base_pred = float(np.asarray(self.forecasting_preprocessor.inverse_transform_y(pred_base_scaled)).ravel()[0])
        sim_pred = float(np.asarray(self.forecasting_preprocessor.inverse_transform_y(pred_sim_scaled)).ravel()[0])
        delta = sim_pred - base_pred

        disclaimer = (
            f"Under this temporal forecasting LSTM model, next-day predicted productivity changes by {delta:+.2f} points "
            f"(from {base_pred:.2f} to {sim_pred:.2f}). This hypothetical model calculation does not demonstrate that a "
            f"real-world intervention will cause this future change."
        )

        return SimulationResult(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            task_type=scenario.task_type.value,
            baseline_input={k: round(v, 4) for k, v in base_dict.items() if k in features_modified or k in ["focus_duration_hours", "productivity_score"]},
            simulated_input={k: round(v, 4) for k, v in sim_dict.items() if k in features_modified or k in ["focus_duration_hours", "productivity_score"]},
            features_modified=features_modified,
            baseline_prediction=base_pred,
            simulated_prediction=sim_pred,
            prediction_delta=delta,
            warnings=all_warnings,
            is_out_of_distribution=is_ood,
            non_causal_disclaimer=disclaimer,
        )

    def run_scenario_suite(
        self,
        baseline_record: Union[dict[str, Any], pd.Series, pd.DataFrame],
        scenarios: Sequence[SimulationScenario],
    ) -> list[SimulationResult]:
        """Run a batch of hypothetical scenarios against the same baseline record."""
        results: list[SimulationResult] = []
        for sc in scenarios:
            if sc.task_type == SimulationTaskType.RETROSPECTIVE_ESTIMATION:
                res = self.simulate_retrospective(baseline_record, sc)
            else:
                raise ValueError(
                    f"run_scenario_suite on single record expects RETROSPECTIVE_ESTIMATION, got {sc.task_type}."
                )
            results.append(res)
        return results
