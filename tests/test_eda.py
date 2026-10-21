"""Unit tests for Exploratory Data Analysis (EDA) module."""

import numpy as np
import pandas as pd
import pytest

from app.ml.eda import generate_eda_markdown_report, perform_exploratory_data_analysis
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    return generate_synthetic_data(n_users=4, n_days=10, seed=42)


def test_eda_returns_correct_high_level_metrics(sample_dataset):
    eda = perform_exploratory_data_analysis(sample_dataset, generate_plots=False)

    assert eda.total_rows == 40
    assert eda.total_columns == 15
    assert eda.unique_users == 4
    assert eda.total_days == 10
    assert eda.records_per_user_mean == 10.0
    assert eda.duplicate_user_days == 0
    assert eda.duplicate_rows == 0


def test_eda_calculates_missingness_correctly(sample_dataset):
    df_missing = sample_dataset.copy()
    df_missing.loc[0:4, "mood_score"] = np.nan

    eda = perform_exploratory_data_analysis(df_missing, generate_plots=False)
    assert eda.missingness_counts["mood_score"] >= 5
    assert eda.missingness_percentages["mood_score"] >= 12.5


def test_eda_computes_numeric_summary_statistics(sample_dataset):
    eda = perform_exploratory_data_analysis(sample_dataset, generate_plots=False)

    assert "focus_duration_hours" in eda.numeric_summaries
    focus_sum = eda.numeric_summaries["focus_duration_hours"]

    assert focus_sum["mean"] > 0.0
    assert focus_sum["min"] <= focus_sum["median"] <= focus_sum["max"]
    assert focus_sum["iqr"] >= 0.0


def test_eda_detects_duplicate_user_days(sample_dataset):
    # Duplicate first row
    dup_df = pd.concat([sample_dataset, sample_dataset.iloc[[0]]], ignore_index=True)
    eda = perform_exploratory_data_analysis(dup_df, generate_plots=False)

    assert eda.duplicate_user_days == 1
    assert eda.duplicate_rows == 1


def test_eda_correlation_analysis_structure(sample_dataset):
    eda = perform_exploratory_data_analysis(sample_dataset, generate_plots=False)

    assert "focus_duration_hours" in eda.pearson_correlations
    assert "sleep_hours" in eda.pearson_correlations["focus_duration_hours"]
    # Correlation with self must be 1.0
    assert eda.pearson_correlations["focus_duration_hours"]["focus_duration_hours"] == 1.0


def test_eda_user_heterogeneity_metrics(sample_dataset):
    eda = perform_exploratory_data_analysis(sample_dataset, generate_plots=False)

    assert "focus_duration_hours" in eda.heterogeneity_metrics
    focus_het = eda.heterogeneity_metrics["focus_duration_hours"]
    assert "between_user_std" in focus_het
    assert "mean_within_user_std" in focus_het
    assert focus_het["between_user_std"] >= 0.0


def test_eda_markdown_report_generation(sample_dataset):
    eda = perform_exploratory_data_analysis(sample_dataset, generate_plots=False)
    report_md = generate_eda_markdown_report(eda)

    assert "# Behavioural Dataset — Exploratory Data Analysis" in report_md
    assert "**Total Daily Records:** 40" in report_md
    assert "Unique Simulated Users:** 4" in report_md


def test_eda_empty_dataframe_raises_error():
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError):
        perform_exploratory_data_analysis(empty_df)


def test_eda_plot_generation(sample_dataset, tmp_path):
    eda = perform_exploratory_data_analysis(
        sample_dataset,
        output_dir=tmp_path,
        generate_plots=True,
    )

    assert len(eda.generated_plots) >= 4
    for plot_path in eda.generated_plots:
        assert (tmp_path / plot_path).exists()
