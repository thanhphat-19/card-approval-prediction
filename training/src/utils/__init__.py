"""Utilities package"""

from src.utils.dimensionality import DimensionalityReducer
from src.utils.encoders import FeatureEncoder
from src.utils.helpers import ensure_dir, get_project_root, load_config, save_config
from src.utils.logger import logger, setup_file_logging
from src.utils.metrics import calculate_metrics, find_optimal_threshold, get_classification_report
from src.utils.mlflow_registry import MLflowRegistry
from src.utils.model_configs import get_model_configs
from src.utils.plotting import (
    plot_confusion_matrix,
    plot_precision_recall_curve,
    plot_roc_curve,
    plot_threshold_analysis,
)
from src.utils.resampling import Resampler
from src.utils.scalers import FeatureScaler

__all__ = [
    # Logger
    "logger",
    "setup_file_logging",
    # Data processing
    "FeatureEncoder",
    "FeatureScaler",
    "DimensionalityReducer",
    "Resampler",
    # MLflow
    "MLflowRegistry",
    # Metrics
    "calculate_metrics",
    "get_classification_report",
    "find_optimal_threshold",
    # Plotting
    "plot_confusion_matrix",
    "plot_roc_curve",
    "plot_precision_recall_curve",
    "plot_threshold_analysis",
    # Model configs
    "get_model_configs",
    # Helpers
    "load_config",
    "save_config",
    "ensure_dir",
    "get_project_root",
]
