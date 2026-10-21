"""Command-line interface for the AI Cognitive Digital Twin data pipeline."""

import argparse
import sys
from pathlib import Path
import pandas as pd

from app.data_pipeline.pipeline import run_data_pipeline
from app.services.data_validation import validate_behavioral_data
from app.services.synthetic_data import generate_synthetic_data, save_synthetic_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Cognitive Digital Twin — Dataset Engineering CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: generate
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic behavioural records.")
    gen_parser.add_argument("--users", type=int, default=50, help="Number of simulated users.")
    gen_parser.add_argument("--days", type=int, default=90, help="Number of days per user.")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    gen_parser.add_argument("--start-date", type=str, default="2026-01-01", help="Start date (YYYY-MM-DD).")
    gen_parser.add_argument("--scenario", type=str, default="baseline", choices=["baseline", "stress_spike", "focus_drop"])
    gen_parser.add_argument("--output", type=str, default="data/synthetic/behavioral_records.csv", help="Output CSV path.")
    gen_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output file.")

    # Command: validate
    val_parser = subparsers.add_parser("validate", help="Validate a behavioural dataset CSV.")
    val_parser.add_argument("--input", type=str, required=True, help="Input CSV file path.")
    val_parser.add_argument("--strict", action="store_true", help="Raise error if validation fails.")
    val_parser.add_argument("--report", type=str, default=None, help="Optional output JSON report path.")

    # Command: run-all
    run_parser = subparsers.add_parser("run-all", help="Execute complete generation, validation, feature engineering, and splitting.")
    run_parser.add_argument("--users", type=int, default=50, help="Number of users.")
    run_parser.add_argument("--days", type=int, default=90, help="Number of days per user.")
    run_parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    run_parser.add_argument("--output-dir", type=str, default="data", help="Output root directory.")
    run_parser.add_argument("--scenario", type=str, default="baseline", choices=["baseline", "stress_spike", "focus_drop"])
    run_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")

    args = parser.parse_args()

    if args.command == "generate":
        print(f"Generating synthetic dataset: {args.users} users, {args.days} days, seed={args.seed}, scenario={args.scenario}...")
        df = generate_synthetic_data(
            n_users=args.users,
            n_days=args.days,
            start_date=args.start_date,
            seed=args.seed,
            scenario=args.scenario,
        )
        saved_path = save_synthetic_data(
            df,
            output_path=args.output,
            overwrite=args.overwrite,
            save_metadata=True,
        )
        print(f"Successfully generated {len(df):,} records across {df['user_id'].nunique()} users.")
        print(f"Saved dataset to: {saved_path}")
        print(f"Saved metadata to: {saved_path.with_suffix('.metadata.json')}")

    elif args.command == "validate":
        print(f"Validating dataset from: {args.input}...")
        df = pd.read_csv(args.input)
        report = validate_behavioral_data(df, strict=args.strict)
        print(report.to_markdown())
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report.to_json())
            print(f"\nReport written to: {args.report}")
        if not report.is_valid:
            sys.exit(1)

    elif args.command == "run-all":
        print("Executing complete data engineering pipeline...")
        summary = run_data_pipeline(
            n_users=args.users,
            n_days=args.days,
            seed=args.seed,
            output_dir=args.output_dir,
            scenario=args.scenario,
            overwrite=args.overwrite,
        )
        print("\n--- Pipeline Execution Summary ---")
        print(f"Input records: {summary['input_rows']:,}")
        print(f"Validation status: {'PASSED' if summary['validation_passed'] else 'FAILED'}")
        print(f"Engineered total columns: {summary['engineered_columns']}")
        print(f"Predictor features ({summary['predictor_features_count']}): {summary['predictor_feature_names']}")
        print(f"Train split: {summary['split_summary']['train_rows']:,} rows ({summary['split_summary']['train_dates'][0]} to {summary['split_summary']['train_dates'][1]})")
        print(f"Val split:   {summary['split_summary']['val_rows']:,} rows ({summary['split_summary']['val_dates'][0]} to {summary['split_summary']['val_dates'][1]})")
        print(f"Test split:  {summary['split_summary']['test_rows']:,} rows ({summary['split_summary']['test_dates'][0]} to {summary['split_summary']['test_dates'][1]})")
        print(f"Artifacts exported: {len(summary['artifacts_saved'])} files in {args.output_dir}/")


if __name__ == "__main__":
    main()
