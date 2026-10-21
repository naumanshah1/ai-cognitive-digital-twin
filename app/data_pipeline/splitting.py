"""Chronological train/validation/test dataset splitting for temporal prediction.

Ensures strict temporal ordering and zero future-data leakage across splits.
"""

from dataclasses import asdict, dataclass, field
import json
from typing import Any, Optional
import pandas as pd


@dataclass
class PartitionInfo:
    """Metadata describing a single partition."""

    name: str
    row_count: int
    user_count: int
    min_date: str
    max_date: str
    unique_dates: int


@dataclass
class DataSplitReport:
    """Detailed summary of the dataset partitioning outcome."""

    strategy: str
    train: PartitionInfo
    validation: PartitionInfo
    test: PartitionInfo
    total_rows: int
    train_ratio: float
    val_ratio: float
    test_ratio: float
    date_overlap_detected: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    date_col: str = "record_date",
    user_col: str = "user_id",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, DataSplitReport]:
    """Split behavioural data into chronological train, validation, and test sets.

    Partitions are created along calendar date boundaries so that:
    train_dates < val_dates < test_dates.
    Never shuffles individual rows.

    Args:
        df: Input DataFrame.
        train_ratio: Fraction of dates assigned to training (default 0.70).
        val_ratio: Fraction of dates assigned to validation (default 0.15).
        test_ratio: Fraction of dates assigned to testing (default 0.15).
        date_col: Name of date column.
        user_col: Name of user identifier column.

    Returns:
        (train_df, val_df, test_df, split_report)
    """
    total_rows = len(df)
    if total_rows < 10:
        raise ValueError(
            f"Dataset has only {total_rows} rows; at least 10 rows are required for splitting."
        )

    if not abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5:
        raise ValueError(
            f"Split ratios must sum to 1.0; got {train_ratio} + {val_ratio} + {test_ratio} = "
            f"{train_ratio + val_ratio + test_ratio}"
        )

    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in DataFrame.")

    # Convert to datetime and sort
    df_sorted = df.copy()
    df_sorted["_parsed_dt"] = pd.to_datetime(df_sorted[date_col], errors="coerce")
    if df_sorted["_parsed_dt"].isna().any():
        raise ValueError(f"Found unparseable dates in '{date_col}'.")

    df_sorted = df_sorted.sort_values(["_parsed_dt", user_col if user_col in df_sorted.columns else "_parsed_dt"])

    unique_dates = df_sorted["_parsed_dt"].drop_duplicates().sort_values().reset_index(drop=True)
    n_dates = len(unique_dates)

    if n_dates < 3:
        raise ValueError(
            f"Dataset has only {n_dates} unique date(s). Chronological 3-way splitting requires at least 3 distinct dates."
        )

    # Determine cutoff indices on unique dates
    train_end_idx = max(1, int(round(n_dates * train_ratio)))
    val_end_idx = max(train_end_idx + 1, int(round(n_dates * (train_ratio + val_ratio))))

    # Ensure at least 1 date in each split
    if train_end_idx >= n_dates - 1:
        train_end_idx = n_dates - 2
        val_end_idx = n_dates - 1
    elif val_end_idx >= n_dates:
        val_end_idx = n_dates - 1

    train_dates = set(unique_dates.iloc[:train_end_idx])
    val_dates = set(unique_dates.iloc[train_end_idx:val_end_idx])
    test_dates = set(unique_dates.iloc[val_end_idx:])

    # Partition DataFrames
    train_mask = df_sorted["_parsed_dt"].isin(train_dates)
    val_mask = df_sorted["_parsed_dt"].isin(val_dates)
    test_mask = df_sorted["_parsed_dt"].isin(test_dates)

    train_df = df_sorted[train_mask].drop(columns=["_parsed_dt"]).copy()
    val_df = df_sorted[val_mask].drop(columns=["_parsed_dt"]).copy()
    test_df = df_sorted[test_mask].drop(columns=["_parsed_dt"]).copy()

    # Safety assertion: non-overlapping dates
    train_max = pd.to_datetime(train_df[date_col]).max()
    val_min = pd.to_datetime(val_df[date_col]).min()
    val_max = pd.to_datetime(val_df[date_col]).max()
    test_min = pd.to_datetime(test_df[date_col]).min()

    overlap_detected = not (train_max < val_min <= val_max < test_min)

    def _get_partition_info(name: str, p_df: pd.DataFrame) -> PartitionInfo:
        return PartitionInfo(
            name=name,
            row_count=len(p_df),
            user_count=int(p_df[user_col].nunique()) if user_col in p_df.columns else 0,
            min_date=str(p_df[date_col].min()) if len(p_df) > 0 else "N/A",
            max_date=str(p_df[date_col].max()) if len(p_df) > 0 else "N/A",
            unique_dates=int(p_df[date_col].nunique()) if len(p_df) > 0 else 0,
        )

    report = DataSplitReport(
        strategy="chronological_by_date",
        train=_get_partition_info("train", train_df),
        validation=_get_partition_info("validation", val_df),
        test=_get_partition_info("test", test_df),
        total_rows=total_rows,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        date_overlap_detected=overlap_detected,
        notes=[
            "Splitting strictly follows date boundaries. Historical observations precede validation and test.",
            "Limitation: Global date splitting forecasts future behavior for users with known history. "
            "To evaluate generalization to completely unseen users, use unseen_user_split.",
        ],
    )

    if overlap_detected:
        raise ValueError("Fatal error: Chronological partition date overlap detected!")

    return train_df, val_df, test_df, report


def unseen_user_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    user_col: str = "user_id",
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Distinct splitting strategy that partitions by user_id to test unseen-user generalization.

    Kept separate from chronological splitting as requested by research protocol.
    """
    if user_col not in df.columns:
        raise ValueError(f"User column '{user_col}' not found.")

    users = df[user_col].drop_duplicates().sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n_users = len(users)

    if n_users < 3:
        raise ValueError("At least 3 distinct users are required for 3-way user-level split.")

    train_end = max(1, int(round(n_users * train_ratio)))
    val_end = max(train_end + 1, int(round(n_users * (train_ratio + val_ratio))))

    train_users = set(users.iloc[:train_end])
    val_users = set(users.iloc[train_end:val_end])
    test_users = set(users.iloc[val_end:])

    train_df = df[df[user_col].isin(train_users)].copy()
    val_df = df[df[user_col].isin(val_users)].copy()
    test_df = df[df[user_col].isin(test_users)].copy()

    report = {
        "strategy": "grouped_unseen_users",
        "total_users": n_users,
        "train_users": len(train_users),
        "val_users": len(val_users),
        "test_users": len(test_users),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
    }

    return train_df, val_df, test_df, report
