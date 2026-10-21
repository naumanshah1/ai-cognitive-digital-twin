"""Structured data quality reporting for behavioural datasets."""

from dataclasses import asdict, dataclass, field
import json
from typing import Any


@dataclass
class DataQualityReport:
    """Detailed summary of dataset quality, integrity, and validation outcome."""

    schema_version: str
    total_rows: int
    total_columns: int
    duplicate_count: int
    missing_counts: dict[str, int] = field(default_factory=dict)
    missing_percentages: dict[str, float] = field(default_factory=dict)
    invalid_value_counts: dict[str, int] = field(default_factory=dict)
    valid_row_count: int = 0
    invalid_row_count: int = 0
    per_column_ranges: dict[str, dict[str, Any]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    is_valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert report to a dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert report to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_markdown(self) -> str:
        """Generate human-readable GitHub-style markdown report."""
        status = "PASSED" if self.is_valid else "FAILED"
        lines = [
            f"# Data Quality Report — Schema v{self.schema_version}",
            f"**Validation Status:** {status}",
            f"- **Total Rows:** {self.total_rows:,}",
            f"- **Total Columns:** {self.total_columns}",
            f"- **Valid Rows:** {self.valid_row_count:,}",
            f"- **Invalid Rows:** {self.invalid_row_count:,}",
            f"- **Duplicate User-Day Pairs:** {self.duplicate_count:,}",
            "",
            "## Missingness Summary",
            "| Column | Missing Count | Missing % |",
            "|---|---|---|",
        ]

        for col, count in sorted(self.missing_counts.items(), key=lambda x: x[1], reverse=True):
            pct = self.missing_percentages.get(col, 0.0)
            lines.append(f"| {col} | {count:,} | {pct:.2f}% |")

        if self.invalid_value_counts:
            lines.extend([
                "",
                "## Invalid Value Counts",
                "| Column | Invalid Count |",
                "|---|---|",
            ])
            for col, count in self.invalid_value_counts.items():
                lines.append(f"| {col} | {count:,} |")

        if self.errors:
            lines.extend(["", "## Validation Errors"])
            for err in self.errors:
                lines.append(f"- [ERROR] {err}")

        if self.warnings:
            lines.extend(["", "## Validation Warnings"])
            for warn in self.warnings:
                lines.append(f"- [WARNING] {warn}")

        lines.extend([
            "",
            "## Per-Column Observed Ranges",
            "| Column | Min | Max | Mean / Median |",
            "|---|---|---|---|",
        ])
        for col, stats in self.per_column_ranges.items():
            c_min = stats.get("min", "N/A")
            c_max = stats.get("max", "N/A")
            c_mean = stats.get("mean", stats.get("median", "N/A"))
            lines.append(f"| {col} | {c_min} | {c_max} | {c_mean} |")

        return "\n".join(lines)
