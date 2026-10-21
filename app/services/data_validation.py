"""Dataset validation and quality audit service for behavioural records."""

from typing import Any, Optional
import numpy as np
import pandas as pd

from app.data_pipeline.quality_report import DataQualityReport
from app.data_pipeline.schema import (
    COLUMN_RANGES,
    INTEGER_COLUMNS,
    NULLABLE_COLUMNS,
    RAW_COLUMNS,
    SCHEMA_VERSION,
)


class DataValidationError(ValueError):
    """Raised when dataset validation encounters fatal integrity violations."""

    def __init__(self, message: str, report: Optional[DataQualityReport] = None):
        super().__init__(message)
        self.report = report


def validate_behavioral_data(
    df: pd.DataFrame,
    schema_version: str = SCHEMA_VERSION,
    strict: bool = False,
    allow_extra_columns: bool = True,
) -> DataQualityReport:
    """Validate a behavioural dataset against schema, type, range, and logical constraints.

    Returns a comprehensive DataQualityReport. Does not modify or drop rows.
    If strict=True and critical errors are found, raises DataValidationError.
    """
    errors: list[str] = []
    warnings: list[str] = []
    missing_counts: dict[str, int] = {}
    missing_percentages: dict[str, float] = {}
    invalid_value_counts: dict[str, int] = {}
    per_column_ranges: dict[str, dict[str, Any]] = {}

    total_rows = len(df)
    total_columns = len(df.columns)

    if total_rows == 0:
        errors.append("Dataset is empty (0 rows).")
        report = DataQualityReport(
            schema_version=schema_version,
            total_rows=0,
            total_columns=total_columns,
            duplicate_count=0,
            valid_row_count=0,
            invalid_row_count=0,
            errors=errors,
            is_valid=False,
        )
        if strict:
            raise DataValidationError("Dataset is empty.", report=report)
        return report

    # 1. Column presence check
    missing_cols = [col for col in RAW_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required raw columns: {missing_cols}")

    if not allow_extra_columns:
        extra_cols = [col for col in df.columns if col not in RAW_COLUMNS]
        if extra_cols:
            warnings.append(f"Detected extra columns not in raw schema: {extra_cols}")

    # Track row validity mask (True = valid row, False = has error)
    row_valid_mask = pd.Series(True, index=df.index)

    # 2. Missing value audit
    for col in df.columns:
        n_missing = int(df[col].isna().sum())
        missing_counts[col] = n_missing
        missing_percentages[col] = round((n_missing / total_rows) * 100.0, 3)

        if col in RAW_COLUMNS and col not in NULLABLE_COLUMNS and n_missing > 0:
            errors.append(
                f"Column '{col}' is non-nullable but contains {n_missing} missing value(s)."
            )
            row_valid_mask &= df[col].notna()

    # 3. Duplicate (user_id, record_date) check
    duplicate_count = 0
    if "user_id" in df.columns and "record_date" in df.columns:
        dup_mask = df.duplicated(subset=["user_id", "record_date"], keep=False)
        duplicate_count = int(dup_mask.sum())
        if duplicate_count > 0:
            errors.append(
                f"Found {duplicate_count} duplicate record(s) matching (user_id, record_date)."
            )
            row_valid_mask &= ~dup_mask

    # 4. User ID validation
    if "user_id" in df.columns:
        invalid_uid_mask = df["user_id"].isna() | (df["user_id"].astype(str).str.strip() == "")
        n_invalid_uid = int(invalid_uid_mask.sum())
        if n_invalid_uid > 0:
            errors.append(f"Found {n_invalid_uid} empty or whitespace user_id value(s).")
            invalid_value_counts["user_id"] = n_invalid_uid
            row_valid_mask &= ~invalid_uid_mask

    # 5. Date validation
    if "record_date" in df.columns:
        try:
            parsed_dates = pd.to_datetime(df["record_date"], format="%Y-%m-%d", errors="coerce")
            invalid_dates = parsed_dates.isna() & df["record_date"].notna()
            n_invalid_dates = int(invalid_dates.sum())
            if n_invalid_dates > 0:
                errors.append(f"Found {n_invalid_dates} malformed date string(s) in 'record_date'.")
                invalid_value_counts["record_date"] = n_invalid_dates
                row_valid_mask &= ~invalid_dates
        except Exception as e:
            errors.append(f"Failed to parse 'record_date' as dates: {e}")

    # 6. Infinite value check across numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        inf_mask = np.isinf(df[col])
        n_inf = int(inf_mask.sum())
        if n_inf > 0:
            errors.append(f"Column '{col}' contains {n_inf} infinite value(s).")
            invalid_value_counts[f"{col}_inf"] = n_inf
            row_valid_mask &= ~inf_mask

    # 7. Range and domain constraints
    for col, bounds in COLUMN_RANGES.items():
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce")
        valid_numeric = series.dropna()

        if len(valid_numeric) == 0:
            continue

        c_min = float(valid_numeric.min())
        c_max = float(valid_numeric.max())
        c_mean = round(float(valid_numeric.mean()), 3)

        per_column_ranges[col] = {
            "min": round(c_min, 2),
            "max": round(c_max, 2),
            "mean": c_mean,
        }

        min_bound = bounds.get("min")
        max_bound = bounds.get("max")
        warn_min = bounds.get("warn_min")
        warn_max = bounds.get("warn_max")

        # Hard bounds violation
        if min_bound is not None:
            out_of_min = series < min_bound
            n_below = int(out_of_min.sum())
            if n_below > 0:
                errors.append(f"Column '{col}' has {n_below} value(s) below minimum valid bound {min_bound}.")
                invalid_value_counts[f"{col}_below_min"] = n_below
                row_valid_mask &= ~out_of_min

        if max_bound is not None:
            out_of_max = series > max_bound
            n_above = int(out_of_max.sum())
            if n_above > 0:
                errors.append(f"Column '{col}' has {n_above} value(s) above maximum valid bound {max_bound}.")
                invalid_value_counts[f"{col}_above_max"] = n_above
                row_valid_mask &= ~out_of_max

        # Soft bounds warnings
        if warn_min is not None and c_min < warn_min:
            warnings.append(
                f"Column '{col}' observed minimum {c_min:.2f} is unusually low (typical min {warn_min})."
            )
        if warn_max is not None and c_max > warn_max:
            warnings.append(
                f"Column '{col}' observed maximum {c_max:.2f} is unusually high (typical max {warn_max})."
            )

    # 8. Integer constraints
    for col in INTEGER_COLUMNS:
        if col not in df.columns:
            continue
        valid_vals = df[col].dropna()
        if len(valid_vals) > 0:
            # Check if all non-null values are integer-valued
            non_int = (valid_vals.astype(float) % 1 != 0)
            n_non_int = int(non_int.sum())
            if n_non_int > 0:
                errors.append(f"Column '{col}' contains {n_non_int} non-integer value(s).")
                invalid_value_counts[f"{col}_non_integer"] = n_non_int
                row_valid_mask &= ~df.index.isin(valid_vals[non_int].index)

    # 9. Logical relationships
    if "tasks_completed" in df.columns and "tasks_planned" in df.columns:
        task_invalid = df["tasks_completed"] > df["tasks_planned"]
        n_task_invalid = int(task_invalid.sum())
        if n_task_invalid > 0:
            errors.append(
                f"Logical error: tasks_completed > tasks_planned in {n_task_invalid} row(s)."
            )
            invalid_value_counts["tasks_completed_exceeds_planned"] = n_task_invalid
            row_valid_mask &= ~task_invalid

    if "work_session_duration_hours" in df.columns and "inactivity_duration_hours" in df.columns:
        inactivity_invalid = df["inactivity_duration_hours"] > (df["work_session_duration_hours"] + 1e-4)
        n_inactivity_invalid = int(inactivity_invalid.sum())
        if n_inactivity_invalid > 0:
            errors.append(
                f"Logical error: inactivity_duration_hours > work_session_duration_hours in {n_inactivity_invalid} row(s)."
            )
            invalid_value_counts["inactivity_exceeds_work_session"] = n_inactivity_invalid
            row_valid_mask &= ~inactivity_invalid

    if "work_session_duration_hours" in df.columns and "focus_duration_hours" in df.columns:
        focus_invalid = df["focus_duration_hours"] > (df["work_session_duration_hours"] + 1e-4)
        n_focus_invalid = int(focus_invalid.sum())
        if n_focus_invalid > 0:
            errors.append(
                f"Logical error: focus_duration_hours > work_session_duration_hours in {n_focus_invalid} row(s)."
            )
            invalid_value_counts["focus_exceeds_work_session"] = n_focus_invalid
            row_valid_mask &= ~focus_invalid

    valid_row_count = int(row_valid_mask.sum())
    invalid_row_count = total_rows - valid_row_count
    is_valid = len(errors) == 0

    report = DataQualityReport(
        schema_version=schema_version,
        total_rows=total_rows,
        total_columns=total_columns,
        duplicate_count=duplicate_count,
        missing_counts=missing_counts,
        missing_percentages=missing_percentages,
        invalid_value_counts=invalid_value_counts,
        valid_row_count=valid_row_count,
        invalid_row_count=invalid_row_count,
        per_column_ranges=per_column_ranges,
        warnings=warnings,
        errors=errors,
        is_valid=is_valid,
    )

    if strict and not is_valid:
        raise DataValidationError(
            f"Dataset failed validation with {len(errors)} error(s): {errors[:3]}",
            report=report,
        )

    return report
