"""End-to-end integration test for Milestone 6 Behavioural Drift Detection pipeline."""

import json
from pathlib import Path
import pytest

from scripts.run_milestone6 import run_milestone6_experiments


def test_milestone6_end_to_end_pipeline_execution(tmp_path: Path):
    """Verify that Milestone 6 execution completes end-to-end and produces all required artifacts."""
    metadata = run_milestone6_experiments(
        n_users=3,
        n_days=40,
        seed=42,
        ref_window=10,
        cmp_window=5,
        output_root=tmp_path,
    )

    exp_dir = tmp_path / "research" / "experiments" / "milestone6"
    results_dir = exp_dir / "results"

    # 1. Verify Research Report
    report_path = exp_dir / "behavioural_drift_report.md"
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "# Behavioural Drift Detection — Research Report" in content
    assert "Controlled Experiment Results" in content
    assert "Research Limitations" in content

    # 2. Verify Machine-Readable Metadata
    meta_path = exp_dir / "experiment_metadata.json"
    assert meta_path.exists()
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
    assert meta_data["milestone"] == "Milestone 6 — Behavioural Drift Detection"
    assert "scenarios_evaluated" in meta_data
    assert "stable_control" in meta_data["scenarios_evaluated"]
    assert "focus_drop" in meta_data["scenarios_evaluated"]
    assert "stress_spike" in meta_data["scenarios_evaluated"]

    # 3. Verify Diagnostic Publication Plots
    assert (results_dir / "reference_vs_monitoring_distributions.png").exists()
    assert (results_dir / "drift_timeline.png").exists()
    assert (results_dir / "scenario_performance_summary.png").exists()
