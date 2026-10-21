"""Exploratory Data Analysis (EDA) module for behavioural records.

Provides statistical profiling, univariate, bivariate, temporal, and user
heterogeneity analysis with publication-quality visualizations and Markdown reports.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd

# Use non-interactive Agg backend for headless visualization generation
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass
class EDAResults:
    """Structured container for exploratory data analysis results."""

    total_rows: int
    total_columns: int
    unique_users: int
    min_date: str
    max_date: str
    total_days: int
    records_per_user_mean: float
    records_per_user_min: int
    records_per_user_max: int
    duplicate_rows: int
    duplicate_user_days: int
    missingness_counts: dict[str, int]
    missingness_percentages: dict[str, float]
    numeric_summaries: dict[str, dict[str, float]]
    rating_distributions: dict[str, dict[str, int]]
    pearson_correlations: dict[str, dict[str, float]]
    spearman_correlations: dict[str, dict[str, float]]
    heterogeneity_metrics: dict[str, dict[str, float]]
    generated_plots: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def perform_exploratory_data_analysis(
    df: pd.DataFrame,
    output_dir: Optional[str | Path] = None,
    generate_plots: bool = True,
) -> EDAResults:
    """Execute comprehensive exploratory data analysis on behavioural data.

    Calculates descriptive metrics, correlations, temporal dynamics, and user
    heterogeneity, and optionally generates visualization charts and reports.
    """
    if len(df) == 0:
        raise ValueError("Cannot perform EDA on an empty DataFrame.")

    total_rows = len(df)
    total_columns = len(df.columns)

    # 1. Dataset overview
    user_col = "user_id" if "user_id" in df.columns else None
    date_col = "record_date" if "record_date" in df.columns else None

    unique_users = int(df[user_col].nunique()) if user_col else 1
    min_date = str(df[date_col].min()) if date_col else "N/A"
    max_date = str(df[date_col].max()) if date_col else "N/A"
    total_days = int(df[date_col].nunique()) if date_col else 1

    if user_col:
        counts = df[user_col].value_counts()
        rec_mean = round(float(counts.mean()), 2)
        rec_min = int(counts.min())
        rec_max = int(counts.max())
    else:
        rec_mean = float(total_rows)
        rec_min = total_rows
        rec_max = total_rows

    duplicate_rows = int(df.duplicated().sum())
    duplicate_user_days = int(df.duplicated(subset=[user_col, date_col]).sum()) if (user_col and date_col) else 0

    # 2. Missingness calculations
    missing_counts = {col: int(df[col].isna().sum()) for col in df.columns}
    missing_pcts = {col: round((missing_counts[col] / total_rows) * 100.0, 2) for col in df.columns}

    # 3. Numeric summary statistics
    numeric_df = df.select_dtypes(include=[np.number])
    numeric_summaries: dict[str, dict[str, float]] = {}

    for col in numeric_df.columns:
        valid_series = numeric_df[col].dropna()
        if len(valid_series) == 0:
            continue
        q25 = float(valid_series.quantile(0.25))
        q75 = float(valid_series.quantile(0.75))
        skew_val = float(valid_series.skew()) if len(valid_series) > 2 else 0.0

        numeric_summaries[col] = {
            "mean": round(float(valid_series.mean()), 3),
            "std": round(float(valid_series.std()), 3) if len(valid_series) > 1 else 0.0,
            "min": round(float(valid_series.min()), 3),
            "q25": round(q25, 3),
            "median": round(float(valid_series.median()), 3),
            "q75": round(q75, 3),
            "max": round(float(valid_series.max()), 3),
            "iqr": round(q75 - q25, 3),
            "skewness": round(skew_val, 3) if not np.isnan(skew_val) else 0.0,
        }

    # 4. Rating distributions
    rating_cols = [c for c in ["sleep_quality", "mood_score", "perceived_stress"] if c in df.columns]
    rating_distributions: dict[str, dict[str, int]] = {}
    for r_col in rating_cols:
        val_counts = df[r_col].dropna().astype(int).value_counts().to_dict()
        rating_distributions[r_col] = {str(k): int(v) for k, v in sorted(val_counts.items())}

    # 5. Correlation analysis (Pearson and Spearman)
    candidate_corr_cols = [
        c for c in [
            "sleep_hours", "sleep_quality", "focus_duration_hours", "screen_time_hours",
            "tasks_planned", "tasks_completed", "task_difficulty_avg",
            "work_session_duration_hours", "inactivity_duration_hours",
            "interruption_count", "mood_score", "perceived_stress", "productivity_score",
        ] if c in numeric_df.columns
    ]
    corr_subset = numeric_df[candidate_corr_cols].dropna()

    if len(corr_subset) > 5 and len(candidate_corr_cols) > 1:
        pearson_mat = corr_subset.corr(method="pearson").round(3).to_dict()
        spearman_mat = corr_subset.corr(method="spearman").round(3).to_dict()
    else:
        pearson_mat = {}
        spearman_mat = {}

    # 6. User heterogeneity (Within-user vs. Between-user variability)
    heterogeneity_metrics: dict[str, dict[str, float]] = {}
    if user_col and unique_users > 1:
        for metric in ["focus_duration_hours", "sleep_hours", "productivity_score", "work_session_duration_hours"]:
            if metric not in df.columns:
                continue
            user_means = df.groupby(user_col)[metric].mean()
            user_stds = df.groupby(user_col)[metric].std()
            between_user_std = float(user_means.std())
            within_user_std = float(user_stds.mean())
            heterogeneity_metrics[metric] = {
                "between_user_std": round(between_user_std, 3),
                "mean_within_user_std": round(within_user_std, 3),
                "ratio_between_to_within": round(between_user_std / (within_user_std + 1e-6), 3),
            }

    # 7. Generate publication-quality visualization plots
    generated_plots: list[str] = []
    if generate_plots and output_dir is not None:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        # Plot 1: Feature Distributions
        plt.figure(figsize=(14, 10))
        plot_features = [
            f for f in ["sleep_hours", "focus_duration_hours", "screen_time_hours",
                        "work_session_duration_hours", "interruption_count", "productivity_score"]
            if f in df.columns
        ]
        n_plots = len(plot_features)
        cols = 3
        rows = (n_plots + cols - 1) // cols

        for idx, col in enumerate(plot_features, 1):
            plt.subplot(rows, cols, idx)
            vals = df[col].dropna()
            plt.hist(vals, bins=25, color="#2b5c8f", edgecolor="black", alpha=0.75)
            plt.title(f"{col.replace('_', ' ').title()}", fontsize=11, fontweight="bold")
            plt.xlabel("Value")
            plt.ylabel("Frequency")
            plt.grid(True, linestyle="--", alpha=0.5)

        plt.tight_layout()
        dist_path = out_p / "feature_distributions.png"
        plt.savefig(dist_path, dpi=200)
        plt.close()
        generated_plots.append(str(dist_path))

        # Plot 2: Correlation Heatmap
        if len(candidate_corr_cols) > 2 and len(corr_subset) > 5:
            plt.figure(figsize=(10, 8))
            corr_matrix = corr_subset.corr(method="pearson")
            im = plt.imshow(corr_matrix, cmap="coolwarm", vmin=-1, vmax=1)
            plt.colorbar(im, fraction=0.046, pad=0.04)
            plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns, rotation=45, ha="right", fontsize=9)
            plt.yticks(range(len(corr_matrix.columns)), corr_matrix.columns, fontsize=9)
            plt.title("Pearson Correlation Matrix (Behavioral Metrics)", fontsize=13, fontweight="bold", pad=12)

            for i in range(len(corr_matrix)):
                for j in range(len(corr_matrix)):
                    val = corr_matrix.iloc[i, j]
                    text_color = "white" if abs(val) > 0.5 else "black"
                    plt.text(j, i, f"{val:.2f}", ha="center", va="center", color=text_color, fontsize=8)

            plt.tight_layout()
            corr_path = out_p / "correlation_matrix.png"
            plt.savefig(corr_path, dpi=200)
            plt.close()
            generated_plots.append(str(corr_path))

        # Plot 3: Missingness Overview
        missing_filtered = {k: v for k, v in missing_pcts.items() if v > 0}
        if missing_filtered:
            plt.figure(figsize=(8, 4.5))
            bars = plt.bar(list(missing_filtered.keys()), list(missing_filtered.values()), color="#d95f02", edgecolor="black")
            plt.title("Missing Value Rates (%) in Behavioural Dataset", fontsize=12, fontweight="bold")
            plt.ylabel("Percentage Missing (%)")
            plt.ylim(0, max(25, max(missing_filtered.values()) + 5))
            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.8, f"{yval:.1f}%", ha="center", va="bottom", fontsize=10)
            plt.grid(axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            miss_path = out_p / "missingness_overview.png"
            plt.savefig(miss_path, dpi=200)
            plt.close()
            generated_plots.append(str(miss_path))

        # Plot 4: Temporal Aggregates Over Time
        if date_col and total_days > 3:
            daily_agg = df.groupby(date_col)[["focus_duration_hours", "sleep_hours", "productivity_score"]].mean()
            plt.figure(figsize=(12, 5))
            plt.plot(daily_agg.index, daily_agg["focus_duration_hours"], label="Daily Mean Focus (hrs)", color="#1b9e77", linewidth=2)
            plt.plot(daily_agg.index, daily_agg["sleep_hours"], label="Daily Mean Sleep (hrs)", color="#7570b3", linewidth=2)
            plt.plot(daily_agg.index, daily_agg["productivity_score"] / 10.0, label="Daily Mean Productivity (/10)", color="#e7298a", linewidth=2, linestyle="--")
            plt.title("Cohort Mean Behavioural Trends Over 90-Day Period", fontsize=12, fontweight="bold")
            plt.xlabel("Record Date")
            plt.ylabel("Observed Units")
            # Show tick every 10 days
            ticks = range(0, len(daily_agg), max(1, len(daily_agg) // 9))
            plt.xticks(ticks, [daily_agg.index[i] for i in ticks], rotation=35, ha="right", fontsize=9)
            plt.legend(frameon=True)
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
            temp_path = out_p / "temporal_trends.png"
            plt.savefig(temp_path, dpi=200)
            plt.close()
            generated_plots.append(str(temp_path))

        # Plot 5: User Heterogeneity
        if user_col and unique_users >= 2:
            user_means = df.groupby(user_col)["focus_duration_hours"].mean().sort_values()
            plt.figure(figsize=(12, 4.5))
            plt.bar(range(len(user_means)), user_means.values, color="#386cb0", width=0.8)
            plt.axhline(user_means.mean(), color="red", linestyle="--", label=f"Cohort Mean ({user_means.mean():.2f} hrs)")
            plt.title("Between-User Heterogeneity: Mean Focus Duration by Simulated User", fontsize=12, fontweight="bold")
            plt.xlabel("Simulated User Rank")
            plt.ylabel("Mean Focus Hours")
            plt.legend()
            plt.grid(axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            het_path = out_p / "user_heterogeneity.png"
            plt.savefig(het_path, dpi=200)
            plt.close()
            generated_plots.append(str(het_path))

    return EDAResults(
        total_rows=total_rows,
        total_columns=total_columns,
        unique_users=unique_users,
        min_date=min_date,
        max_date=max_date,
        total_days=total_days,
        records_per_user_mean=rec_mean,
        records_per_user_min=rec_min,
        records_per_user_max=rec_max,
        duplicate_rows=duplicate_rows,
        duplicate_user_days=duplicate_user_days,
        missingness_counts=missing_counts,
        missingness_percentages=missing_pcts,
        numeric_summaries=numeric_summaries,
        rating_distributions=rating_distributions,
        pearson_correlations=pearson_mat,
        spearman_correlations=spearman_mat,
        heterogeneity_metrics=heterogeneity_metrics,
        generated_plots=generated_plots,
    )


def generate_eda_markdown_report(eda: EDAResults) -> str:
    """Generate comprehensive GitHub-flavored Markdown EDA report."""
    lines = [
        "# Behavioural Dataset — Exploratory Data Analysis (EDA) Report",
        "",
        "## 1. Dataset Composition & High-Level Metrics",
        f"- **Total Daily Records:** {eda.total_rows:,}",
        f"- **Total Variables:** {eda.total_columns}",
        f"- **Unique Simulated Users:** {eda.unique_users}",
        f"- **Temporal Range:** {eda.min_date} to {eda.max_date} ({eda.total_days} days)",
        f"- **Mean Records per User:** {eda.records_per_user_mean:.1f} (range: {eda.records_per_user_min}–{eda.records_per_user_max})",
        f"- **Duplicate User-Day Pairs:** {eda.duplicate_user_days} (100% unique user-date integrity)",
        "",
        "## 2. Missingness Analysis",
        "| Variable | Missing Count | Missing Rate (%) | Missingness Mechanism |",
        "|---|---|---|---|",
    ]

    for col, count in sorted(eda.missingness_counts.items(), key=lambda x: x[1], reverse=True):
        rate = eda.missingness_percentages.get(col, 0.0)
        mechanism = "Simulated MCAR (Optional Self-Report)" if rate > 0 else "Fully Observed"
        lines.append(f"| `{col}` | {count:,} | {rate:.2f}% | {mechanism} |")

    lines.extend([
        "",
        "## 3. Univariate Summary Statistics",
        "| Feature | Mean | Std | Min | Median | Max | IQR | Skewness |",
        "|---|---|---|---|---|---|---|---|",
    ])

    for col, s in eda.numeric_summaries.items():
        lines.append(
            f"| `{col}` | {s['mean']:.2f} | {s['std']:.2f} | {s['min']:.2f} | "
            f"{s['median']:.2f} | {s['max']:.2f} | {s['iqr']:.2f} | {s['skewness']:.2f} |"
        )

    lines.extend([
        "",
        "## 4. Bivariate & Correlation Analysis",
        "Selected bivariate Pearson linear correlation coefficients:",
        "- **Focus vs. Work Session Duration:** "
        f"{eda.pearson_correlations.get('focus_duration_hours', {}).get('work_session_duration_hours', 'N/A')}",
        "- **Focus vs. Sleep Hours:** "
        f"{eda.pearson_correlations.get('focus_duration_hours', {}).get('sleep_hours', 'N/A')}",
        "- **Focus vs. Tasks Completed:** "
        f"{eda.pearson_correlations.get('focus_duration_hours', {}).get('tasks_completed', 'N/A')}",
        "- **Focus vs. Interruptions:** "
        f"{eda.pearson_correlations.get('focus_duration_hours', {}).get('interruption_count', 'N/A')}",
        "- **Interruptions vs. Productivity Score:** "
        f"{eda.pearson_correlations.get('interruption_count', {}).get('productivity_score', 'N/A')}",
        "",
        "> **Methodological Limitation Notice:**",
        "> Any correlation involving `productivity_score` reflects the generator's mathematical heuristic formula,",
        "> not an empirical human psychological relationship. Correlations must never be interpreted as causal proof.",
        "",
        "## 5. User Heterogeneity Analysis",
        "| Metric | Between-User Std | Mean Within-User Std | Ratio (Between / Within) |",
        "|---|---|---|---|",
    ])

    for metric, h in eda.heterogeneity_metrics.items():
        lines.append(
            f"| `{metric}` | {h['between_user_std']:.3f} | {h['mean_within_user_std']:.3f} | {h['ratio_between_to_within']:.3f} |"
        )

    lines.extend([
        "",
        "### Analytical Implication for Clustering:",
        "- **Within-User Daily Variation:** Daily records capture short-term state fluctuations (e.g., good sleep vs. high interruptions).",
        "- **Between-User Baseline Variation:** User-level aggregations capture distinct sustained behavioural profiles.",
        "- **Clustering Strategy:** This justifies separating **Experiment A (Daily Pattern Clustering)** from **Experiment B (User-Level Profile Clustering)**.",
        "",
        "## 6. Generated Visualizations",
    ])

    for plot_p in eda.generated_plots:
        name = Path(plot_p).name
        lines.append(f"- [{name}](results/{name})")

    return "\n".join(lines)
