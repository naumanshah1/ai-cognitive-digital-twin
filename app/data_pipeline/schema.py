"""Dataset schema definitions and constraints for behavioural records.

Defines column groupings, valid ranges, roles (predictors, target, identifiers,
timestamps), and data validation models for Milestone 2.
"""

from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


SCHEMA_VERSION = "0.1.0"

# Raw columns generated or imported per user-day
RAW_COLUMNS = [
    "user_id",
    "record_date",
    "sleep_hours",
    "sleep_quality",
    "focus_duration_hours",
    "screen_time_hours",
    "tasks_planned",
    "tasks_completed",
    "task_difficulty_avg",
    "work_session_duration_hours",
    "inactivity_duration_hours",
    "interruption_count",
    "mood_score",
    "perceived_stress",
    "productivity_score",
]

IDENTIFIER_COLUMNS = ["user_id"]
TIMESTAMP_COLUMNS = ["record_date"]
TARGET_COLUMNS = ["productivity_score"]

# Rating columns that are optionally reported / nullable
NULLABLE_COLUMNS = [
    "sleep_quality",
    "mood_score",
    "perceived_stress",
]

INTEGER_COLUMNS = [
    "sleep_quality",
    "tasks_planned",
    "tasks_completed",
    "interruption_count",
    "mood_score",
    "perceived_stress",
]

FLOAT_COLUMNS = [
    "sleep_hours",
    "focus_duration_hours",
    "screen_time_hours",
    "task_difficulty_avg",
    "work_session_duration_hours",
    "inactivity_duration_hours",
    "productivity_score",
]

# Physical and logical domain ranges: (min_valid, max_valid, min_plausible_warn, max_plausible_warn)
COLUMN_RANGES: dict[str, dict[str, float]] = {
    "sleep_hours": {"min": 0.0, "max": 24.0, "warn_min": 3.0, "warn_max": 14.0},
    "sleep_quality": {"min": 1, "max": 5},
    "focus_duration_hours": {"min": 0.0, "max": 16.0, "warn_min": 0.0, "warn_max": 12.0},
    "screen_time_hours": {"min": 0.0, "max": 24.0, "warn_min": 0.0, "warn_max": 18.0},
    "tasks_planned": {"min": 0, "max": 100},
    "tasks_completed": {"min": 0, "max": 100},
    "task_difficulty_avg": {"min": 1.0, "max": 5.0},
    "work_session_duration_hours": {"min": 0.0, "max": 16.0},
    "inactivity_duration_hours": {"min": 0.0, "max": 16.0},
    "interruption_count": {"min": 0, "max": 200},
    "mood_score": {"min": 1, "max": 5},
    "perceived_stress": {"min": 1, "max": 5},
    "productivity_score": {"min": 0.0, "max": 100.0},
}

# Engineered features derived from raw observations
ENGINEERED_FEATURE_COLUMNS = [
    "task_completion_rate",
    "work_session_utilization",
    "inactivity_ratio",
    "rolling_focus_std_7d",
    "work_session_frequency_7d",
    "rolling_productivity_mean_7d",  # TARGET-DERIVED
    "productivity_change_7d",        # TARGET-DERIVED
    "day_of_week",
    "is_weekend",
]

# Target-derived features that MUST be excluded from predictors when predicting productivity_score
TARGET_DERIVED_COLUMNS = [
    "rolling_productivity_mean_7d",
    "productivity_change_7d",
]

# All columns strictly forbidden from predictor matrices
EXCLUDED_FROM_PREDICTORS = list(
    set(
        IDENTIFIER_COLUMNS
        + TIMESTAMP_COLUMNS
        + TARGET_COLUMNS
        + TARGET_DERIVED_COLUMNS
    )
)

# Standard set of valid candidate predictor features for model training in Milestone 3
PREDICTOR_COLUMNS = [
    "sleep_hours",
    "sleep_quality",
    "focus_duration_hours",
    "screen_time_hours",
    "tasks_planned",
    "tasks_completed",
    "task_difficulty_avg",
    "work_session_duration_hours",
    "inactivity_duration_hours",
    "interruption_count",
    "mood_score",
    "perceived_stress",
    "task_completion_rate",
    "work_session_utilization",
    "inactivity_ratio",
    "rolling_focus_std_7d",
    "work_session_frequency_7d",
    "day_of_week",
    "is_weekend",
]


class DailyBehavioralRecord(BaseModel):
    """Pydantic model representing a single validated user-day record."""

    user_id: str = Field(..., min_length=1, description="Pseudonymous user identifier")
    record_date: date = Field(..., description="Date of the observation")
    sleep_hours: float = Field(..., ge=0.0, le=24.0)
    sleep_quality: Optional[int] = Field(None, ge=1, le=5)
    focus_duration_hours: float = Field(..., ge=0.0, le=16.0)
    screen_time_hours: float = Field(..., ge=0.0, le=24.0)
    tasks_planned: int = Field(..., ge=0)
    tasks_completed: int = Field(..., ge=0)
    task_difficulty_avg: float = Field(..., ge=1.0, le=5.0)
    work_session_duration_hours: float = Field(..., ge=0.0, le=16.0)
    inactivity_duration_hours: float = Field(..., ge=0.0, le=16.0)
    interruption_count: int = Field(..., ge=0)
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    perceived_stress: Optional[int] = Field(None, ge=1, le=5)
    productivity_score: float = Field(..., ge=0.0, le=100.0)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("user_id must not be empty or whitespace")
        return stripped

    @model_validator(mode="after")
    def validate_logical_relationships(self) -> "DailyBehavioralRecord":
        if self.tasks_completed > self.tasks_planned:
            raise ValueError(
                f"tasks_completed ({self.tasks_completed}) cannot exceed tasks_planned ({self.tasks_planned})"
            )
        if self.inactivity_duration_hours > self.work_session_duration_hours:
            raise ValueError(
                f"inactivity_duration_hours ({self.inactivity_duration_hours}) cannot exceed "
                f"work_session_duration_hours ({self.work_session_duration_hours})"
            )
        if self.focus_duration_hours > (self.work_session_duration_hours + 1e-4):
            raise ValueError(
                f"focus_duration_hours ({self.focus_duration_hours}) cannot exceed "
                f"work_session_duration_hours ({self.work_session_duration_hours})"
            )
        return self
