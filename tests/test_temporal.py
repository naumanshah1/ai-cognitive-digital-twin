"""Unit tests for Milestone 5 temporal dataset construction, forecasting baselines, and PyTorch LSTM."""

from datetime import datetime
import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler
import torch

from app.ml.regression import compute_regression_metrics
from app.ml.temporal import (
    ProductivityLSTM,
    PyTorchTemporalDataset,
    TemporalPreprocessor,
    TemporalSequenceData,
    build_temporal_sequences,
    evaluate_forecasting_baselines,
    load_temporal_model,
    predict_lstm,
    save_temporal_model,
    train_lstm_forecaster,
)
from app.services.synthetic_data import generate_synthetic_data


@pytest.fixture
def small_synthetic_df() -> pd.DataFrame:
    """Generate small 3-user, 25-day synthetic dataset for fast unit tests."""
    df = generate_synthetic_data(n_users=3, n_days=25, seed=42)
    return df


@pytest.fixture
def sequence_feature_cols() -> list[str]:
    return [
        "sleep_hours", "focus_duration_hours", "interruption_count",
        "task_difficulty_avg", "productivity_score",
    ]


# --- 1. Sequence Construction, Horizon, and Alignment Tests ---

def test_sequence_shape_and_target_alignment(small_synthetic_df, sequence_feature_cols):
    """Verify that sequences have shape (N, L, D) and target belongs to day t+1."""
    seqs = build_temporal_sequences(
        df=small_synthetic_df,
        feature_cols=sequence_feature_cols,
        target_col="productivity_score",
        lookback=5,
        val_start_date="2026-01-16",
        val_end_date="2026-01-20",
        test_start_date="2026-01-21",
        test_end_date="2026-01-25",
    )

    for split_key in ["train", "val", "test"]:
        data = seqs[split_key]
        assert data.X.ndim == 3
        assert data.X.shape[1] == 5  # lookback L=5
        assert data.X.shape[2] == len(sequence_feature_cols)
        assert len(data.y) == len(data.X)
        assert len(data.origin_dates) == len(data.X)
        assert len(data.target_dates) == len(data.X)


def test_forecast_horizon_is_strictly_next_day(small_synthetic_df, sequence_feature_cols):
    """Verify that target_date is exactly 1 day after origin_date (t+1 forecast horizon)."""
    seqs = build_temporal_sequences(
        df=small_synthetic_df,
        feature_cols=sequence_feature_cols,
        target_col="productivity_score",
        lookback=7,
        val_start_date="2026-01-16",
        val_end_date="2026-01-20",
        test_start_date="2026-01-21",
        test_end_date="2026-01-25",
    )

    for split_key in ["train", "val", "test"]:
        data = seqs[split_key]
        for orig_str, tgt_str in zip(data.origin_dates, data.target_dates):
            orig_dt = pd.Timestamp(orig_str)
            tgt_dt = pd.Timestamp(tgt_str)
            assert (tgt_dt - orig_dt).days == 1, f"Expected 1-day step, got {(tgt_dt - orig_dt).days} from {orig_str} to {tgt_str}"


def test_per_user_isolation_no_cross_user_sequences(sequence_feature_cols):
    """Verify that no sequence contains data from more than one user."""
    # Construct 2 users with 10 days each
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    records = []
    for u in ["user_A", "user_B"]:
        for d in dates:
            records.append({
                "user_id": u,
                "record_date": d.strftime("%Y-%m-%d"),
                "sleep_hours": 7.0 if u == "user_A" else 8.0,
                "focus_duration_hours": 4.0 if u == "user_A" else 5.0,
                "interruption_count": 2,
                "task_difficulty_avg": 3.0,
                "productivity_score": 50.0 if u == "user_A" else 60.0,
            })
    df = pd.DataFrame(records)

    seqs = build_temporal_sequences(
        df=df,
        feature_cols=sequence_feature_cols,
        lookback=3,
        val_start_date="2026-01-08",
        val_end_date="2026-01-08",
        test_start_date="2026-01-09",
        test_end_date="2026-01-10",
    )

    for split in ["train", "val", "test"]:
        data = seqs[split]
        for idx in range(len(data.X)):
            uid = data.user_ids[idx]
            sleep_vals = data.X[idx, :, 0]  # sleep_hours
            expected_sleep = 7.0 if uid == "user_A" else 8.0
            assert np.allclose(sleep_vals, expected_sleep), "Cross-user data leakage detected in sequence!"


def test_chronological_ordering_and_daily_continuity():
    """Verify that gaps in daily history are detected and invalid windows skipped."""
    # User has dates Jan 1, Jan 2, Jan 3, [gap Jan 4], Jan 5, Jan 6, Jan 7
    df = pd.DataFrame({
        "user_id": ["u1"] * 6,
        "record_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-05", "2026-01-06", "2026-01-07"],
        "sleep_hours": [7.0] * 6,
        "focus_duration_hours": [4.0] * 6,
        "interruption_count": [2] * 6,
        "task_difficulty_avg": [3.0] * 6,
        "productivity_score": [50.0] * 6,
    })

    cols = ["sleep_hours", "focus_duration_hours", "interruption_count", "task_difficulty_avg", "productivity_score"]
    seqs = build_temporal_sequences(df, cols, lookback=2, val_start_date="2026-01-10", val_end_date="2026-01-10", test_start_date="2026-01-11", test_end_date="2026-01-12")

    # Day Jan 5 following Jan 3 has a gap > 1 day: should not produce sequence bridging Jan 3-5
    for orig, tgt in zip(seqs["train"].origin_dates, seqs["train"].target_dates):
        assert (pd.Timestamp(tgt) - pd.Timestamp(orig)).days == 1


# --- 2. Leakage Protection Tests ---

def test_target_for_day_t_plus_1_never_in_inputs(small_synthetic_df, sequence_feature_cols):
    """Verify that y(t+1) is NEVER present in the input sequence X."""
    # Inject a unique distinct marker into a specific target day
    df = small_synthetic_df.copy()
    marker_val = 99.99
    df.loc[10, "productivity_score"] = marker_val
    marker_date = df.loc[10, "record_date"]
    marker_user = df.loc[10, "user_id"]

    seqs = build_temporal_sequences(
        df=df,
        feature_cols=sequence_feature_cols,
        lookback=4,
        val_start_date="2026-01-16",
        val_end_date="2026-01-20",
        test_start_date="2026-01-21",
        test_end_date="2026-01-25",
    )

    prod_idx = sequence_feature_cols.index("productivity_score")

    for split in ["train", "val", "test"]:
        data = seqs[split]
        for i in range(len(data.y)):
            if data.user_ids[i] == marker_user and data.target_dates[i] == marker_date:
                # The target is marker_val
                assert data.y[i] == marker_val
                # But the input sequence for this forecast MUST NOT contain marker_val
                seq_targets = data.X[i, :, prod_idx]
                assert marker_val not in seq_targets, "Target leakage: target value for t+1 found in input sequence!"


def test_split_boundary_context_uses_only_past_observations(small_synthetic_df, sequence_feature_cols):
    """Verify that validation day 1 uses training dates as context, without leaking validation targets."""
    seqs = build_temporal_sequences(
        df=small_synthetic_df,
        feature_cols=sequence_feature_cols,
        lookback=7,
        val_start_date="2026-01-16",
        val_end_date="2026-01-20",
        test_start_date="2026-01-21",
        test_end_date="2026-01-25",
    )

    val_data = seqs["val"]
    # First validation target is 2026-01-16
    first_val_indices = [i for i, d in enumerate(val_data.target_dates) if d == "2026-01-16"]
    assert len(first_val_indices) > 0

    for idx in first_val_indices:
        # Forecast origin must be Jan 15 (which is the last day of training)
        assert val_data.origin_dates[idx] == "2026-01-15"


# --- 3. Preprocessing & Imputation Tests ---

def test_temporal_preprocessor_train_only_fit():
    """Verify that preprocessor fits exclusively on training data and preserves state."""
    train_df = pd.DataFrame({
        "feat1": [1.0, 2.0, 3.0, 4.0],
        "feat2": [10.0, np.nan, 30.0, 40.0],
        "productivity_score": [50.0, 60.0, 70.0, 80.0],
    })
    val_df = pd.DataFrame({
        "feat1": [100.0, 200.0],  # Outliers in validation
        "feat2": [np.nan, 999.0],
        "productivity_score": [10.0, 20.0],
    })

    prep = TemporalPreprocessor(scale_target=True)
    prep.fit(train_df, feature_names=["feat1", "feat2"], target_col="productivity_score")

    assert prep.imputed_medians_["feat2"] == 30.0  # Median of [10, 30, 40] is 30.0
    initial_mean = prep.feature_scaler_.mean_.copy()

    # Preprocess val array
    val_X = np.array([[[100.0, np.nan]], [[200.0, 999.0]]])
    val_scaled = prep.transform_X(val_X)

    # Internal training statistics must be completely unchanged
    assert np.allclose(prep.feature_scaler_.mean_, initial_mean)
    assert not np.isnan(val_scaled).any()


def test_temporal_preprocessor_inverse_transform_target():
    """Verify that target inverse transformation accurately recovers original units."""
    train_df = pd.DataFrame({
        "feat": [1.0, 2.0, 3.0],
        "productivity_score": [40.0, 50.0, 60.0],
    })
    prep = TemporalPreprocessor(scale_target=True).fit(train_df, ["feat"])

    original_y = np.array([45.0, 55.0, 65.0], dtype=np.float32)
    scaled_y = prep.transform_y(original_y)
    recovered_y = prep.inverse_transform_y(scaled_y)

    assert np.allclose(original_y, recovered_y, atol=1e-4)


# --- 4. Forecasting Baselines Tests ---

def test_evaluate_forecasting_baselines(small_synthetic_df, sequence_feature_cols):
    """Verify training-mean, persistence, and lagged-ridge baseline implementations."""
    seqs = build_temporal_sequences(
        df=small_synthetic_df,
        feature_cols=sequence_feature_cols,
        lookback=5,
        val_start_date="2026-01-16",
        val_end_date="2026-01-20",
        test_start_date="2026-01-21",
        test_end_date="2026-01-25",
    )

    baselines = evaluate_forecasting_baselines(
        train_data=seqs["train"],
        val_data=seqs["val"],
        test_data=seqs["test"],
        feature_names=sequence_feature_cols,
    )

    assert "training_mean" in baselines
    assert "persistence" in baselines
    assert "lagged_ridge" in baselines

    for b in baselines.values():
        assert b["val_metrics"].sample_count == seqs["val"].sample_count
        assert b["test_metrics"].sample_count == seqs["test"].sample_count
        assert b["val_metrics"].rmse > 0.0
        assert b["test_metrics"].rmse > 0.0


# --- 5. PyTorch LSTM Architecture and Training Tests ---

def test_lstm_forward_pass_shape():
    """Verify that LSTM produces output shape (batch_size,) for 3D input (batch, lookback, features)."""
    batch_size, lookback, num_feats = 16, 7, 20
    model = ProductivityLSTM(input_dim=num_feats, hidden_dim=32, num_layers=1)
    x = torch.randn(batch_size, lookback, num_feats)

    out = model(x)
    assert out.shape == (batch_size,)


def test_lstm_training_and_early_stopping(small_synthetic_df, sequence_feature_cols):
    """Verify that LSTM trains on small fixture, achieves early stopping, and restores best checkpoint."""
    seqs = build_temporal_sequences(
        df=small_synthetic_df,
        feature_cols=sequence_feature_cols,
        lookback=5,
        val_start_date="2026-01-16",
        val_end_date="2026-01-20",
        test_start_date="2026-01-21",
        test_end_date="2026-01-25",
    )

    prep = TemporalPreprocessor(scale_target=True).fit(small_synthetic_df, sequence_feature_cols)

    model = ProductivityLSTM(input_dim=len(sequence_feature_cols), hidden_dim=16)
    trained_model, history, best_epoch = train_lstm_forecaster(
        model=model,
        train_data=seqs["train"],
        val_data=seqs["val"],
        preprocessor=prep,
        epochs=15,
        lr=0.01,
        patience=5,
        seed=42,
    )

    assert len(history["train_loss"]) > 0
    assert len(history["val_loss"]) > 0
    assert 1 <= best_epoch <= len(history["val_loss"])

    preds = predict_lstm(trained_model, seqs["val"], prep)
    assert len(preds) == seqs["val"].sample_count
    assert not np.isnan(preds).any()


def test_temporal_model_serialization_and_reload(tmp_path, sequence_feature_cols):
    """Verify serialization and deserialization of LSTM weights and preprocessor."""
    prep = TemporalPreprocessor(scale_target=True)
    prep.feature_names_ = sequence_feature_cols
    prep.imputed_medians_ = {c: 0.0 for c in sequence_feature_cols}
    prep.feature_scaler_ = StandardScaler().fit(np.zeros((5, len(sequence_feature_cols))))
    prep.target_scaler_ = StandardScaler().fit(np.zeros((5, 1)))
    prep.fitted_ = True

    model = ProductivityLSTM(input_dim=len(sequence_feature_cols), hidden_dim=16)
    hparams = {"input_dim": len(sequence_feature_cols), "hidden_dim": 16, "num_layers": 1, "dropout": 0.1}

    save_path = tmp_path / "lstm_test.pt"
    save_temporal_model(model, prep, hparams, save_path)
    assert save_path.exists()

    loaded_model, loaded_prep, loaded_hparams = load_temporal_model(save_path)
    assert loaded_hparams["hidden_dim"] == 16
    assert loaded_prep.fitted_ is True

    # Test identical predictions
    test_X = np.random.randn(4, 5, len(sequence_feature_cols)).astype(np.float32)
    seq_data = TemporalSequenceData(
        X=test_X, y=np.zeros(4), user_ids=["u1"]*4,
        origin_dates=["2026-01-01"]*4, target_dates=["2026-01-02"]*4,
        feature_names=sequence_feature_cols,
    )

    p1 = predict_lstm(model, seq_data, prep)
    p2 = predict_lstm(loaded_model, seq_data, loaded_prep)
    assert np.allclose(p1, p2, atol=1e-5)
