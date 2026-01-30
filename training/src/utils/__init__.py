"""Utilities package

Note: Heavy ML dependencies (model_configs, plotting, dimensionality, resampling)
are not imported here to avoid loading lightgbm/catboost/xgboost/matplotlib
at module level. Import them directly when needed:
    from src.utils.model_configs import get_model_configs
    from src.utils.plotting import plot_confusion_matrix
"""

from src.utils.encoders import FeatureEncoder
from src.utils.helpers import ensure_dir, get_project_root, load_config, save_config
from src.utils.logger import logger, setup_file_logging
from src.utils.metrics import calculate_metrics, find_optimal_threshold, get_classification_report
from src.utils.mlflow_registry import MLflowRegistry
from src.utils.scalers import FeatureScaler

__all__ = [
    # Logger
    "logger",
    "setup_file_logging",
    # Data processing
    "FeatureEncoder",
    "FeatureScaler",
    # MLflow
    "MLflowRegistry",
    # Metrics
    "calculate_metrics",
    "get_classification_report",
    "find_optimal_threshold",
    # Helpers
    "load_config",
    "save_config",
    "ensure_dir",
    "get_project_root",
]
