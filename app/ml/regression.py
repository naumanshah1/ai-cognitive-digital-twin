"""Regression pipeline, candidate model evaluation, selection, and diagnostic reporting.

Implements baseline DummyRegressor, LinearRegression, Ridge, and RandomForestRegressor,
ensuring strict chronological validation-based model selection, leakage-free evaluation,
and diagnostic visualization (actual vs. predicted, residual distributions, and feature importance).
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass
class RegressionMetrics:
    """Standard evaluation metrics for continuous target prediction."""

    mae: float
    rmse: float
    r2: float
    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mae": round(self.mae, 4),
            "rmse": round(self.rmse, 4),
            "r2": round(self.r2, 4),
            "sample_count": int(self.sample_count),
        }


@dataclass
class ModelEvaluationResult:
    """Training, validation, and optional test performance for a regression candidate."""

    model_name: str
    model_type: str
    train_metrics: RegressionMetrics
    val_metrics: RegressionMetrics
    test_metrics: Optional[RegressionMetrics] = None
    hyperparameters: dict[str, Any] = None  # type: ignore
    feature_names: list[str] = None  # type: ignore
    coefficients_or_importances: Optional[dict[str, float]] = None
    unstandardized_coefficients: Optional[dict[str, float]] = None
    unstandardized_intercept: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "train_metrics": self.train_metrics.to_dict(),
            "val_metrics": self.val_metrics.to_dict(),
            "test_metrics": self.test_metrics.to_dict() if self.test_metrics else None,
            "hyperparameters": self.hyperparameters or {},
            "feature_names": self.feature_names or [],
            "coefficients_or_importances": self.coefficients_or_importances,
            "unstandardized_coefficients": self.unstandardized_coefficients,
            "unstandardized_intercept": self.unstandardized_intercept,
        }


def compute_regression_metrics(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
) -> RegressionMetrics:
    """Compute MAE, RMSE, and R2 regression metrics."""
    y_t = np.asarray(y_true).ravel()
    y_p = np.asarray(y_pred).ravel()

    if len(y_t) != len(y_p):
        raise ValueError(f"Shape mismatch: y_true has {len(y_t)} samples, y_pred has {len(y_p)} samples.")

    if len(y_t) == 0:
        raise ValueError("Cannot compute metrics on empty arrays.")

    mae = float(mean_absolute_error(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    r2 = float(r2_score(y_t, y_p))

    return RegressionMetrics(
        mae=mae,
        rmse=rmse,
        r2=r2,
        sample_count=len(y_t),
    )


def extract_feature_importance_or_coefficients(
    model: Any,
    feature_names: list[str],
) -> Optional[dict[str, float]]:
    """Extract model coefficients or feature importances mapped to feature names."""
    if hasattr(model, "coef_"):
        coefs = np.asarray(model.coef_).ravel()
        if len(coefs) == len(feature_names):
            return {
                feat: round(float(c), 4)
                for feat, c in sorted(
                    zip(feature_names, coefs),
                    key=lambda x: abs(x[1]),
                    reverse=True,
                )
            }
    elif hasattr(model, "feature_importances_"):
        imps = np.asarray(model.feature_importances_).ravel()
        if len(imps) == len(feature_names):
            return {
                feat: round(float(imp), 4)
                for feat, imp in sorted(
                    zip(feature_names, imps),
                    key=lambda x: x[1],
                    reverse=True,
                )
            }
    return None


def compute_unstandardized_coefficients(
    model: Any,
    scaler: Any,
    feature_names: list[str],
) -> tuple[dict[str, float], float]:
    """Calculate unstandardized physical slopes b_j and unstandardized intercept b_0.

    Formula:
        b_j = beta_j / scale_j
        b_0 = beta_0 - sum_j (beta_j * mean_j / scale_j)

    Returns:
        tuple of (slopes_dict, unstandardized_intercept)
    """
    if not hasattr(model, "coef_"):
        raise ValueError(f"Model of type {type(model)} does not have 'coef_' attribute.")

    if not hasattr(scaler, "scale_") or not hasattr(scaler, "mean_"):
        raise ValueError("Scaler must have fitted 'scale_' and 'mean_' attributes.")

    scales = np.asarray(scaler.scale_).ravel()
    means = np.asarray(scaler.mean_).ravel()
    betas = np.asarray(model.coef_).ravel()

    if len(betas) != len(feature_names) or len(scales) != len(feature_names):
        raise ValueError(
            f"Dimension mismatch between coefficients ({len(betas)}), scales ({len(scales)}), and feature_names ({len(feature_names)})."
        )

    raw_slopes = betas / scales
    intercept = float(getattr(model, "intercept_", 0.0))
    raw_intercept = float(intercept - np.sum(betas * means / scales))

    slope_dict = {
        feat: round(float(slope), 4)
        for feat, slope in sorted(
            zip(feature_names, raw_slopes),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
    }
    return slope_dict, round(raw_intercept, 4)


def evaluate_persistence_baseline(
    df: pd.DataFrame,
    target_col: str = "productivity_score",
    user_col: str = "user_id",
) -> tuple[pd.Series, RegressionMetrics]:
    """Evaluate lag-1 persistence baseline (predicting y_{u, t} using y_{u, t-1}).

    Requires data to be sorted chronologically per user. If target_lag1 is not present,
    it computes target_lag1 = df.groupby(user_col)[target_col].shift(1).
    Excludes rows where target_lag1 is NaN (e.g. user's first observation in history).
    """
    if "target_lag1" in df.columns:
        lagged = df["target_lag1"].copy()
    else:
        lagged = df.groupby(user_col)[target_col].shift(1)

    valid_mask = lagged.notna() & df[target_col].notna()
    if not valid_mask.any():
        raise ValueError("No valid prior observations available for persistence baseline.")

    y_true = df.loc[valid_mask, target_col]
    y_pred = lagged.loc[valid_mask]

    metrics = compute_regression_metrics(y_true, y_pred)
    return lagged, metrics


def evaluate_oracle_regression(
    df: pd.DataFrame,
    target_col: str = "productivity_score",
) -> tuple[pd.Series, RegressionMetrics]:
    """Evaluate theoretical Oracle regression using known synthetic generative parameters.

    Generative formula (without unobserved user_consistency):
        latent = 30.0 + 4.0*focus + 3.0*(sleep - 7.0) + 3.0*0.875 - 1.5*interruptions - 2.0*(task_difficulty - 3.0)
    """
    required = ["focus_duration_hours", "sleep_hours", "interruption_count", "task_difficulty_avg"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Oracle evaluation requires columns: {missing}")

    user_term = 3.0 * df["user_consistency"] if "user_consistency" in df.columns else 3.0 * 0.875

    oracle_latent = (
        30.0
        + 4.0 * df["focus_duration_hours"]
        + 3.0 * (df["sleep_hours"] - 7.0)
        + user_term
        - 1.5 * df["interruption_count"]
        - 2.0 * (df["task_difficulty_avg"] - 3.0)
    )
    oracle_pred = np.clip(oracle_latent, 0.0, 100.0)

    metrics = compute_regression_metrics(df[target_col], oracle_pred)
    return pd.Series(oracle_pred, index=df.index), metrics


def train_and_evaluate_model(
    model: RegressorMixin,
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    feature_names: list[str],
    hyperparameters: Optional[dict[str, Any]] = None,
    scaler: Optional[Any] = None,
) -> tuple[RegressorMixin, ModelEvaluationResult]:
    """Fit a regression model on training data and evaluate on both train and validation partitions."""
    model.fit(X_train, y_train)

    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)

    train_m = compute_regression_metrics(y_train, train_preds)
    val_m = compute_regression_metrics(y_val, val_preds)

    importances = extract_feature_importance_or_coefficients(model, feature_names)

    unstd_coefs = None
    unstd_intercept = None
    if scaler is not None and hasattr(model, "coef_"):
        try:
            unstd_coefs, unstd_intercept = compute_unstandardized_coefficients(model, scaler, feature_names)
        except Exception:
            pass

    result = ModelEvaluationResult(
        model_name=model_name,
        model_type=model.__class__.__name__,
        train_metrics=train_m,
        val_metrics=val_m,
        hyperparameters=hyperparameters or {},
        feature_names=list(feature_names),
        coefficients_or_importances=importances,
        unstandardized_coefficients=unstd_coefs,
        unstandardized_intercept=unstd_intercept,
    )

    return model, result


def build_default_candidate_models(
    random_state: int = 42,
) -> dict[str, tuple[RegressorMixin, dict[str, Any]]]:
    """Build standardized dictionary of candidate models (Baseline, Linear, and Non-Linear)."""
    return {
        "Dummy (Mean Baseline)": (
            DummyRegressor(strategy="mean"),
            {"strategy": "mean"},
        ),
        "Linear Regression": (
            LinearRegression(),
            {"fit_intercept": True},
        ),
        "Ridge Regression (L2)": (
            Ridge(alpha=1.0, random_state=random_state),
            {"alpha": 1.0, "random_state": random_state},
        ),
        "Random Forest Regressor": (
            RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                min_samples_split=5,
                random_state=random_state,
                n_jobs=-1,
            ),
            {
                "n_estimators": 100,
                "max_depth": 8,
                "min_samples_split": 5,
                "random_state": random_state,
            },
        ),
        "Gradient Boosting Regressor": (
            GradientBoostingRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.05,
                random_state=random_state,
            ),
            {
                "n_estimators": 100,
                "max_depth": 3,
                "learning_rate": 0.05,
                "random_state": random_state,
            },
        ),
    }


def select_best_candidate(
    evaluations: list[ModelEvaluationResult],
    criterion: str = "val_rmse",
) -> ModelEvaluationResult:
    """Select winning candidate model based strictly on validation partition metrics.

    Never accesses test data for model selection.
    """
    if not evaluations:
        raise ValueError("Cannot select from empty evaluations list.")

    # Exclude dummy baseline from candidate selection unless it is the only model
    non_dummy = [e for e in evaluations if "Dummy" not in e.model_name]
    pool = non_dummy if non_dummy else evaluations

    if criterion == "val_rmse":
        return min(pool, key=lambda e: e.val_metrics.rmse)
    elif criterion == "val_mae":
        return min(pool, key=lambda e: e.val_metrics.mae)
    elif criterion == "val_r2":
        return max(pool, key=lambda e: e.val_metrics.r2)
    else:
        raise ValueError(f"Unknown selection criterion '{criterion}'. Expected 'val_rmse', 'val_mae', or 'val_r2'.")


def evaluate_selected_on_test(
    model: RegressorMixin,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[np.ndarray, RegressionMetrics]:
    """Evaluate selected model on test partition (executed strictly after model selection)."""
    test_preds = model.predict(X_test)
    test_metrics = compute_regression_metrics(y_test, test_preds)
    return test_preds, test_metrics


def save_regression_model(model: Any, output_path: str | Path) -> Path:
    """Serialize model to a joblib file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_regression_model(input_path: str | Path) -> Any:
    """Load model from joblib file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)


# --- Visualization Utilities ---

def plot_actual_vs_predicted(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    model_name: str,
    output_path: str | Path,
    r2_val: Optional[float] = None,
    rmse_val: Optional[float] = None,
) -> Path:
    """Generate publication-quality Actual vs. Predicted scatter plot with ideal 1:1 diagonal."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    y_t = np.asarray(y_true).ravel()
    y_p = np.asarray(y_pred).ravel()

    plt.figure(figsize=(7, 6))
    plt.scatter(y_t, y_p, alpha=0.5, color="#1b4f72", edgecolors="none", s=25, label="Observations")

    min_val = min(float(y_t.min()), float(y_p.min()))
    max_val = max(float(y_t.max()), float(y_p.max()))
    plt.plot([min_val, max_val], [min_val, max_val], color="#c0392b", linestyle="--", linewidth=2, label="Ideal 1:1 Fit")

    subtitle = []
    if r2_val is not None:
        subtitle.append(f"$R^2 = {r2_val:.4f}$")
    if rmse_val is not None:
        subtitle.append(f"RMSE $= {rmse_val:.2f}$")
    sub_str = f" ({', '.join(subtitle)})" if subtitle else ""

    plt.title(f"Actual vs. Predicted Productivity — {model_name}{sub_str}", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Actual Synthetic Productivity Score", fontsize=10)
    plt.ylabel("Predicted Productivity Score", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()

    plt.savefig(path, dpi=200)
    plt.close()
    return path


def plot_residuals_diagnostics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    model_name: str,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Generate residual distribution histogram and residual vs. predicted scatter plots."""
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    y_t = np.asarray(y_true).ravel()
    y_p = np.asarray(y_pred).ravel()
    residuals = y_t - y_p

    # 1. Residuals vs Predicted
    scatter_path = out_p / "residuals_vs_predicted.png"
    plt.figure(figsize=(7, 5))
    plt.scatter(y_p, residuals, alpha=0.5, color="#2e4053", edgecolors="none", s=25)
    plt.axhline(0, color="#c0392b", linestyle="--", linewidth=1.5)
    plt.title(f"Residuals vs. Fitted Values — {model_name}", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Fitted Values (Predicted Productivity)", fontsize=10)
    plt.ylabel("Residuals (Actual - Predicted)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(scatter_path, dpi=200)
    plt.close()

    # 2. Residual Distribution Histogram
    hist_path = out_p / "residuals_distribution.png"
    plt.figure(figsize=(7, 5))
    plt.hist(residuals, bins=35, color="#2874a6", edgecolor="#1b4f72", alpha=0.7, density=True)
    # Add normal distribution curve
    mean_res, std_res = float(np.mean(residuals)), float(np.std(residuals))
    x_range = np.linspace(min(residuals), max(residuals), 100)
    norm_pdf = (1.0 / (std_res * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_range - mean_res) / std_res) ** 2)
    plt.plot(x_range, norm_pdf, color="#c0392b", linewidth=2, label=f"Normal Fit (μ={mean_res:.2f}, σ={std_res:.2f})")

    plt.axvline(0, color="black", linestyle=":", linewidth=1)
    plt.title(f"Residual Distribution — {model_name}", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Residual Value (Actual - Predicted)", fontsize=10)
    plt.ylabel("Density", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(hist_path, dpi=200)
    plt.close()

    return scatter_path, hist_path


def plot_feature_importance_or_coefficients(
    coefficients_or_importances: dict[str, float],
    model_name: str,
    output_path: str | Path,
    top_n: int = 15,
) -> Path:
    """Generate horizontal bar chart of top predictor coefficients or feature importances."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    items = list(coefficients_or_importances.items())[:top_n]
    features = [item[0] for item in reversed(items)]
    values = [item[1] for item in reversed(items)]

    is_signed = any(v < 0 for v in values)
    colors = ["#2e86c1" if v >= 0 else "#e74c3c" for v in values] if is_signed else "#2e86c1"

    plt.figure(figsize=(9, 6))
    plt.barh(features, values, color=colors, alpha=0.85, edgecolor="#1b4f72")
    if is_signed:
        plt.axvline(0, color="black", linestyle="--", linewidth=1)

    chart_type = "Standardized Linear Coefficients" if is_signed else "Feature Importance"
    plt.title(f"{chart_type} — {model_name}\n(Associational Relationship, Not Causal Mechanism)", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Magnitude / Weight", fontsize=10)
    plt.grid(True, axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig(path, dpi=200)
    plt.close()
    return path


def plot_model_comparison(
    evaluations: list[ModelEvaluationResult],
    output_path: str | Path,
) -> Path:
    """Generate bar chart comparing Train and Validation RMSE and R2 across candidates."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    names = [e.model_name for e in evaluations]
    train_rmse = [e.train_metrics.rmse for e in evaluations]
    val_rmse = [e.val_metrics.rmse for e in evaluations]
    val_r2 = [e.val_metrics.r2 for e in evaluations]

    x = np.arange(len(names))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.bar(x - width/2, train_rmse, width, label="Train RMSE", color="#85929e", alpha=0.8)
    ax1.bar(x + width/2, val_rmse, width, label="Val RMSE", color="#2e86c1", alpha=0.85)
    ax1.set_ylabel("RMSE (Lower is Better)", color="#1b4f72", fontsize=11, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Twin axis for R2
    ax2 = ax1.twinx()
    ax2.plot(x, val_r2, color="#c0392b", marker="o", linewidth=2, linestyle="--", label="Val $R^2$")
    ax2.set_ylabel("Validation $R^2$ (Higher is Better)", color="#c0392b", fontsize=11, fontweight="bold")
    ax2.legend(loc="upper right")

    plt.title("Model Selection: Candidate Comparison on Chronological Data", fontsize=12, fontweight="bold", pad=14)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()
    return path
