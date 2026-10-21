"""Tests for synthetic behavioural data generation, scenarios, and persistence."""

import json
from pathlib import Path
import pandas as pd
import pytest

from app.services.synthetic_data import (
    RAW_COLUMNS,
    generate_synthetic_data,
    save_synthetic_data,
)


def test_generator_returns_expected_schema():
    df = generate_synthetic_data(
        n_users=3,
        n_days=10,
        seed=42,
    )

    assert list(df.columns) == RAW_COLUMNS
    assert len(df) == 30


def test_generator_is_reproducible():
    first = generate_synthetic_data(
        n_users=3,
        n_days=10,
        seed=42,
    )
    second = generate_synthetic_data(
        n_users=3,
        n_days=10,
        seed=42,
    )

    pd.testing.assert_frame_equal(first, second)


def test_different_seeds_produce_different_data():
    first = generate_synthetic_data(n_users=3, n_days=10, seed=42)
    second = generate_synthetic_data(n_users=3, n_days=10, seed=99)
    assert not first["productivity_score"].equals(second["productivity_score"])


def test_user_date_pairs_are_unique():
    df = generate_synthetic_data(
        n_users=5,
        n_days=20,
    )

    assert not df.duplicated(
        subset=["user_id", "record_date"]
    ).any()


def test_numeric_ranges_are_valid():
    df = generate_synthetic_data(
        n_users=5,
        n_days=20,
    )

    assert df["sleep_hours"].between(0, 24).all()
    assert df["focus_duration_hours"].between(0, 16).all()
    assert df["screen_time_hours"].between(0, 24).all()
    assert df["tasks_completed"].ge(0).all()
    assert (
        df["tasks_completed"] <= df["tasks_planned"]
    ).all()
    assert df["productivity_score"].between(0, 100).all()


def test_optional_fields_can_be_missing():
    df = generate_synthetic_data(
        n_users=50,
        n_days=90,
        seed=42,
    )

    assert df["mood_score"].isna().any()
    assert df["perceived_stress"].isna().any()


def test_invalid_generator_parameters_are_rejected():
    with pytest.raises(ValueError):
        generate_synthetic_data(n_users=0)

    with pytest.raises(ValueError):
        generate_synthetic_data(n_days=0)


def test_scenarios_generate_expected_variation():
    baseline = generate_synthetic_data(n_users=5, n_days=30, seed=42, scenario="baseline")
    stress = generate_synthetic_data(n_users=5, n_days=30, seed=42, scenario="stress_spike")
    focus_drop = generate_synthetic_data(n_users=5, n_days=30, seed=42, scenario="focus_drop")

    # In the stress spike scenario, interruptions and perceived stress should be higher in final days
    assert stress.iloc[-10:]["perceived_stress"].mean() >= baseline.iloc[-10:]["perceived_stress"].mean()
    # In focus drop scenario, focus duration should be lower
    assert focus_drop.iloc[-10:]["focus_duration_hours"].mean() <= baseline.iloc[-10:]["focus_duration_hours"].mean()


def test_invalid_scenario_is_rejected():
    with pytest.raises(ValueError) as exc:
        generate_synthetic_data(scenario="non_existent_scenario")
    assert "Unsupported scenario" in str(exc.value)


def test_csv_can_be_saved_and_reloaded(tmp_path):
    df = generate_synthetic_data(
        n_users=2,
        n_days=5,
    )

    output = tmp_path / "records.csv"
    saved_path = save_synthetic_data(df, output)
    reloaded = pd.read_csv(saved_path)

    assert saved_path.exists()
    assert len(reloaded) == len(df)
    assert list(reloaded.columns) == RAW_COLUMNS


def test_no_accidental_overwrite(tmp_path):
    df = generate_synthetic_data(n_users=2, n_days=5)
    output = tmp_path / "protected_records.csv"

    # First write succeeds
    save_synthetic_data(df, output, overwrite=False)

    # Second write without overwrite=True must raise FileExistsError
    with pytest.raises(FileExistsError):
        save_synthetic_data(df, output, overwrite=False)


def test_overwrite_allowed_when_explicit(tmp_path):
    df1 = generate_synthetic_data(n_users=2, n_days=5, seed=1)
    df2 = generate_synthetic_data(n_users=2, n_days=5, seed=2)
    output = tmp_path / "records_overwrite.csv"

    save_synthetic_data(df1, output, overwrite=False)
    save_synthetic_data(df2, output, overwrite=True)

    reloaded = pd.read_csv(output)
    assert len(reloaded) == len(df2)


def test_metadata_sidecar_generated(tmp_path):
    df = generate_synthetic_data(n_users=2, n_days=5)
    output = tmp_path / "dataset_with_meta.csv"

    save_synthetic_data(df, output, save_metadata=True)
    meta_path = output.with_suffix(".metadata.json")

    assert meta_path.exists()
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["schema_version"] == "0.1.0"
    assert meta["statistics"]["row_count"] == 10
    assert "productivity_score" in meta["target_specification"]["target_column"]
