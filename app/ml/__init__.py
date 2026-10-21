"""Machine Learning module for AI Cognitive Digital Twin."""

from app.ml.clustering import BehavioralKMeansPipeline, evaluate_candidate_k, evaluate_clustering_stability
from app.ml.eda import perform_exploratory_data_analysis
from app.ml.feature_selection import (
    DAILY_CLUSTERING_FEATURES,
    USER_AGGREGATED_CLUSTERING_FEATURES,
    prepare_daily_clustering_data,
    prepare_user_level_clustering_data,
)
from app.ml.regression import (
    ModelEvaluationResult,
    RegressionMetrics,
    build_default_candidate_models,
    compute_regression_metrics,
    compute_unstandardized_coefficients,
    evaluate_oracle_regression,
    evaluate_persistence_baseline,
    evaluate_selected_on_test,
    load_regression_model,
    save_regression_model,
    select_best_candidate,
    train_and_evaluate_model,
)
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

__all__ = [
    "BehavioralKMeansPipeline",
    "evaluate_candidate_k",
    "evaluate_clustering_stability",
    "perform_exploratory_data_analysis",
    "DAILY_CLUSTERING_FEATURES",
    "USER_AGGREGATED_CLUSTERING_FEATURES",
    "prepare_daily_clustering_data",
    "prepare_user_level_clustering_data",
    "ModelEvaluationResult",
    "RegressionMetrics",
    "build_default_candidate_models",
    "compute_regression_metrics",
    "compute_unstandardized_coefficients",
    "evaluate_oracle_regression",
    "evaluate_persistence_baseline",
    "evaluate_selected_on_test",
    "load_regression_model",
    "save_regression_model",
    "select_best_candidate",
    "train_and_evaluate_model",
    "ProductivityLSTM",
    "PyTorchTemporalDataset",
    "TemporalPreprocessor",
    "TemporalSequenceData",
    "build_temporal_sequences",
    "evaluate_forecasting_baselines",
    "load_temporal_model",
    "predict_lstm",
    "save_temporal_model",
    "train_lstm_forecaster",
]
