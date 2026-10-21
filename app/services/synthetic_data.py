"""Synthetic behavioural data generator for AI Cognitive Digital Twin.

Provides reproducible simulation of daily behavioural records for pipeline
development, validation, and controlled experiments.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from app.data_pipeline.schema import RAW_COLUMNS, SCHEMA_VERSION

DEFAULT_SEED = 42

DEFAULT_MISSINGNESS_RATES = {
    "sleep_quality": 0.03,
    "mood_score": 0.15,
    "perceived_stress": 0.15,
}

SUPPORTED_SCENARIOS = ("baseline", "stress_spike", "focus_drop")


def generate_synthetic_data(
    n_users: int = 50,
    n_days: int = 90,
    start_date: str = "2026-01-01",
    seed: int = DEFAULT_SEED,
    missingness_rates: Optional[dict[str, float]] = None,
    scenario: str = "baseline",
) -> pd.DataFrame:
    """Generate reproducible, simulated daily behavioural records.

    Synthetic outcomes are generated from an explicit heuristic.
    They are not validated measures of real human productivity.
    """
    if n_users < 1:
        raise ValueError("n_users must be at least 1")

    if n_days < 1:
        raise ValueError("n_days must be at least 1")

    if scenario not in SUPPORTED_SCENARIOS:
        raise ValueError(
            f"Unsupported scenario '{scenario}'. Supported scenarios: {SUPPORTED_SCENARIOS}"
        )

    dates = pd.date_range(
        start=pd.Timestamp(start_date),
        periods=n_days,
        freq="D",
    )

    rng = np.random.default_rng(seed)
    records = []

    # Shift threshold day for scenario-based behavioural shifts (e.g. final 30% of days)
    scenario_cutoff_idx = int(0.70 * n_days) if scenario != "baseline" else n_days + 1

    for user_index in range(n_users):
        user_id = f"synthetic_{user_index + 1:04d}"

        # Stable baseline differences between simulated individuals
        user_sleep_baseline = rng.normal(7.5, 0.6)
        user_focus_baseline = rng.normal(4.5, 0.8)
        user_consistency = rng.uniform(0.75, 1.0)

        for day_index, record_date in enumerate(dates):
            # Check scenario adjustments
            in_scenario_shift = day_index >= scenario_cutoff_idx

            sleep_mod = -0.6 if (in_scenario_shift and scenario == "stress_spike") else 0.0
            focus_mod = -1.5 if (in_scenario_shift and scenario == "focus_drop") else 0.0
            interruption_mod = 3 if (in_scenario_shift and scenario == "stress_spike") else 0

            # Day-to-day variation
            sleep = np.clip(
                user_sleep_baseline + sleep_mod + rng.normal(0, 0.8),
                3.0,
                11.0,
            )

            focus = np.clip(
                user_focus_baseline
                + focus_mod
                + rng.normal(0, 1.2)
                + 0.25 * (sleep - 7.0),
                0.0,
                12.0,
            )

            screen_time = np.clip(
                4.0 + 0.6 * focus + (1.5 if in_scenario_shift and scenario == "focus_drop" else 0.0) + rng.normal(0, 1.5),
                0.0,
                16.0,
            )

            work_duration = np.clip(
                focus + rng.uniform(0.5, 2.5),
                focus,
                16.0,
            )

            inactivity = np.clip(
                work_duration - focus + rng.normal(0, 0.3),
                0.0,
                work_duration,
            )

            interruption_lambda = max(0.5, 4.0 - 0.12 * focus + interruption_mod)
            interruptions = int(rng.poisson(interruption_lambda))

            tasks_planned = int(rng.integers(3, 9))
            task_difficulty = float(rng.uniform(1.5, 4.5))

            # Synthetic productivity-generating rule.
            # Deliberately an explicit heuristic, not a scientifically validated human model.
            latent_score = (
                30.0
                + 4.0 * focus
                + 3.0 * (sleep - 7.0)
                + 3.0 * user_consistency
                - 1.5 * interruptions
                - 2.0 * (task_difficulty - 3.0)
                + rng.normal(0, 7.0)
            )

            productivity_score = float(np.clip(latent_score, 0.0, 100.0))

            # Completion is a separate simulated observation
            completion_probability = np.clip(
                0.25
                + 0.06 * focus
                + 0.025 * (sleep - 7.0)
                - 0.025 * (task_difficulty - 3.0),
                0.05,
                0.95,
            )

            tasks_completed = int(
                rng.binomial(tasks_planned, completion_probability)
            )

            sleep_quality = int(
                np.clip(
                    np.rint(3.0 + 0.7 * (sleep - 7.0) + rng.normal(0, 0.7)),
                    1,
                    5,
                )
            )

            mood_score = int(rng.integers(1, 6))

            stress_val = 3.0 + 0.25 * interruptions - 0.2 * focus + rng.normal(0, 0.8)
            if in_scenario_shift and scenario == "stress_spike":
                stress_val += 1.2

            perceived_stress = int(
                np.clip(
                    np.rint(stress_val),
                    1,
                    5,
                )
            )

            records.append(
                {
                    "user_id": user_id,
                    "record_date": record_date.date().isoformat(),
                    "sleep_hours": round(float(sleep), 2),
                    "sleep_quality": sleep_quality,
                    "focus_duration_hours": round(float(focus), 2),
                    "screen_time_hours": round(float(screen_time), 2),
                    "tasks_planned": tasks_planned,
                    "tasks_completed": tasks_completed,
                    "task_difficulty_avg": round(task_difficulty, 2),
                    "work_session_duration_hours": round(float(work_duration), 2),
                    "inactivity_duration_hours": round(float(inactivity), 2),
                    "interruption_count": interruptions,
                    "mood_score": mood_score,
                    "perceived_stress": perceived_stress,
                    "productivity_score": round(productivity_score, 2),
                }
            )

    df = pd.DataFrame(records, columns=RAW_COLUMNS)

    # Missingness treatment for optional / self-reported fields
    rates = DEFAULT_MISSINGNESS_RATES if missingness_rates is None else missingness_rates
    for column, probability in rates.items():
        if column in df.columns and probability > 0:
            missing_mask = rng.random(len(df)) < probability
            df.loc[missing_mask, column] = np.nan

    # Preserve nullable integer semantics for rating columns
    for column in ["sleep_quality", "mood_score", "perceived_stress"]:
        if column in df.columns:
            df[column] = df[column].astype("Int64")

    return df


def generate_dataset_metadata(
    df: pd.DataFrame,
    seed: int = DEFAULT_SEED,
    n_users: int = 50,
    n_days: int = 90,
    start_date: str = "2026-01-01",
    scenario: str = "baseline",
    missingness_rates: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """Generate provenance metadata for a generated synthetic dataset."""
    actual_missing = {
        col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().any()
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_type": "synthetic_behavioral_records",
        "provenance": "synthetic_heuristic_simulation",
        "generator_module": "app.services.synthetic_data",
        "generation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": seed,
        "parameters": {
            "n_users": n_users,
            "n_days": n_days,
            "start_date": start_date,
            "scenario": scenario,
            "configured_missingness_rates": missingness_rates or DEFAULT_MISSINGNESS_RATES,
        },
        "statistics": {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "date_range": [str(df["record_date"].min()), str(df["record_date"].max())],
            "unique_users": int(df["user_id"].nunique()),
            "missing_value_counts": actual_missing,
        },
        "target_specification": {
            "target_column": "productivity_score",
            "valid_range": [0.0, 100.0],
            "nature": "synthetic_heuristic_outcome",
            "leakage_rule": "productivity_score and target-derived features must not be used as predictor features.",
        },
        "limitations": (
            "This synthetic dataset was generated for software engineering, pipeline validation, "
            "and controlled drift simulation. It does not represent validated empirical human psychology."
        ),
    }


def save_synthetic_data(
    df: pd.DataFrame,
    output_path: str | Path = "data/synthetic/behavioral_records.csv",
    overwrite: bool = False,
    save_metadata: bool = True,
    metadata_extra: Optional[dict[str, Any]] = None,
) -> Path:
    """Save generated records to CSV safely, with optional metadata sidecar.

    Raises FileExistsError if output_path exists and overwrite is False.
    """
    path = Path(output_path)
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Destination file already exists: {path}. Set overwrite=True to replace it."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

    if save_metadata:
        meta_dict = generate_dataset_metadata(df)
        if metadata_extra:
            meta_dict.update(metadata_extra)
        meta_path = path.with_suffix(".metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

    return path
