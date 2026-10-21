"""Temporal sequence dataset construction, forecasting baselines, and PyTorch LSTM modeling.

Provides strictly leakage-free chronological sequence windowing, train-only preprocessing,
forecasting baselines (Training-Mean, Persistence, Lagged Ridge Regression), and a compact
PyTorch LSTM with early stopping and checkpoint restoration for next-day productivity forecasting.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

# Headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.ml.regression import RegressionMetrics, compute_regression_metrics


@dataclass
class TemporalSequenceData:
    """Container for chronological sequence inputs and future forecast targets."""

    X: np.ndarray  # Shape: (N, lookback, num_features)
    y: np.ndarray  # Shape: (N,) - unscaled target values at t+1
    user_ids: list[str]
    origin_dates: list[str]  # Date at forecast origin t
    target_dates: list[str]  # Date at forecast target t+1
    feature_names: list[str]

    @property
    def sample_count(self) -> int:
        return len(self.y)

    @property
    def lookback(self) -> int:
        return self.X.shape[1] if len(self.X) > 0 else 0

    @property
    def num_features(self) -> int:
        return self.X.shape[2] if len(self.X) > 0 else 0


class PyTorchTemporalDataset(Dataset):
    """PyTorch Dataset wrapping temporal sequence tensors."""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.from_numpy(X.astype(np.float32))
        self.y = torch.from_numpy(y.astype(np.float32)).view(-1, 1)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


class TemporalPreprocessor:
    """Leakage-safe imputer and standardizer for temporal sequence arrays.

    Must be fitted on training sequence data only.
    """

    def __init__(self, scale_target: bool = True):
        self.scale_target = scale_target
        self.fitted_: bool = False
        self.feature_scaler_: StandardScaler = StandardScaler()
        self.target_scaler_: Optional[StandardScaler] = StandardScaler() if scale_target else None
        self.imputed_medians_: dict[str, float] = {}
        self.feature_names_: list[str] = []

    def fit(
        self,
        train_df: pd.DataFrame,
        feature_names: list[str],
        target_col: str = "productivity_score",
    ) -> "TemporalPreprocessor":
        """Fit feature medians and scalers strictly on training data."""
        self.feature_names_ = list(feature_names)
        self.imputed_medians_ = {}

        # 1. Compute training medians for feature imputation
        for col in self.feature_names_:
            if col in train_df.columns:
                med = float(train_df[col].median(skipna=True))
                self.imputed_medians_[col] = 0.0 if np.isnan(med) else med
            else:
                self.imputed_medians_[col] = 0.0

        # 2. Fit feature standardizer on non-missing training features
        train_feats = train_df[self.feature_names_].astype(float).copy()
        for col in self.feature_names_:
            train_feats[col] = train_feats[col].fillna(self.imputed_medians_[col])
        self.feature_scaler_.fit(train_feats.values)

        # 3. Fit target scaler if requested
        if self.scale_target and target_col in train_df.columns:
            train_y = train_df[target_col].astype(float).values.reshape(-1, 1)
            self.target_scaler_.fit(train_y)

        self.fitted_ = True
        return self

    def impute_X(self, X: np.ndarray) -> np.ndarray:
        """Fill NaNs in 3D sequence array (N, L, D) using training-fitted feature medians."""
        if not self.fitted_:
            raise RuntimeError("TemporalPreprocessor must be fitted before impute_X.")
        if len(X) == 0:
            return X.copy()
        N, L, D = X.shape
        flat = X.reshape(-1, D).copy()
        for col_idx, col_name in enumerate(self.feature_names_):
            med = self.imputed_medians_.get(col_name, 0.0)
            nan_mask = np.isnan(flat[:, col_idx])
            if nan_mask.any():
                flat[nan_mask, col_idx] = med
        return flat.reshape(N, L, D).astype(np.float32)

    def transform_X(self, X: np.ndarray) -> np.ndarray:
        """Impute and scale 3D sequence array (N, L, D) using training-fitted scaler."""
        if not self.fitted_:
            raise RuntimeError("TemporalPreprocessor must be fitted before transform_X.")
        if len(X) == 0:
            return X.copy()
        imputed_X = self.impute_X(X)
        N, L, D = imputed_X.shape
        flat = imputed_X.reshape(-1, D)
        scaled_flat = self.feature_scaler_.transform(flat)
        return scaled_flat.reshape(N, L, D).astype(np.float32)

    def transform_y(self, y: np.ndarray) -> np.ndarray:
        """Scale target array using training-fitted target scaler."""
        if not self.fitted_:
            raise RuntimeError("TemporalPreprocessor must be fitted before transform_y.")
        if self.scale_target and self.target_scaler_ is not None:
            return self.target_scaler_.transform(y.reshape(-1, 1)).ravel().astype(np.float32)
        return y.astype(np.float32)

    def inverse_transform_y(self, y_scaled: np.ndarray | torch.Tensor) -> np.ndarray:
        """Convert scaled target predictions back to original physical score units [0, 100]."""
        if isinstance(y_scaled, torch.Tensor):
            y_arr = y_scaled.detach().cpu().numpy().ravel()
        else:
            y_arr = np.asarray(y_scaled).ravel()

        if self.scale_target and self.target_scaler_ is not None:
            inv = self.target_scaler_.inverse_transform(y_arr.reshape(-1, 1)).ravel()
            return inv.astype(np.float32)
        return y_arr.astype(np.float32)


def build_temporal_sequences(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "productivity_score",
    lookback: int = 7,
    user_col: str = "user_id",
    date_col: str = "record_date",
    val_start_date: str = "2026-03-05",
    val_end_date: str = "2026-03-17",
    test_start_date: str = "2026-03-18",
    test_end_date: str = "2026-03-31",
) -> dict[str, TemporalSequenceData]:
    """Construct chronological, leakage-safe rolling sequences for forecasting day t+1.

    Rules:
    - Sequences are grouped by user_id and strictly ordered by record_date.
    - No sequence ever crosses from one user to another.
    - An input window uses observations from days [t - lookback + 1, ..., t].
    - Target is the productivity score observed on day t+1.
    - Day t+1 observations NEVER appear in the input sequence.
    - Daily continuity is strictly validated: every step in window and transition to target
      must have an exact 1-day spacing.
    - Validation and test sequences are allowed to use preceding context from earlier dates
      as inputs (e.g. 2026-03-05 target uses 2026-02-26 through 2026-03-04 from training),
      realistically mirroring live deployment.
    """
    if lookback < 1:
        raise ValueError(f"Lookback must be >= 1, got {lookback}")

    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values([user_col, date_col]).reset_index(drop=True)

    val_start = pd.Timestamp(val_start_date)
    val_end = pd.Timestamp(val_end_date)
    test_start = pd.Timestamp(test_start_date)
    test_end = pd.Timestamp(test_end_date)

    splits: dict[str, dict[str, list]] = {
        "train": {"X": [], "y": [], "users": [], "origin_dates": [], "target_dates": []},
        "val": {"X": [], "y": [], "users": [], "origin_dates": [], "target_dates": []},
        "test": {"X": [], "y": [], "users": [], "origin_dates": [], "target_dates": []},
    }

    # Ensure all feature columns exist and are numeric float
    missing_cols = [c for c in feature_cols if c not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns in DataFrame: {missing_cols}")

    for c in feature_cols:
        data[c] = data[c].astype(float)

    for user_id, group in data.groupby(user_col, sort=False):
        group = group.sort_values(date_col).reset_index(drop=True)
        dates = group[date_col].values
        feat_matrix = group[feature_cols].values
        target_series = group[target_col].astype(float).values

        n_days = len(group)
        if n_days <= lookback:
            continue

        for i in range(lookback, n_days):
            target_dt = pd.Timestamp(dates[i])
            origin_dt = pd.Timestamp(dates[i - 1])

            # Verify daily continuity between origin t and target t+1
            day_gap = (target_dt - origin_dt).days
            if day_gap != 1:
                # Discontinuous gap: skip invalid window
                continue

            # Verify window internal continuity
            window_dates = [pd.Timestamp(d) for d in dates[i - lookback : i]]
            has_gap = False
            for step_idx in range(1, len(window_dates)):
                if (window_dates[step_idx] - window_dates[step_idx - 1]).days != 1:
                    has_gap = True
                    break
            if has_gap:
                continue

            window_feats = feat_matrix[i - lookback : i]
            target_val = float(target_series[i])

            # Assign to split by target date
            if val_start <= target_dt <= val_end:
                split_key = "val"
            elif test_start <= target_dt <= test_end:
                split_key = "test"
            elif target_dt < val_start:
                split_key = "train"
            else:
                # Beyond test window
                continue

            splits[split_key]["X"].append(window_feats)
            splits[split_key]["y"].append(target_val)
            splits[split_key]["users"].append(str(user_id))
            splits[split_key]["origin_dates"].append(origin_dt.strftime("%Y-%m-%d"))
            splits[split_key]["target_dates"].append(target_dt.strftime("%Y-%m-%d"))

    result = {}
    for key in ["train", "val", "test"]:
        X_arr = np.array(splits[key]["X"], dtype=np.float32) if splits[key]["X"] else np.empty((0, lookback, len(feature_cols)), dtype=np.float32)
        y_arr = np.array(splits[key]["y"], dtype=np.float32) if splits[key]["y"] else np.empty((0,), dtype=np.float32)
        result[key] = TemporalSequenceData(
            X=X_arr,
            y=y_arr,
            user_ids=splits[key]["users"],
            origin_dates=splits[key]["origin_dates"],
            target_dates=splits[key]["target_dates"],
            feature_names=list(feature_cols),
        )

    return result


class ProductivityLSTM(nn.Module):
    """Compact recurrent neural network for next-day productivity forecasting."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 32,
        num_layers: int = 1,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, lookback, input_dim)
        lstm_out, _ = self.lstm(x)
        # Final timestep representation
        last_step = lstm_out[:, -1, :]  # (batch_size, hidden_dim)
        out = self.dropout(last_step)
        preds = self.head(out)  # (batch_size, 1)
        return preds.squeeze(-1)  # (batch_size,)


def set_seed(seed: int = 42) -> None:
    """Set deterministic seeds for Python, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_lstm_forecaster(
    model: ProductivityLSTM,
    train_data: TemporalSequenceData,
    val_data: TemporalSequenceData,
    preprocessor: TemporalPreprocessor,
    batch_size: int = 64,
    epochs: int = 50,
    lr: float = 0.002,
    patience: int = 10,
    seed: int = 42,
) -> tuple[ProductivityLSTM, dict[str, list[float]], int]:
    """Train LSTM with early stopping on validation loss and restore best checkpoint."""
    set_seed(seed)

    # Scale inputs using training-fitted preprocessor
    X_train_scaled = preprocessor.transform_X(train_data.X)
    y_train_scaled = preprocessor.transform_y(train_data.y)
    X_val_scaled = preprocessor.transform_X(val_data.X)
    y_val_scaled = preprocessor.transform_y(val_data.y)

    train_ds = PyTorchTemporalDataset(X_train_scaled, y_train_scaled)
    val_ds = PyTorchTemporalDataset(X_val_scaled, y_val_scaled)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.MSELoss()

    history = {"train_loss": [], "val_loss": [], "val_rmse": []}

    best_val_loss = float("inf")
    best_state_dict = None
    best_epoch = 0
    patience_counter = 0

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss_total = 0.0
        n_train_batches = 0

        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            preds = model(batch_X)
            loss = criterion(preds, batch_y.view(-1))
            loss.backward()
            optimizer.step()

            train_loss_total += loss.item() * len(batch_y)
            n_train_batches += len(batch_y)

        epoch_train_loss = train_loss_total / max(1, n_train_batches)

        # Validation phase
        model.eval()
        val_loss_total = 0.0
        n_val_batches = 0
        all_val_preds = []

        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                preds = model(batch_X)
                loss = criterion(preds, batch_y.view(-1))
                val_loss_total += loss.item() * len(batch_y)
                n_val_batches += len(batch_y)
                all_val_preds.append(preds.cpu())

        epoch_val_loss = val_loss_total / max(1, n_val_batches)
        val_preds_arr = torch.cat(all_val_preds).numpy()
        val_preds_orig = preprocessor.inverse_transform_y(val_preds_arr)
        val_metrics = compute_regression_metrics(val_data.y, val_preds_orig)

        history["train_loss"].append(round(epoch_train_loss, 5))
        history["val_loss"].append(round(epoch_val_loss, 5))
        history["val_rmse"].append(round(val_metrics.rmse, 4))

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_epoch = epoch
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    # Restore best checkpoint
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)

    return model, history, best_epoch


def predict_lstm(
    model: ProductivityLSTM,
    seq_data: TemporalSequenceData,
    preprocessor: TemporalPreprocessor,
) -> np.ndarray:
    """Generate unscaled predictions [0, 100] for given sequence data."""
    model.eval()
    X_scaled = preprocessor.transform_X(seq_data.X)
    tensor_X = torch.from_numpy(X_scaled.astype(np.float32))

    with torch.no_grad():
        scaled_preds = model(tensor_X).cpu().numpy()

    return preprocessor.inverse_transform_y(scaled_preds)


def evaluate_forecasting_baselines(
    train_data: TemporalSequenceData,
    val_data: TemporalSequenceData,
    test_data: TemporalSequenceData,
    feature_names: list[str],
    preprocessor: Optional[TemporalPreprocessor] = None,
) -> dict[str, dict[str, Any]]:
    """Train and evaluate strictly matched forecasting baselines.

    All baselines predict the exact same future target on day t+1.
    """
    # Find index of historical productivity_score in features
    prod_idx = feature_names.index("productivity_score") if "productivity_score" in feature_names else -1

    # Baseline A: Training Mean
    train_mean = float(np.mean(train_data.y))
    val_pred_mean = np.full_like(val_data.y, train_mean)
    test_pred_mean = np.full_like(test_data.y, train_mean)

    mean_val_metrics = compute_regression_metrics(val_data.y, val_pred_mean)
    mean_test_metrics = compute_regression_metrics(test_data.y, test_pred_mean)

    # Baseline B: Persistence (Predicts target at origin t for same user)
    # The last timestep in the input window (-1) corresponds to day t
    if prod_idx >= 0:
        val_pred_pers = val_data.X[:, -1, prod_idx]
        test_pred_pers = test_data.X[:, -1, prod_idx]
    else:
        raise ValueError("Cannot evaluate persistence baseline: 'productivity_score' missing from features.")

    pers_val_metrics = compute_regression_metrics(val_data.y, val_pred_pers)
    pers_test_metrics = compute_regression_metrics(test_data.y, test_pred_pers)

    # Baseline C: Lagged-Feature Ridge Regression
    # Impute missing values using preprocessor or training medians
    if preprocessor is not None:
        X_tr_imp = preprocessor.impute_X(train_data.X)
        X_va_imp = preprocessor.impute_X(val_data.X)
        X_te_imp = preprocessor.impute_X(test_data.X)
    else:
        # Standalone median imputation
        X_tr_imp = train_data.X.copy()
        X_va_imp = val_data.X.copy()
        X_te_imp = test_data.X.copy()
        for c_idx in range(train_data.X.shape[2]):
            tr_col = train_data.X[:, :, c_idx].ravel()
            med = float(np.nanmedian(tr_col)) if np.isnan(tr_col).any() else 0.0
            if np.isnan(med):
                med = 0.0
            X_tr_imp[:, :, c_idx] = np.nan_to_num(X_tr_imp[:, :, c_idx], nan=med)
            X_va_imp[:, :, c_idx] = np.nan_to_num(X_va_imp[:, :, c_idx], nan=med)
            X_te_imp[:, :, c_idx] = np.nan_to_num(X_te_imp[:, :, c_idx], nan=med)

    # Uses feature vector at forecast origin t plus window mean
    def _flatten_window(X: np.ndarray) -> np.ndarray:
        origin_t = X[:, -1, :]  # (N, D)
        window_mean = X.mean(axis=1)  # (N, D)
        return np.hstack([origin_t, window_mean])

    X_train_flat = _flatten_window(X_tr_imp)
    X_val_flat = _flatten_window(X_va_imp)
    X_test_flat = _flatten_window(X_te_imp)

    scaler = StandardScaler().fit(X_train_flat)
    X_tr_sc = scaler.transform(X_train_flat)
    X_va_sc = scaler.transform(X_val_flat)
    X_te_sc = scaler.transform(X_test_flat)

    # Select best alpha on validation data
    best_alpha = 10.0
    best_val_rmse = float("inf")
    best_ridge = None

    for alpha in [0.1, 1.0, 10.0, 100.0, 1000.0]:
        r = Ridge(alpha=alpha).fit(X_tr_sc, train_data.y)
        preds = r.predict(X_va_sc)
        rmse = float(np.sqrt(np.mean((val_data.y - preds) ** 2)))
        if rmse < best_val_rmse:
            best_val_rmse = rmse
            best_alpha = alpha
            best_ridge = r

    val_pred_ridge = best_ridge.predict(X_va_sc)
    test_pred_ridge = best_ridge.predict(X_te_sc)

    ridge_val_metrics = compute_regression_metrics(val_data.y, val_pred_ridge)
    ridge_test_metrics = compute_regression_metrics(test_data.y, test_pred_ridge)

    return {
        "training_mean": {
            "name": "Training-Mean Baseline",
            "val_metrics": mean_val_metrics,
            "test_metrics": mean_test_metrics,
            "val_preds": val_pred_mean,
            "test_preds": test_pred_mean,
            "description": f"Predicts constant training target mean ({train_mean:.2f} points)",
        },
        "persistence": {
            "name": "Lag-1 Persistence Baseline",
            "val_metrics": pers_val_metrics,
            "test_metrics": pers_test_metrics,
            "val_preds": val_pred_pers,
            "test_preds": test_pred_pers,
            "description": "Predicts next-day target using latest observed target for the same user at day t",
        },
        "lagged_ridge": {
            "name": "Lagged Ridge Regression",
            "val_metrics": ridge_val_metrics,
            "test_metrics": ridge_test_metrics,
            "val_preds": val_pred_ridge,
            "test_preds": test_pred_ridge,
            "hyperparameters": {"alpha": best_alpha},
            "description": f"Ridge regression on origin features and window summary (alpha={best_alpha})",
        },
    }


def save_temporal_model(
    model: ProductivityLSTM,
    preprocessor: TemporalPreprocessor,
    hyperparameters: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Save PyTorch LSTM weights, preprocessor, and architecture metadata."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "state_dict": model.state_dict(),
        "hyperparameters": hyperparameters,
        "preprocessor": preprocessor,
    }
    torch.save(payload, path)
    return path


def load_temporal_model(
    input_path: str | Path,
) -> tuple[ProductivityLSTM, TemporalPreprocessor, dict[str, Any]]:
    """Load PyTorch LSTM weights, preprocessor, and architecture metadata."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    payload = torch.load(path, map_location="cpu", weights_only=False)
    hparams = payload["hyperparameters"]
    model = ProductivityLSTM(
        input_dim=hparams["input_dim"],
        hidden_dim=hparams.get("hidden_dim", 32),
        num_layers=hparams.get("num_layers", 1),
        dropout=hparams.get("dropout", 0.1),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    preprocessor = payload["preprocessor"]
    return model, preprocessor, hparams


# --- Visualizations ---

def plot_loss_curves(
    history: dict[str, list[float]],
    best_epoch: int,
    output_path: str | Path,
) -> Path:
    """Generate training and validation loss curves across training epochs."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    epochs = range(1, len(history["train_loss"]) + 1)
    plt.figure(figsize=(8, 5))
    plt.plot(epochs, history["train_loss"], label="Training Loss (MSE)", color="#2980b9", linewidth=2)
    plt.plot(epochs, history["val_loss"], label="Validation Loss (MSE)", color="#e67e22", linewidth=2)
    plt.axvline(best_epoch, color="#27ae60", linestyle="--", linewidth=1.5, label=f"Best Checkpoint (Epoch {best_epoch})")

    plt.title("LSTM Training & Validation Loss Curves (Early Stopping)", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Epoch", fontsize=10)
    plt.ylabel("Loss (MSE, Scaled Space)", fontsize=10)
    plt.legend(frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig(path, dpi=200)
    plt.close()
    return path


def plot_forecasting_model_comparison(
    models_dict: dict[str, dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Generate comparative bar chart of Validation and Test RMSE across forecasting candidates."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    names = [info["name"] for info in models_dict.values()]
    val_rmse = [info["val_metrics"].rmse for info in models_dict.values()]
    test_rmse = [info["test_metrics"].rmse for info in models_dict.values()]

    x = np.arange(len(names))
    width = 0.35

    plt.figure(figsize=(9, 5))
    plt.bar(x - width/2, val_rmse, width, label="Validation RMSE", color="#3498db", alpha=0.85)
    plt.bar(x + width/2, test_rmse, width, label="Test RMSE", color="#2c3e50", alpha=0.85)

    plt.ylabel("RMSE (Points, Lower is Better)", fontsize=10, fontweight="bold")
    plt.title("Next-Day Productivity Forecasting: Model Comparison", fontsize=11, fontweight="bold", pad=12)
    plt.xticks(x, names, rotation=15, ha="right", fontsize=9)
    plt.legend(frameon=True)
    plt.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    plt.savefig(path, dpi=200)
    plt.close()
    return path


def plot_temporal_actual_vs_predicted(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    output_path: str | Path,
    r2: float,
    rmse: float,
) -> Path:
    """Generate Actual vs. Predicted scatter plot for forecasting test evaluation."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    y_t = np.asarray(y_true).ravel()
    y_p = np.asarray(y_pred).ravel()

    plt.figure(figsize=(7, 6))
    plt.scatter(y_t, y_p, alpha=0.45, color="#16a085", edgecolors="none", s=25, label="Test Observations")

    min_val = min(float(y_t.min()), float(y_p.min()))
    max_val = max(float(y_t.max()), float(y_p.max()))
    plt.plot([min_val, max_val], [min_val, max_val], color="#c0392b", linestyle="--", linewidth=2, label="Ideal 1:1 Diagonal")

    plt.title(f"Next-Day Productivity: Actual vs. Predicted — {model_name}\n($R^2 = {r2:.4f}$, RMSE $= {rmse:.2f}$ pts)", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Actual Synthetic Productivity Score (t+1)", fontsize=10)
    plt.ylabel("Forecasted Productivity Score (t+1)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()

    plt.savefig(path, dpi=200)
    plt.close()
    return path


def plot_temporal_residuals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    output_path: str | Path,
) -> Path:
    """Generate residual distribution histogram for forecasting test evaluation."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    residuals = np.asarray(y_true).ravel() - np.asarray(y_pred).ravel()

    plt.figure(figsize=(7, 5))
    plt.hist(residuals, bins=35, color="#34495e", edgecolor="#2c3e50", alpha=0.75, density=True)

    mean_res, std_res = float(np.mean(residuals)), float(np.std(residuals))
    x_range = np.linspace(min(residuals), max(residuals), 100)
    norm_pdf = (1.0 / (std_res * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_range - mean_res) / std_res) ** 2)
    plt.plot(x_range, norm_pdf, color="#e74c3c", linewidth=2, label=f"Normal Fit (μ={mean_res:.2f}, σ={std_res:.2f})")

    plt.axvline(0, color="black", linestyle=":", linewidth=1.2)
    plt.title(f"Forecast Residual Distribution — {model_name}", fontsize=11, fontweight="bold", pad=12)
    plt.xlabel("Residual (Actual - Forecast, Points)", fontsize=10)
    plt.ylabel("Density", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()

    plt.savefig(path, dpi=200)
    plt.close()
    return path
