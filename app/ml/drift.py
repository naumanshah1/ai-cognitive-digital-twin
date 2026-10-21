"""Behavioural Drift Detection Pipeline for AI Cognitive Digital Twin.

Provides per-user longitudinal distribution shift detection across behavioural
telemetry features, comparing historical reference windows against recent monitoring
windows with multiple-testing correction and non-clinical neutral reporting.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from typing import Any, Optional, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wasserstein_distance

from app.data_pipeline.feature_engineering import engineer_features
from app.services.synthetic_data import generate_synthetic_data

DEFAULT_BEHAVIORAL_DRIFT_FEATURES = [
    "focus_duration_hours",
    "sleep_hours",
    "sleep_quality",
    "screen_time_hours",
    "interruption_count",
    "task_completion_rate",
    "work_session_duration_hours",
    "work_session_utilization",
    "inactivity_duration_hours",
    "inactivity_ratio",
    "perceived_stress",
    "mood_score",
]

FEATURE_METRIC_LABELS: dict[str, str] = {
    "focus_duration_hours": "Focus Duration (hours/day)",
    "sleep_hours": "Sleep Duration (hours/night)",
    "sleep_quality": "Sleep Quality (1-5 rating)",
    "screen_time_hours": "Screen Time (hours/day)",
    "interruption_count": "Interruptions (count/day)",
    "task_completion_rate": "Task Completion Rate (ratio)",
    "work_session_duration_hours": "Work Session Duration (hours/day)",
    "work_session_utilization": "Work Session Utilization (ratio)",
    "inactivity_duration_hours": "Inactivity Duration (hours/day)",
    "inactivity_ratio": "Inactivity Ratio (ratio)",
    "perceived_stress": "Perceived Stress (1-5 rating)",
    "mood_score": "Mood Score (1-5 rating)",
    "productivity_score": "Productivity Score (0-100 score)",
}


class DriftStatus(str, Enum):
    """Categorical classification of behavioural distribution shift."""

    NO_DRIFT = "no_drift"
    TENTATIVE_DRIFT = "tentative_drift"
    STRONG_DRIFT = "strong_drift"
    INSUFFICIENT_DATA = "insufficient_data"


class DriftDirection(str, Enum):
    """Direction of observed distribution change."""

    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"


@dataclass
class DriftDetectionConfig:
    """Configuration for per-user behavioural drift detector."""

    reference_window_days: int = 14
    comparison_window_days: int = 7
    min_reference_samples: int = 7
    min_comparison_samples: int = 4
    significance_alpha: float = 0.05
    moderate_effect_threshold: float = 0.50
    strong_effect_threshold: float = 0.80
    psi_moderate_threshold: float = 0.10
    psi_strong_threshold: float = 0.25
    features: list[str] = field(default_factory=lambda: list(DEFAULT_BEHAVIORAL_DRIFT_FEATURES))
    multiple_testing_correction: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DistributionSummary:
    """Summary statistics for a continuous or ordinal sample distribution."""

    count: int
    mean: float
    std: float
    median: float
    q25: float
    q75: float
    iqr: float
    min: float
    max: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FeatureDriftResult:
    """Detailed drift detection evaluation for a single behavioural feature."""

    feature_name: str
    status: DriftStatus
    direction: DriftDirection
    reference_summary: Optional[DistributionSummary]
    comparison_summary: Optional[DistributionSummary]
    mean_difference: float
    median_difference: float
    cohens_d: float
    wasserstein_distance: float
    psi: Optional[float]
    p_value_raw: float
    p_value_adjusted: float
    is_statistically_significant: bool
    is_practically_meaningful: bool
    rationale: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        res = asdict(self)
        res["status"] = self.status.value
        res["direction"] = self.direction.value
        return res


@dataclass
class UserDriftReport:
    """Aggregated drift detection report for a single user at an evaluation origin."""

    user_id: str
    evaluation_date: str
    reference_start_date: str
    reference_end_date: str
    comparison_start_date: str
    comparison_end_date: str
    feature_results: dict[str, FeatureDriftResult]
    overall_status: DriftStatus
    drifted_features_count: int
    strong_drift_features: list[str]
    tentative_drift_features: list[str]
    insufficient_data_features: list[str]
    summary_narrative: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "evaluation_date": self.evaluation_date,
            "reference_window": f"{self.reference_start_date} to {self.reference_end_date}",
            "comparison_window": f"{self.comparison_start_date} to {self.comparison_end_date}",
            "overall_status": self.overall_status.value,
            "drifted_features_count": self.drifted_features_count,
            "strong_drift_features": self.strong_drift_features,
            "tentative_drift_features": self.tentative_drift_features,
            "insufficient_data_features": self.insufficient_data_features,
            "summary_narrative": self.summary_narrative,
            "feature_results": {k: v.to_dict() for k, v in self.feature_results.items()},
        }


# --- Statistical Utilities ---

def benjamini_hochberg(p_values: Sequence[float]) -> list[float]:
    """Apply the Benjamini-Hochberg (BH) step-up procedure to control False Discovery Rate (FDR).

    Note: This controls False Discovery Rate (the expected proportion of false positives
    among rejected hypotheses), rather than the Family-Wise Error Rate (FWER).

    Args:
        p_values: Sequence of raw p-values from independent or positively dependent tests.

    Returns:
        List of adjusted p-values (q-values) bounded in [0.0, 1.0].
    """
    p_arr = np.asarray(p_values, dtype=float)
    m = len(p_arr)
    if m == 0:
        return []
    if m == 1:
        return [float(np.clip(p_arr[0], 0.0, 1.0))]

    # Sort p-values while preserving original indices
    order = np.argsort(p_arr)
    sorted_p = p_arr[order]

    # q_{(i)} = p_{(i)} * m / i
    ranks = np.arange(1, m + 1, dtype=float)
    q_vals = sorted_p * (m / ranks)

    # Enforce monotonicity backwards: q_{(i)} = min(q_{(i)}, q_{(i+1)})
    q_adj = np.minimum.accumulate(q_vals[::-1])[::-1]
    q_adj = np.clip(q_adj, 0.0, 1.0)

    # Reorder back to original order
    adjusted = np.empty(m, dtype=float)
    adjusted[order] = q_adj
    return [float(x) for x in adjusted]


def compute_distribution_summary(arr: np.ndarray) -> DistributionSummary:
    """Compute parametric and non-parametric summary metrics for a sample array."""
    clean = arr[~np.isnan(arr)]
    if len(clean) == 0:
        return DistributionSummary(
            count=0, mean=0.0, std=0.0, median=0.0, q25=0.0, q75=0.0, iqr=0.0, min=0.0, max=0.0
        )
    q25, med, q75 = np.percentile(clean, [25, 50, 75])
    return DistributionSummary(
        count=int(len(clean)),
        mean=float(np.mean(clean)),
        std=float(np.std(clean, ddof=1)) if len(clean) > 1 else 0.0,
        median=float(med),
        q25=float(q25),
        q75=float(q75),
        iqr=float(q75 - q25),
        min=float(np.min(clean)),
        max=float(np.max(clean)),
    )


def compute_cohens_d(ref: np.ndarray, cmp: np.ndarray) -> float:
    """Compute Cohen's d standardized mean difference between comparison and reference.

    d = (mean(cmp) - mean(ref)) / s_pooled
    Positive d indicates an increase in the comparison period; negative indicates a decrease.
    """
    r_clean = ref[~np.isnan(ref)]
    c_clean = cmp[~np.isnan(cmp)]
    n1, n2 = len(r_clean), len(c_clean)
    if n1 < 2 or n2 < 2:
        return 0.0

    mean_diff = float(np.mean(c_clean) - np.mean(r_clean))
    s1 = float(np.std(r_clean, ddof=1))
    s2 = float(np.std(c_clean, ddof=1))

    # Pooled variance
    s_pooled_sq = ((n1 - 1) * (s1 ** 2) + (n2 - 1) * (s2 ** 2)) / (n1 + n2 - 2)
    if s_pooled_sq <= 1e-12:
        return 0.0 if abs(mean_diff) < 1e-6 else float(np.sign(mean_diff) * 5.0)

    s_pooled = np.sqrt(s_pooled_sq)
    return float(np.clip(mean_diff / s_pooled, -10.0, 10.0))


def compute_population_stability_index(
    ref: np.ndarray,
    cmp: np.ndarray,
    num_bins: int = 5,
    epsilon: float = 1e-4,
) -> float:
    """Compute Population Stability Index (PSI) between reference and comparison samples.

    PSI = sum((P_cmp(b) - P_ref(b)) * ln(P_cmp(b) / P_ref(b)))
    """
    r_clean = ref[~np.isnan(ref)]
    c_clean = cmp[~np.isnan(cmp)]
    if len(r_clean) < 4 or len(c_clean) < 2:
        return 0.0

    # Define bins based on reference sample quantiles
    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(r_clean, quantiles)
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    # Handle duplicate edges if data has low cardinality (e.g. integer ratings)
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 3:
        # Fallback to uniform linspace between min and max
        min_val = min(np.min(r_clean), np.min(c_clean))
        max_val = max(np.max(r_clean), np.max(c_clean))
        if max_val - min_val < 1e-6:
            return 0.0
        bin_edges = np.linspace(min_val - 1e-4, max_val + 1e-4, num_bins + 1)

    ref_counts, _ = np.histogram(r_clean, bins=bin_edges)
    cmp_counts, _ = np.histogram(c_clean, bins=bin_edges)

    p_ref = (ref_counts + epsilon) / (np.sum(ref_counts) + epsilon * len(ref_counts))
    p_cmp = (cmp_counts + epsilon) / (np.sum(cmp_counts) + epsilon * len(cmp_counts))

    psi = np.sum((p_cmp - p_ref) * np.log(p_cmp / p_ref))
    return float(np.clip(psi, 0.0, 50.0))


# --- Detection Functions ---

def detect_feature_drift(
    ref_values: np.ndarray,
    cmp_values: np.ndarray,
    feature_name: str,
    config: DriftDetectionConfig,
    p_value_raw: Optional[float] = None,
    p_value_adjusted: Optional[float] = None,
) -> FeatureDriftResult:
    """Evaluate behavioural drift for a single numeric/ordinal feature.

    Args:
        ref_values: Observations from the historical reference window.
        cmp_values: Observations from the recent comparison window.
        feature_name: Name of the evaluated telemetry feature.
        config: Detector thresholds and parameters.
        p_value_raw: Precomputed raw p-value, or None to compute locally.
        p_value_adjusted: Precomputed FDR-adjusted p-value, or None.

    Returns:
        FeatureDriftResult with classification, effect sizes, and rationale.
    """
    ref_clean = ref_values[~np.isnan(ref_values)]
    cmp_clean = cmp_values[~np.isnan(cmp_values)]

    # Check minimum observation requirements
    if len(ref_clean) < config.min_reference_samples or len(cmp_clean) < config.min_comparison_samples:
        return FeatureDriftResult(
            feature_name=feature_name,
            status=DriftStatus.INSUFFICIENT_DATA,
            direction=DriftDirection.STABLE,
            reference_summary=compute_distribution_summary(ref_clean) if len(ref_clean) > 0 else None,
            comparison_summary=compute_distribution_summary(cmp_clean) if len(cmp_clean) > 0 else None,
            mean_difference=0.0,
            median_difference=0.0,
            cohens_d=0.0,
            wasserstein_distance=0.0,
            psi=None,
            p_value_raw=1.0,
            p_value_adjusted=1.0,
            is_statistically_significant=False,
            is_practically_meaningful=False,
            rationale=(
                f"Insufficient non-null observations (Reference: {len(ref_clean)}/{config.min_reference_samples}, "
                f"Comparison: {len(cmp_clean)}/{config.min_comparison_samples})."
            ),
            notes=["Window sample size below configured minimum thresholds."],
        )

    ref_sum = compute_distribution_summary(ref_clean)
    cmp_sum = compute_distribution_summary(cmp_clean)
    mean_diff = float(cmp_sum.mean - ref_sum.mean)
    med_diff = float(cmp_sum.median - ref_sum.median)

    # Standardized and non-parametric effect sizes
    cohens_d = compute_cohens_d(ref_clean, cmp_clean)
    w_dist = float(wasserstein_distance(ref_clean, cmp_clean))
    psi = compute_population_stability_index(ref_clean, cmp_clean)

    # Two-sample Mann-Whitney U test (non-parametric)
    if p_value_raw is None:
        try:
            # If all values are identical across both samples, p-value is 1.0
            if np.array_equal(ref_clean, cmp_clean) or (np.var(ref_clean) == 0 and np.var(cmp_clean) == 0 and ref_clean[0] == cmp_clean[0]):
                p_raw = 1.0
            else:
                stat, p_val = mannwhitneyu(cmp_clean, ref_clean, alternative="two-sided")
                p_raw = float(p_val)
        except Exception:
            p_raw = 1.0
    else:
        p_raw = p_value_raw

    p_adj = p_value_adjusted if p_value_adjusted is not None else p_raw

    # Direction determination
    if abs(mean_diff) < 1e-4 and abs(med_diff) < 1e-4:
        direction = DriftDirection.STABLE
    elif mean_diff > 0:
        direction = DriftDirection.INCREASE
    else:
        direction = DriftDirection.DECREASE

    # Decision policy
    is_sig_adj = p_adj < config.significance_alpha
    is_sig_raw = p_raw < config.significance_alpha
    is_sig = is_sig_adj or is_sig_raw
    abs_d = abs(cohens_d)
    is_large_effect = abs_d >= config.strong_effect_threshold
    is_moderate_effect = abs_d >= config.moderate_effect_threshold

    if (is_sig_adj and is_moderate_effect) or (is_sig_raw and is_large_effect):
        status = DriftStatus.STRONG_DRIFT
        rationale = (
            f"Strong drift detected: statistically significant shift (p_raw = {p_raw:.4f}, p_adj = {p_adj:.4f}) "
            f"with substantial standardized effect size (Cohen's d = {cohens_d:+.2f}, |d| >= {config.moderate_effect_threshold})."
        )
    elif is_sig_adj or is_sig_raw or is_large_effect or is_moderate_effect:
        status = DriftStatus.TENTATIVE_DRIFT
        rationale = (
            f"Tentative drift detected: notable distributional change (Cohen's d = {cohens_d:+.2f}, "
            f"p_raw = {p_raw:.4f}, p_adj = {p_adj:.4f}) warrants continued longitudinal observation."
        )
    else:
        status = DriftStatus.NO_DRIFT
        rationale = (
            f"No drift detected: distribution metrics are stable within expected statistical variance "
            f"(p_adj = {p_adj:.4f}, Cohen's d = {cohens_d:+.2f})."
        )

    label = FEATURE_METRIC_LABELS.get(feature_name, feature_name)
    notes = [
        f"Feature: {label}",
        f"Reference (N={len(ref_clean)}): Mean={ref_sum.mean:.2f}, Median={ref_sum.median:.2f}, Std={ref_sum.std:.2f}",
        f"Comparison (N={len(cmp_clean)}): Mean={cmp_sum.mean:.2f}, Median={cmp_sum.median:.2f}, Std={cmp_sum.std:.2f}",
        f"Shift: Delta={mean_diff:+.2f}, Cohen's d={cohens_d:+.2f}, Wasserstein={w_dist:.2f}, PSI={psi:.3f}",
    ]

    return FeatureDriftResult(
        feature_name=feature_name,
        status=status,
        direction=direction,
        reference_summary=ref_sum,
        comparison_summary=cmp_sum,
        mean_difference=round(mean_diff, 4),
        median_difference=round(med_diff, 4),
        cohens_d=round(cohens_d, 4),
        wasserstein_distance=round(w_dist, 4),
        psi=round(psi, 4),
        p_value_raw=round(p_raw, 5),
        p_value_adjusted=round(p_adj, 5),
        is_statistically_significant=is_sig,
        is_practically_meaningful=is_moderate_effect or is_large_effect,
        rationale=rationale,
        notes=notes,
    )


def detect_user_drift(
    user_df: pd.DataFrame,
    evaluation_date: str,
    config: DriftDetectionConfig,
) -> UserDriftReport:
    """Evaluate multi-feature behavioural drift for a single user at a forecast origin.

    Ensures chronological ordering, strict past-only historical reference, zero future leakage,
    and Benjamini-Hochberg FDR correction across the monitored feature set.

    Args:
        user_df: DataFrame of records for a single user, containing 'record_date'.
        evaluation_date: Forecast/monitoring origin day t ('YYYY-MM-DD').
        config: Detector configuration specifying reference and comparison lengths.

    Returns:
        UserDriftReport containing individual feature results and overall user status.
    """
    if "record_date" not in user_df.columns:
        raise ValueError("DataFrame must contain 'record_date' column.")

    df = user_df.copy()
    df["_date_parsed"] = pd.to_datetime(df["record_date"]).dt.strftime("%Y-%m-%d")
    df = df.sort_values("_date_parsed")

    user_ids = df["user_id"].unique() if "user_id" in df.columns else ["unknown_user"]
    user_id = str(user_ids[0])

    eval_dt = pd.to_datetime(evaluation_date)
    cmp_days = config.comparison_window_days
    ref_days = config.reference_window_days

    # Comparison window: [eval_date - cmp_days + 1, eval_date]
    cmp_start_dt = eval_dt - pd.Timedelta(days=cmp_days - 1)
    cmp_end_dt = eval_dt

    # Reference window: [cmp_start_dt - ref_days, cmp_start_dt - 1 day]
    ref_end_dt = cmp_start_dt - pd.Timedelta(days=1)
    ref_start_dt = ref_end_dt - pd.Timedelta(days=ref_days - 1)

    ref_start_str = ref_start_dt.strftime("%Y-%m-%d")
    ref_end_str = ref_end_dt.strftime("%Y-%m-%d")
    cmp_start_str = cmp_start_dt.strftime("%Y-%m-%d")
    cmp_end_str = cmp_end_dt.strftime("%Y-%m-%d")

    # Strict isolation: filter data strictly within windows (no future data past eval_dt)
    ref_slice = df[(df["_date_parsed"] >= ref_start_str) & (df["_date_parsed"] <= ref_end_str)]
    cmp_slice = df[(df["_date_parsed"] >= cmp_start_str) & (df["_date_parsed"] <= cmp_end_str)]

    # First pass: compute raw Mann-Whitney U p-values for all candidate features
    raw_p_values: list[float] = []
    feature_names: list[str] = []
    feature_arrays: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    for feat in config.features:
        if feat not in df.columns:
            continue
        feature_names.append(feat)
        ref_arr = ref_slice[feat].dropna().to_numpy(dtype=float)
        cmp_arr = cmp_slice[feat].dropna().to_numpy(dtype=float)
        feature_arrays[feat] = (ref_arr, cmp_arr)

        if len(ref_arr) >= config.min_reference_samples and len(cmp_arr) >= config.min_comparison_samples:
            if np.array_equal(ref_arr, cmp_arr) or (np.var(ref_arr) == 0 and np.var(cmp_arr) == 0 and ref_arr[0] == cmp_arr[0]):
                p_val = 1.0
            else:
                try:
                    _, p = mannwhitneyu(cmp_arr, ref_arr, alternative="two-sided")
                    p_val = float(p)
                except Exception:
                    p_val = 1.0
        else:
            p_val = 1.0
        raw_p_values.append(p_val)

    # Multiple-testing correction across monitored features
    if config.multiple_testing_correction and len(raw_p_values) > 0:
        adjusted_p_values = benjamini_hochberg(raw_p_values)
    else:
        adjusted_p_values = raw_p_values

    # Second pass: compute comprehensive feature drift results
    feature_results: dict[str, FeatureDriftResult] = {}
    strong_drift_feats: list[str] = []
    tentative_drift_feats: list[str] = []
    insufficient_feats: list[str] = []

    for idx, feat in enumerate(feature_names):
        ref_arr, cmp_arr = feature_arrays[feat]
        res = detect_feature_drift(
            ref_values=ref_arr,
            cmp_values=cmp_arr,
            feature_name=feat,
            config=config,
            p_value_raw=raw_p_values[idx],
            p_value_adjusted=adjusted_p_values[idx],
        )
        feature_results[feat] = res
        if res.status == DriftStatus.STRONG_DRIFT:
            strong_drift_feats.append(feat)
        elif res.status == DriftStatus.TENTATIVE_DRIFT:
            tentative_drift_feats.append(feat)
        elif res.status == DriftStatus.INSUFFICIENT_DATA:
            insufficient_feats.append(feat)

    # Determine overall user drift status
    total_valid = len(feature_names) - len(insufficient_feats)
    if total_valid < max(1, len(feature_names) // 2):
        overall_status = DriftStatus.INSUFFICIENT_DATA
        narrative = "Insufficient historical observations available to establish robust multi-feature behavioural baseline."
    elif len(strong_drift_feats) > 0:
        overall_status = DriftStatus.STRONG_DRIFT
        narrative = (
            f"Strong behavioural drift observed in {len(strong_drift_feats)} feature(s): "
            f"{', '.join(strong_drift_feats)}. Statistical evidence indicates a significant distribution change "
            f"relative to the {config.reference_window_days}-day reference period."
        )
    elif len(tentative_drift_feats) > 0:
        overall_status = DriftStatus.TENTATIVE_DRIFT
        narrative = (
            f"Tentative behavioural drift observed in {len(tentative_drift_feats)} feature(s): "
            f"{', '.join(tentative_drift_feats)}. Distribution shift warrants continued observation."
        )
    else:
        overall_status = DriftStatus.NO_DRIFT
        narrative = (
            f"No behavioural drift detected across {len(feature_names)} monitored features. "
            f"Recent comparison window aligns with the reference distribution within expected statistical variance."
        )

    return UserDriftReport(
        user_id=user_id,
        evaluation_date=evaluation_date,
        reference_start_date=ref_start_str,
        reference_end_date=ref_end_str,
        comparison_start_date=cmp_start_str,
        comparison_end_date=cmp_end_str,
        feature_results=feature_results,
        overall_status=overall_status,
        drifted_features_count=len(strong_drift_feats) + len(tentative_drift_feats),
        strong_drift_features=strong_drift_feats,
        tentative_drift_features=tentative_drift_feats,
        insufficient_data_features=insufficient_feats,
        summary_narrative=narrative,
    )


def detect_cohort_drift(
    df: pd.DataFrame,
    evaluation_date: str,
    config: DriftDetectionConfig,
) -> dict[str, UserDriftReport]:
    """Execute drift detection across all users in a behavioural cohort at a single evaluation origin.

    Args:
        df: Cohort DataFrame containing 'user_id' and 'record_date'.
        evaluation_date: Date to evaluate ('YYYY-MM-DD').
        config: Drift detector configuration.

    Returns:
        Dictionary mapping user_id to UserDriftReport.
    """
    reports: dict[str, UserDriftReport] = {}
    grouped = df.groupby("user_id")

    for user_id, user_group in grouped:
        report = detect_user_drift(
            user_df=user_group,
            evaluation_date=evaluation_date,
            config=config,
        )
        reports[str(user_id)] = report

    return reports


# --- Controlled Experiment Utilities ---

def generate_recovery_scenario_data(
    n_users: int = 50,
    n_days: int = 90,
    start_date: str = "2026-01-01",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate controlled three-phase recovery data: Baseline -> Shift -> Return-to-Baseline.

    - Phase 1 (Days 1–56, 8 weeks): Stable baseline.
    - Phase 2 (Days 57–70, 2 weeks): Injected focus reduction (-1.5h) and stress elevation (+1.2).
    - Phase 3 (Days 71–90, ~3 weeks): Recovery return to original baseline distribution.

    Implemented as an isolated experiment utility without modifying the production generator.
    """
    df = generate_synthetic_data(
        n_users=n_users,
        n_days=n_days,
        start_date=start_date,
        seed=seed,
        scenario="baseline",
    )

    dates = sorted(df["record_date"].unique())
    shift_start_idx = int(0.60 * len(dates))
    shift_end_idx = int(0.75 * len(dates))
    shift_dates = set(dates[shift_start_idx:shift_end_idx])

    rng = np.random.default_rng(seed + 100)
    out = df.copy()

    # Apply temporary perturbation during Phase 2 only
    in_shift = out["record_date"].isin(shift_dates)

    out.loc[in_shift, "focus_duration_hours"] = np.clip(
        out.loc[in_shift, "focus_duration_hours"] - 1.5 + rng.normal(0, 0.2, size=int(in_shift.sum())),
        0.0,
        12.0,
    )

    out.loc[in_shift, "screen_time_hours"] = np.clip(
        out.loc[in_shift, "screen_time_hours"] + 1.2,
        0.0,
        16.0,
    )

    if "perceived_stress" in out.columns:
        stress_series = out.loc[in_shift, "perceived_stress"].fillna(3)
        out.loc[in_shift, "perceived_stress"] = np.clip(
            np.rint(stress_series + 1.2),
            1,
            5,
        )

    # Recompute engineered features for the perturbed dataset
    out = engineer_features(out, include_target_derived=False)
    return out


# --- Publication Diagnostic Plotting ---

def plot_reference_vs_monitoring_distributions(
    user_report: UserDriftReport,
    user_df: pd.DataFrame,
    features_to_plot: list[str],
    output_path: Path,
) -> None:
    """Generate comparative KDE and boxplot diagnostic distributions for selected features."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = user_df.copy()
    df["_date"] = pd.to_datetime(df["record_date"]).dt.strftime("%Y-%m-%d")

    ref_df = df[(df["_date"] >= user_report.reference_start_date) & (df["_date"] <= user_report.reference_end_date)]
    cmp_df = df[(df["_date"] >= user_report.comparison_start_date) & (df["_date"] <= user_report.comparison_end_date)]

    n_feats = len(features_to_plot)
    fig, axes = plt.subplots(n_feats, 2, figsize=(12, 3.5 * n_feats))
    if n_feats == 1:
        axes = np.expand_dims(axes, 0)

    for i, feat in enumerate(features_to_plot):
        ref_vals = ref_df[feat].dropna().to_numpy()
        cmp_vals = cmp_df[feat].dropna().to_numpy()
        label = FEATURE_METRIC_LABELS.get(feat, feat)
        res = user_report.feature_results.get(feat)
        d_val = res.cohens_d if res else 0.0
        p_val = res.p_value_adjusted if res else 1.0

        # Subplot 1: Boxplots
        ax_box = axes[i, 0]
        ax_box.boxplot(
            [ref_vals, cmp_vals],
            tick_labels=[f"Reference\n({user_report.reference_start_date[-5:]} to {user_report.reference_end_date[-5:]})",
                         f"Comparison\n({user_report.comparison_start_date[-5:]} to {user_report.comparison_end_date[-5:]})"],
            patch_artist=True,
            boxprops=dict(facecolor="#e2e8f0", color="#334155"),
            medianprops=dict(color="#0284c7", linewidth=2),
        )
        ax_box.set_title(f"{label} — Distribution Comparison", fontsize=11, fontweight="bold")
        ax_box.set_ylabel(label)
        ax_box.grid(axis="y", linestyle="--", alpha=0.5)

        # Subplot 2: Histograms / KDE
        ax_hist = axes[i, 1]
        bins = np.linspace(
            min(np.min(ref_vals), np.min(cmp_vals)) if len(ref_vals) and len(cmp_vals) else 0,
            max(np.max(ref_vals), np.max(cmp_vals)) if len(ref_vals) and len(cmp_vals) else 10,
            12,
        )
        ax_hist.hist(ref_vals, bins=bins, alpha=0.5, color="#64748b", label=f"Ref (Mean={np.mean(ref_vals):.2f})", density=True)
        ax_hist.hist(cmp_vals, bins=bins, alpha=0.6, color="#0284c7", label=f"Cmp (Mean={np.mean(cmp_vals):.2f})", density=True)
        ax_hist.set_title(f"Cohen's d = {d_val:+.2f} | p_adj = {p_val:.4f}", fontsize=11)
        ax_hist.set_xlabel(label)
        ax_hist.set_ylabel("Density")
        ax_hist.legend(loc="upper right", fontsize=9)
        ax_hist.grid(axis="y", linestyle="--", alpha=0.5)

    plt.suptitle(f"User {user_report.user_id} — Behavioural Drift Diagnostic Inspection ({user_report.evaluation_date})", fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_drift_timeline(
    timeline_records: list[dict[str, Any]],
    feature_name: str,
    output_path: Path,
) -> None:
    """Plot longitudinal timeline of effect size and drift alerts across evaluation dates."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(timeline_records).sort_values("evaluation_date")

    dates = df["evaluation_date"].to_list()
    effect_sizes = df["cohens_d"].to_list()
    p_adj_vals = df["p_value_adjusted"].to_list()
    statuses = df["status"].to_list()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    # Panel 1: Standardized Effect Size (Cohen's d)
    colors = ["#dc2626" if s == "strong_drift" else ("#f59e0b" if s == "tentative_drift" else "#10b981") for s in statuses]
    ax1.plot(dates, effect_sizes, color="#334155", marker="o", linewidth=1.5, zorder=2)
    ax1.scatter(dates, effect_sizes, c=colors, s=70, zorder=3, edgecolors="#1e293b")
    ax1.axhline(0.0, color="#94a3b8", linestyle="-", linewidth=1)
    ax1.axhline(0.80, color="#dc2626", linestyle="--", linewidth=1, label="Strong Drift (|d| >= 0.8)")
    ax1.axhline(-0.80, color="#dc2626", linestyle="--", linewidth=1)
    ax1.axhline(0.50, color="#f59e0b", linestyle=":", linewidth=1, label="Moderate Drift (|d| >= 0.5)")
    ax1.axhline(-0.50, color="#f59e0b", linestyle=":", linewidth=1)

    label = FEATURE_METRIC_LABELS.get(feature_name, feature_name)
    ax1.set_ylabel("Cohen's d (Effect Size)", fontsize=11, fontweight="bold")
    ax1.set_title(f"Longitudinal Drift Timeline: {label}", fontsize=13, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Panel 2: Adjusted p-values
    ax2.plot(dates, p_adj_vals, color="#0284c7", marker="s", linewidth=1.5)
    ax2.axhline(0.05, color="#dc2626", linestyle="--", linewidth=1, label="FDR Alpha = 0.05")
    ax2.set_ylabel("Adjusted p-value (BH)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Evaluation Date (Forecast Origin t)", fontsize=11, fontweight="bold")
    ax2.set_ylim(-0.02, 1.05)
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.5)

    # Format x-axis tick frequency
    step = max(1, len(dates) // 10)
    ax2.set_xticks(range(0, len(dates), step))
    ax2.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_scenario_performance_summary(
    scenario_metrics: dict[str, dict[str, Any]],
    output_path: Path,
) -> None:
    """Plot detection rates and false alarm metrics across controlled perturbation scenarios."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scenarios = list(scenario_metrics.keys())
    clean_labels = [s.replace("_", " ").title() for s in scenarios]

    tpr_vals = [scenario_metrics[s].get("target_feature_detection_rate", 0.0) * 100 for s in scenarios]
    fpr_vals = [scenario_metrics[s].get("false_alarm_rate", 0.0) * 100 for s in scenarios]

    x = np.arange(len(scenarios))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    rects1 = ax.bar(x - width/2, tpr_vals, width, label="Target Feature Detection Rate (Sensitivity %)", color="#0284c7")
    rects2 = ax.bar(x + width/2, fpr_vals, width, label="False Alarm Rate (Stable Features %)", color="#f43f5e")

    ax.set_ylabel("Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Behavioural Drift Detector — Controlled Experiment Performance", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(clean_labels, fontsize=11)
    ax.set_ylim(0, 110)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"{height:.1f}%",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9, fontweight="bold")

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()
