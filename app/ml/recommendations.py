"""Evidence-based behavioural recommendation engine with non-clinical guardrails.

Synthesizes daily telemetry, longitudinal behavioural drift detection,
and unsupervised clustering patterns into deterministic, actionable,
and prioritized behavioural recommendations.

Strict Responsible AI Guardrails:
- Recommendations are exploratory suggestions, never clinical diagnoses or treatments.
- No claims that a suggested action will 'definitely' improve productivity.
- Neutral, non-judgmental language throughout.
- Explainable, deterministic priority scoring.
- Cautious handling of missing or insufficient telemetry.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from typing import Any, Optional, Sequence
import numpy as np
import pandas as pd

from app.ml.drift import DriftDirection, DriftStatus, UserDriftReport


class RecommendationCategory(str, Enum):
    """Categorical classification of behavioural suggestions."""

    INTERRUPTION_MANAGEMENT = "interruption_management"
    SESSION_PACING = "session_pacing"
    FOCUS_OPTIMIZATION = "focus_optimization"
    SLEEP_RECOVERY = "sleep_recovery"
    STRESS_PACING = "stress_pacing"
    TASK_CALIBRATION = "task_calibration"
    DATA_COLLECTION = "data_collection"


class ConfidenceLevel(str, Enum):
    """Subjective evidence confidence based on sample completeness and effect strength."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass
class RecommendationItem:
    """An individual, explainable behavioural recommendation."""

    recommendation_id: str
    title: str
    category: RecommendationCategory
    explanation: str
    observed_evidence: dict[str, Any]
    proposed_action: str
    rationale: str
    expected_direction: str
    confidence: ConfidenceLevel
    priority_score: float  # Bounded in [0.0, 1.0]
    limitations: str
    disclaimer: str = (
        "This suggestion is an exploratory heuristic derived from synthetic telemetry patterns. "
        "It is optional and does not constitute a clinical, psychological, or medical recommendation."
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert recommendation to a clean serializable dictionary."""
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "category": self.category.value,
            "explanation": self.explanation,
            "observed_evidence": self.observed_evidence,
            "proposed_action": self.proposed_action,
            "rationale": self.rationale,
            "expected_direction": self.expected_direction,
            "confidence": self.confidence.value,
            "priority_score": round(self.priority_score, 4),
            "limitations": self.limitations,
            "disclaimer": self.disclaimer,
        }


@dataclass
class RecommendationReport:
    """Complete per-user recommendation report with metadata and audit trace."""

    user_id: str
    evaluation_date: str
    recommendations: list[RecommendationItem] = field(default_factory=list)
    audit_summary: dict[str, Any] = field(default_factory=dict)
    insufficient_data: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "evaluation_date": self.evaluation_date,
            "recommendation_count": len(self.recommendations),
            "insufficient_data": self.insufficient_data,
            "audit_summary": self.audit_summary,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


def compute_priority_score(
    magnitude_norm: float,
    evidence_quality: float,
    data_completeness: float,
    persistence: float = 1.0,
    weights: Optional[tuple[float, float, float, float]] = None,
) -> float:
    """Compute an explainable, deterministic priority score bounded in [0.0, 1.0].

    Formula:
        Score = w_1 * Magnitude + w_2 * EvidenceQuality + w_3 * Completeness + w_4 * Persistence

    Default weights:
        w_1 (Magnitude) = 0.35
        w_2 (Evidence Quality) = 0.30
        w_3 (Data Completeness) = 0.20
        w_4 (Persistence) = 0.15

    Args:
        magnitude_norm: Normalized shift or extremity magnitude [0.0, 1.0].
        evidence_quality: Statistical significance or metric reliability [0.0, 1.0].
        data_completeness: Fraction of valid, non-null observations [0.0, 1.0].
        persistence: Longitudinal duration or recurrence weight [0.0, 1.0].
        weights: Optional custom 4-tuple of weights summing to 1.0.

    Returns:
        Priority score strictly clamped to [0.0, 1.0].
    """
    if weights is None:
        w1, w2, w3, w4 = 0.35, 0.30, 0.20, 0.15
    else:
        w1, w2, w3, w4 = weights
        total_w = w1 + w2 + w3 + w4
        if total_w > 0:
            w1, w2, w3, w4 = w1 / total_w, w2 / total_w, w3 / total_w, w4 / total_w

    raw_score = (
        w1 * np.clip(magnitude_norm, 0.0, 1.0)
        + w2 * np.clip(evidence_quality, 0.0, 1.0)
        + w3 * np.clip(data_completeness, 0.0, 1.0)
        + w4 * np.clip(persistence, 0.0, 1.0)
    )
    return round(float(np.clip(raw_score, 0.0, 1.0)), 6)


def generate_recommendations(
    user_telemetry_df: pd.DataFrame,
    evaluation_date: str,
    user_drift_report: Optional[UserDriftReport] = None,
    cluster_profile: Optional[dict[str, Any]] = None,
    min_monitoring_days: int = 4,
    monitoring_window_days: int = 7,
) -> RecommendationReport:
    """Generate deterministic, evidence-based recommendations for a single user.

    Examines recent telemetry window up to `evaluation_date`, checks against
    validated rule triggers, incorporates drift alerts if provided, and
    ranks suggestions using an explainable priority formula.

    Args:
        user_telemetry_df: Historical daily records for a single user.
        evaluation_date: Date string (YYYY-MM-DD) defining the end of monitoring.
        user_drift_report: Optional validated drift detection output for this user.
        cluster_profile: Optional clustering metadata or cluster assignment.
        min_monitoring_days: Minimum valid records required for confident suggestions.
        monitoring_window_days: Days lookback for monitoring window (default 7).

    Returns:
        RecommendationReport with sorted, deduplicated recommendation items.
    """
    if user_telemetry_df.empty:
        return RecommendationReport(
            user_id="unknown",
            evaluation_date=evaluation_date,
            insufficient_data=True,
            audit_summary={"reason": "Empty telemetry DataFrame provided."},
        )

    # Ensure date column is string formatted
    df = user_telemetry_df.copy()
    user_id = str(df["user_id"].iloc[0]) if "user_id" in df.columns else "unknown"

    df["record_date_str"] = pd.to_datetime(df["record_date"]).dt.strftime("%Y-%m-%d")
    eval_dt = pd.to_datetime(evaluation_date)
    start_dt = eval_dt - pd.Timedelta(days=monitoring_window_days - 1)
    start_dt_str = start_dt.strftime("%Y-%m-%d")

    # Slice monitoring window strictly causally: [start_dt, eval_dt]
    monitoring_mask = (df["record_date_str"] >= start_dt_str) & (df["record_date_str"] <= evaluation_date)
    mon_df = df[monitoring_mask].sort_values("record_date_str")

    n_obs = len(mon_df)
    completeness = min(1.0, n_obs / monitoring_window_days)

    audit: dict[str, Any] = {
        "monitoring_window": [start_dt_str, evaluation_date],
        "observations_count": n_obs,
        "completeness_ratio": round(completeness, 4),
        "rules_evaluated": [],
        "rules_triggered": [],
    }

    # 1. Check for Insufficient Telemetry
    if n_obs < min_monitoring_days:
        audit["rules_evaluated"].append("REC-DAT-001")
        audit["rules_triggered"].append("REC-DAT-001")
        rec_data = RecommendationItem(
            recommendation_id="REC-DAT-001",
            title="Maintain Consistent Behavioural Logging",
            category=RecommendationCategory.DATA_COLLECTION,
            explanation=(
                f"Only {n_obs} observation(s) were recorded in the recent {monitoring_window_days}-day monitoring window. "
                f"A minimum of {min_monitoring_days} active days is required to establish reliable behavioural patterns."
            ),
            observed_evidence={
                "recorded_days": n_obs,
                "required_days": min_monitoring_days,
                "window_days": monitoring_window_days,
            },
            proposed_action=(
                "Continue logging daily activity and sleep metrics consistently over the next 5–7 days before drawing conclusions."
            ),
            rationale="Statistical confidence in personal baseline distributions depends on sufficient sample size.",
            expected_direction="Improved measurement stability and reliable pattern detection.",
            confidence=ConfidenceLevel.LOW,
            priority_score=compute_priority_score(
                magnitude_norm=1.0 - completeness,
                evidence_quality=0.40,
                data_completeness=completeness,
            ),
            limitations=f"Telemetry coverage ({n_obs}/{monitoring_window_days} days) is below confidence threshold.",
        )
        return RecommendationReport(
            user_id=user_id,
            evaluation_date=evaluation_date,
            recommendations=[rec_data],
            audit_summary=audit,
            insufficient_data=True,
        )

    # Compute summary statistics over the monitoring window
    mean_focus = float(mon_df["focus_duration_hours"].mean()) if "focus_duration_hours" in mon_df else 0.0
    mean_screen = float(mon_df["screen_time_hours"].mean()) if "screen_time_hours" in mon_df else 0.0
    mean_interruptions = float(mon_df["interruption_count"].mean()) if "interruption_count" in mon_df else 0.0
    mean_work_session = float(mon_df["work_session_duration_hours"].mean()) if "work_session_duration_hours" in mon_df else 0.0
    mean_sleep = float(mon_df["sleep_hours"].mean()) if "sleep_hours" in mon_df else 0.0
    mean_stress = float(mon_df["perceived_stress"].dropna().mean()) if "perceived_stress" in mon_df and mon_df["perceived_stress"].notna().any() else None

    # Work session utilization
    utilization_series = mon_df["focus_duration_hours"] / mon_df["work_session_duration_hours"].replace(0, np.nan)
    mean_utilization = float(utilization_series.mean()) if not utilization_series.isna().all() else 0.80

    # Task completion
    task_planned_sum = float(mon_df["tasks_planned"].sum()) if "tasks_planned" in mon_df else 0.0
    task_comp_sum = float(mon_df["tasks_completed"].sum()) if "tasks_completed" in mon_df else 0.0
    completion_rate = (task_comp_sum / task_planned_sum) if task_planned_sum > 0 else 1.0

    # Drift signals helper
    drift_features = user_drift_report.feature_results if user_drift_report else {}

    candidates: list[RecommendationItem] = []

    # -------------------------------------------------------------------------
    # RULE 1: Interruption Management (REC-INT-001)
    # -------------------------------------------------------------------------
    audit["rules_evaluated"].append("REC-INT-001")
    int_drift = drift_features.get("interruption_count")
    has_int_drift = int_drift is not None and int_drift.status == DriftStatus.STRONG_DRIFT and int_drift.direction == DriftDirection.INCREASE
    is_high_interruptions = mean_interruptions >= 6.0

    if has_int_drift or is_high_interruptions:
        audit["rules_triggered"].append("REC-INT-001")
        effect_d = int_drift.cohens_d if int_drift else (mean_interruptions - 4.0) / 2.0
        mag = min(1.0, max(0.2, abs(effect_d) / 2.5))
        ev_quality = 0.85 if has_int_drift else 0.65

        candidates.append(
            RecommendationItem(
                recommendation_id="REC-INT-001",
                title="Review Work-Session Interruption Patterns",
                category=RecommendationCategory.INTERRUPTION_MANAGEMENT,
                explanation=(
                    f"Average daily interruptions reached {mean_interruptions:.1f} per day in the recent 7-day window"
                    + (f", with significant upward drift (Cohen's d = {effect_d:+.2f})." if has_int_drift else ".")
                ),
                observed_evidence={
                    "mean_interruption_count": round(mean_interruptions, 2),
                    "drift_detected": has_int_drift,
                    "cohens_d": round(effect_d, 2) if int_drift else None,
                },
                proposed_action=(
                    "Observe notification sources and consider grouping routine communications into designated 15-minute check-in windows."
                ),
                rationale="Frequent context switches fragment sustained attention and increase session restart overhead.",
                expected_direction="Reduced frequency of task interruptions during core work sessions.",
                confidence=ConfidenceLevel.HIGH if has_int_drift else ConfidenceLevel.MODERATE,
                priority_score=compute_priority_score(mag, ev_quality, completeness),
                limitations="Interruption counts reflect device events and may not capture deliberate collaborative interactions.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE 2: Work Session Pacing / Low Utilization (REC-SES-001)
    # -------------------------------------------------------------------------
    audit["rules_evaluated"].append("REC-SES-001")
    is_long_session_low_util = (mean_work_session >= 3.5) and (mean_utilization < 0.65)
    ses_drift = drift_features.get("work_session_utilization")
    has_util_drop = ses_drift is not None and ses_drift.status == DriftStatus.STRONG_DRIFT and ses_drift.direction == DriftDirection.DECREASE

    if is_long_session_low_util or has_util_drop:
        audit["rules_triggered"].append("REC-SES-001")
        mag = min(1.0, max(0.2, (0.75 - mean_utilization) / 0.35))
        ev_quality = 0.85 if has_util_drop else 0.60

        candidates.append(
            RecommendationItem(
                recommendation_id="REC-SES-001",
                title="Experiment with Shorter, Structured Work Blocks",
                category=RecommendationCategory.SESSION_PACING,
                explanation=(
                    f"Work session utilization averaged {mean_utilization:.0%} across {mean_work_session:.1f}-hour daily sessions, "
                    f"indicating substantial inactive or non-focus duration during scheduled work."
                ),
                observed_evidence={
                    "mean_session_duration_hours": round(mean_work_session, 2),
                    "mean_session_utilization": round(mean_utilization, 2),
                    "utilization_drift": has_util_drop,
                },
                proposed_action=(
                    "Experiment with breaking extended sessions into 45- to 60-minute focused intervals separated by brief off-screen pauses."
                ),
                rationale="Shorter planned focus intervals often maintain higher engagement density than continuous open-ended sessions.",
                expected_direction="Higher focus utilization percentage during active session blocks.",
                confidence=ConfidenceLevel.HIGH if has_util_drop else ConfidenceLevel.MODERATE,
                priority_score=compute_priority_score(mag, ev_quality, completeness),
                limitations="Session utilization does not differentiate passive reading or research from idle inactivity.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE 3: Focus Duration Reduction (REC-FOC-001)
    # -------------------------------------------------------------------------
    audit["rules_evaluated"].append("REC-FOC-001")
    foc_drift = drift_features.get("focus_duration_hours")
    has_foc_drop = foc_drift is not None and foc_drift.status == DriftStatus.STRONG_DRIFT and foc_drift.direction == DriftDirection.DECREASE
    is_very_low_focus = mean_focus < 2.0 and task_planned_sum > 0

    if has_foc_drop or is_very_low_focus:
        audit["rules_triggered"].append("REC-FOC-001")
        effect_d = foc_drift.cohens_d if foc_drift else (mean_focus - 4.0) / 1.5
        mag = min(1.0, max(0.3, abs(effect_d) / 2.5))
        ev_quality = 0.90 if has_foc_drop else 0.60

        candidates.append(
            RecommendationItem(
                recommendation_id="REC-FOC-001",
                title="Review Daily Focus Window Alignment",
                category=RecommendationCategory.FOCUS_OPTIMIZATION,
                explanation=(
                    f"Daily focus duration averaged {mean_focus:.1f} hours"
                    + (f", with significant downward drift (Cohen's d = {effect_d:+.2f})." if has_foc_drop else ".")
                ),
                observed_evidence={
                    "mean_focus_duration_hours": round(mean_focus, 2),
                    "drift_detected": has_foc_drop,
                    "cohens_d": round(effect_d, 2) if foc_drift else None,
                },
                proposed_action=(
                    "Review whether cognitive tasks coincide with your typical peak energy hours, and safeguard a single 60-minute distraction-free window daily."
                ),
                rationale="Securing one protected focus block provides a reliable foundation when overall focus hours fluctuate.",
                expected_direction="Stabilization of daily sustained focus time.",
                confidence=ConfidenceLevel.HIGH if has_foc_drop else ConfidenceLevel.MODERATE,
                priority_score=compute_priority_score(mag, ev_quality, completeness),
                limitations="Focus tracking captures keyboard/application telemetry and may exclude offline reading or ideation.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE 4: Sleep Recovery Inconsistency (REC-SLP-001)
    # -------------------------------------------------------------------------
    audit["rules_evaluated"].append("REC-SLP-001")
    slp_drift = drift_features.get("sleep_hours")
    has_slp_drop = slp_drift is not None and slp_drift.status == DriftStatus.STRONG_DRIFT and slp_drift.direction == DriftDirection.DECREASE
    is_low_sleep = mean_sleep < 6.0

    if has_slp_drop or is_low_sleep:
        audit["rules_triggered"].append("REC-SLP-001")
        effect_d = slp_drift.cohens_d if slp_drift else (mean_sleep - 7.5) / 1.5
        mag = min(1.0, max(0.2, abs(effect_d) / 2.0))
        ev_quality = 0.85 if has_slp_drop else 0.65

        candidates.append(
            RecommendationItem(
                recommendation_id="REC-SLP-001",
                title="Observe Sleep Timing and Morning Focus Alignment",
                category=RecommendationCategory.SLEEP_RECOVERY,
                explanation=(
                    f"Recorded sleep averaged {mean_sleep:.1f} hours/night in the recent window"
                    + (f", showing downward drift (Cohen's d = {effect_d:+.2f})." if has_slp_drop else ".")
                ),
                observed_evidence={
                    "mean_sleep_hours": round(mean_sleep, 2),
                    "drift_detected": has_slp_drop,
                    "cohens_d": round(effect_d, 2) if slp_drift else None,
                },
                proposed_action=(
                    "Track whether moving bedtime 30 minutes earlier corresponds with more consistent morning work engagement."
                ),
                rationale="Restful recovery supports cognitive stamina and reduces susceptibility to midday distractions.",
                expected_direction="More consistent day-to-day focus stability.",
                confidence=ConfidenceLevel.HIGH if has_slp_drop else ConfidenceLevel.MODERATE,
                priority_score=compute_priority_score(mag, ev_quality, completeness),
                limitations="Sleep duration is self-reported or device-estimated; sleep architecture is not measured.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE 5: Perceived Stress Elevation (REC-STR-001)
    # -------------------------------------------------------------------------
    audit["rules_evaluated"].append("REC-STR-001")
    str_drift = drift_features.get("perceived_stress")
    has_str_rise = str_drift is not None and str_drift.status == DriftStatus.STRONG_DRIFT and str_drift.direction == DriftDirection.INCREASE
    is_high_stress = (mean_stress is not None) and (mean_stress >= 3.8)

    if has_str_rise or is_high_stress:
        audit["rules_triggered"].append("REC-STR-001")
        str_val_repr = round(mean_stress, 2) if mean_stress is not None else "N/A"
        effect_d = str_drift.cohens_d if str_drift else 1.0
        mag = min(1.0, max(0.3, abs(effect_d) / 2.5))
        ev_quality = 0.85 if has_str_rise else 0.60

        candidates.append(
            RecommendationItem(
                recommendation_id="REC-STR-001",
                title="Incorporate Transition Buffers Between Work Blocks",
                category=RecommendationCategory.STRESS_PACING,
                explanation=(
                    f"Self-reported daily stress ratings averaged {str_val_repr} / 5.0"
                    + (f", exhibiting significant upward drift (Cohen's d = {effect_d:+.2f})." if has_str_rise else ".")
                ),
                observed_evidence={
                    "mean_perceived_stress": str_val_repr,
                    "drift_detected": has_str_rise,
                    "cohens_d": round(effect_d, 2) if str_drift else None,
                },
                proposed_action=(
                    "Buffer 10–15 minutes between consecutive meetings or high-demand tasks to review priorities without schedule compression."
                ),
                rationale="Structured micro-buffers prevent task carryover cognitive load from compounding across the day.",
                expected_direction="Lower perceived task urgency and improved pacing predictability.",
                confidence=ConfidenceLevel.HIGH if has_str_rise else ConfidenceLevel.MODERATE,
                priority_score=compute_priority_score(mag, ev_quality, completeness),
                limitations="Subjective rating is an ordinal proxy and does not indicate a medical or psychiatric diagnosis.",
            )
        )

    # -------------------------------------------------------------------------
    # RULE 6: Task Planning Calibration (REC-TSK-001)
    # -------------------------------------------------------------------------
    audit["rules_evaluated"].append("REC-TSK-001")
    is_overplanned = (task_planned_sum >= 20) and (completion_rate < 0.55)

    if is_overplanned:
        audit["rules_triggered"].append("REC-TSK-001")
        mag = min(1.0, max(0.2, (0.60 - completion_rate) / 0.40))
        candidates.append(
            RecommendationItem(
                recommendation_id="REC-TSK-001",
                title="Calibrate Daily Planned Task Volume",
                category=RecommendationCategory.TASK_CALIBRATION,
                explanation=(
                    f"Overall task completion rate was {completion_rate:.0%} ({int(task_comp_sum)}/{int(task_planned_sum)} tasks) "
                    f"across the monitoring window, suggesting daily planning targets may exceed available bandwidth."
                ),
                observed_evidence={
                    "tasks_planned_total": int(task_planned_sum),
                    "tasks_completed_total": int(task_comp_sum),
                    "completion_rate": round(completion_rate, 2),
                },
                proposed_action=(
                    "Experiment with capping planned daily primary tasks to 3–4 essential items to build completion momentum."
                ),
                rationale="Calibrating task estimates to actual historical throughput reduces planning friction and carryover backlog.",
                expected_direction="Higher task closure rate and clearer end-of-day closure.",
                confidence=ConfidenceLevel.MODERATE,
                priority_score=compute_priority_score(mag, 0.70, completeness),
                limitations="Task complexity and multi-day projects may naturally span multiple recording days.",
            )
        )

    # -------------------------------------------------------------------------
    # Deduplication & Priority Sorting
    # -------------------------------------------------------------------------
    # Deduplicate by category (keep highest priority item per category)
    category_best: dict[RecommendationCategory, RecommendationItem] = {}
    for item in candidates:
        if item.category not in category_best or item.priority_score > category_best[item.category].priority_score:
            category_best[item.category] = item

    # Sort descending by priority_score, breaking ties deterministically by recommendation_id
    deduped_sorted = sorted(
        category_best.values(),
        key=lambda x: (-x.priority_score, x.recommendation_id),
    )

    audit["candidates_generated"] = len(candidates)
    audit["final_deduplicated_count"] = len(deduped_sorted)

    return RecommendationReport(
        user_id=user_id,
        evaluation_date=evaluation_date,
        recommendations=deduped_sorted,
        audit_summary=audit,
        insufficient_data=False,
    )
