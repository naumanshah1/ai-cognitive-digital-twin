"""Integration test for Milestone 7 end-to-end execution.

Verifies that run_milestone7_experiments executes seamlessly on a compact fixture,
generates the markdown research report, metadata JSON, and diagnostic plots,
and returns deterministic output structures.
"""

import json
from pathlib import Path
import pytest

from scripts.run_milestone7 import run_milestone7_experiments


def test_milestone7_end_to_end_pipeline_execution(tmp_path, monkeypatch):
    """Verify that Milestone 7 runs end to end, generating all expected artifacts."""
    # Monkeypatch experiment directories to write into temporary directory
    exp_dir = tmp_path / "research" / "experiments" / "milestone7"
    results_dir = exp_dir / "results"
    exp_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Run on a compact cohort (3 users, 35 days) for fast deterministic integration test
    metadata = run_milestone7_experiments(n_users=3, n_days=35, seed=42)

    assert isinstance(metadata, dict)
    assert metadata["milestone"] == "Milestone 7 — Recommendations & What-If Simulation"
    assert metadata["cohort"]["users_count"] == 3

    # Check recommendation engine metadata
    rec_meta = metadata["recommendation_engine"]
    assert "total_recommendations_generated" in rec_meta
    assert isinstance(rec_meta["category_distribution"], dict)

    # Check simulation engine metadata
    sim_meta = metadata["simulation_engine"]
    assert "retrospective_scenarios" in sim_meta
    assert len(sim_meta["retrospective_scenarios"]) >= 5
    assert "forecasting_scenario" in sim_meta

    # Check generated report and metadata on standard paths
    report_file = Path("research/experiments/milestone7/recommendation_simulation_report.md")
    metadata_file = Path("research/experiments/milestone7/experiment_metadata.json")

    assert report_file.exists(), f"Report file {report_file} was not generated."
    assert metadata_file.exists(), f"Metadata file {metadata_file} was not generated."

    report_content = report_file.read_text(encoding="utf-8")
    assert "# Behavioural Recommendations and What-If Simulation" in report_content
    assert "Priority" in report_content
    assert "Non-Diagnostic Framing" in report_content

    # Check diagnostic plots
    assert Path("research/experiments/milestone7/results/recommendations_by_category.png").exists()
    assert Path("research/experiments/milestone7/results/simulated_productivity_deltas.png").exists()
    assert Path("research/experiments/milestone7/results/what_if_sensitivity_tornado.png").exists()
