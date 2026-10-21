"""Leakage-safe preprocessing and feature scaling pipeline for behavioural data.

Fits missing-value imputers, outlier bounds, and numerical scalers strictly on
the training set and applies them consistently to validation, test, or inference sets.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.data_pipeline.feature_engineering import audit_feature_leakage
from app.data_pipeline.schema import (
    EXCLUDED_FROM_PREDICTORS,
    IDENTIFIER_COLUMNS,
    NULLABLE_COLUMNS,
    PREDICTOR_COLUMNS,
    TARGET_COLUMNS,
    TIMESTAMP_COLUMNS,
)


@dataclass
class PreprocessedOutput:
    """Preprocessed features, target, and metadata."""

    X: pd.DataFrame
    y: Optional[pd.Series]
    metadata: pd.DataFrame
    feature_names: list[str]


@dataclass
class PreprocessingReport:
    """Summary of fitted preprocessing statistics and outlier detection."""

    fitted_feature_names: list[str]
    imputed_medians: dict[str, float]
    iqr_outlier_bounds: dict[str, dict[str, float]]
    scaler_means: dict[str, float]
    scaler_scales: dict[str, float]
    train_outlier_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fitted_feature_names": self.fitted_feature_names,
            "imputed_medians": self.imputed_medians,
            "iqr_outlier_bounds": self.iqr_outlier_bounds,
            "scaler_means": self.scaler_means,
            "scaler_scales": self.scaler_scales,
            "train_outlier_counts": self.train_outlier_counts,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class BehavioralDataPreprocessor:
    """Reproducible, leakage-safe preprocessor for behavioural records.

    Must be fitted on training data only via `fit()` or `fit_transform()`.
    """

    def __init__(
        self,
        target_col: str = "productivity_score",
        clip_outliers: bool = True,
        outlier_iqr_multiplier: float = 2.5,
    ):
        self.target_col = target_col
        self.clip_outliers = clip_outliers
        self.outlier_iqr_multiplier = outlier_iqr_multiplier

        self.fitted_: bool = False
        self.feature_names_: list[str] = []
        self.imputed_medians_: dict[str, float] = {}
        self.outlier_bounds_: dict[str, tuple[float, float]] = {}
        self.scaler_: StandardScaler = StandardScaler()
        self.report_: Optional[PreprocessingReport] = None

    def fit(self, train_df: pd.DataFrame) -> "BehavioralDataPreprocessor":
        """Fit imputers, outlier thresholds, and StandardScaler on training data only."""
        if len(train_df) == 0:
            raise ValueError("Cannot fit preprocessor on an empty training DataFrame.")

        # Determine safe predictor columns present in train_df
        forbidden = set(EXCLUDED_FROM_PREDICTORS)
        forbidden.add(self.target_col)

        # Select candidate features
        candidate_cols = [c for c in train_df.columns if c not in forbidden]
        # Run strict leakage audit
        self.feature_names_ = audit_feature_leakage(candidate_cols, target_col=self.target_col)

        if not self.feature_names_:
            raise ValueError("No valid predictor features found in training data.")

        # 1. Compute training medians for imputation
        self.imputed_medians_ = {}
        train_features = train_df[self.feature_names_].copy()

        for col in self.feature_names_:
            median_val = float(train_features[col].median(skipna=True))
            if np.isnan(median_val):
                median_val = 0.0
            self.imputed_medians_[col] = round(median_val, 4)

        # Impute training features for subsequent fitting
        train_imputed = train_features.fillna(self.imputed_medians_)

        # 2. Compute outlier bounds (IQR based) on training data
        self.outlier_bounds_ = {}
        iqr_bounds_report: dict[str, dict[str, float]] = {}
        outlier_counts: dict[str, int] = {}

        for col in self.feature_names_:
            q25 = float(train_imputed[col].quantile(0.25))
            q75 = float(train_imputed[col].quantile(0.75))
            iqr = q75 - q25
            if iqr > 1e-6:
                lower = round(q25 - self.outlier_iqr_multiplier * iqr, 4)
                upper = round(q75 + self.outlier_iqr_multiplier * iqr, 4)
            else:
                lower = round(float(train_imputed[col].min()), 4)
                upper = round(float(train_imputed[col].max()), 4)

            self.outlier_bounds_[col] = (lower, upper)
            iqr_bounds_report[col] = {"lower": lower, "upper": upper}

            # Count outliers in training set
            n_outliers = int(((train_imputed[col] < lower) | (train_imputed[col] > upper)).sum())
            if n_outliers > 0:
                outlier_counts[col] = n_outliers

        # Optional outlier clipping on training data before scaling
        train_clipped = train_imputed.copy()
        if self.clip_outliers:
            for col in self.feature_names_:
                low, high = self.outlier_bounds_[col]
                train_clipped[col] = train_clipped[col].clip(lower=low, upper=high)

        # 3. Fit standard scaler
        self.scaler_.fit(train_clipped)

        scaler_means = {
            col: round(float(mean), 4)
            for col, mean in zip(self.feature_names_, self.scaler_.mean_)
        }
        scaler_scales = {
            col: round(float(scale), 4)
            for col, scale in zip(self.feature_names_, self.scaler_.scale_)
        }

        self.report_ = PreprocessingReport(
            fitted_feature_names=self.feature_names_,
            imputed_medians=self.imputed_medians_,
            iqr_outlier_bounds=iqr_bounds_report,
            scaler_means=scaler_means,
            scaler_scales=scaler_scales,
            train_outlier_counts=outlier_counts,
        )

        self.fitted_ = True
        return self

    def transform(self, df: pd.DataFrame) -> PreprocessedOutput:
        """Apply fitted imputers, bounds, and scaling to validation, test, or inference data."""
        if not self.fitted_:
            raise RuntimeError("Preprocessor must be fitted on training data before transform().")

        # Verify all fitted features exist
        missing_feats = [col for col in self.feature_names_ if col not in df.columns]
        if missing_feats:
            raise ValueError(f"Input DataFrame is missing fitted features: {missing_feats}")

        # Extract features in exact fitted order
        features = df[self.feature_names_].copy()

        # 1. Impute using training medians
        features_imputed = features.fillna(self.imputed_medians_)

        # 2. Outlier treatment (clip using training bounds if enabled)
        features_processed = features_imputed.copy()
        if self.clip_outliers:
            for col in self.feature_names_:
                low, high = self.outlier_bounds_[col]
                features_processed[col] = features_processed[col].clip(lower=low, upper=high)

        # 3. Scale using fitted training parameters
        scaled_array = self.scaler_.transform(features_processed)
        X_df = pd.DataFrame(
            scaled_array,
            columns=self.feature_names_,
            index=df.index,
        )

        # Extract target if present (NEVER impute target!)
        y_series = df[self.target_col].copy() if self.target_col in df.columns else None

        # Extract metadata
        meta_cols = [c for c in df.columns if c in IDENTIFIER_COLUMNS or c in TIMESTAMP_COLUMNS]
        metadata = df[meta_cols].copy()

        return PreprocessedOutput(
            X=X_df,
            y=y_series,
            metadata=metadata,
            feature_names=list(self.feature_names_),
        )

    def fit_transform(self, train_df: pd.DataFrame) -> PreprocessedOutput:
        """Fit on train_df and transform it in one step."""
        return self.fit(train_df).transform(train_df)

    def save_parameters(self, output_path: str | Path) -> Path:
        """Export fitted preprocessing parameters to a JSON file."""
        if not self.fitted_ or self.report_ is None:
            raise RuntimeError("Cannot save unfitted preprocessor parameters.")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.report_.to_json())
        return path
