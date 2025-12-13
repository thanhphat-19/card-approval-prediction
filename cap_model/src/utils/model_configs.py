"""
Model configuration utilities
"""

from pathlib import Path
from typing import Dict, List, Optional

from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from src.utils.helpers import load_config
from xgboost import XGBClassifier

# Model class mapping
MODEL_CLASSES = {
    "AdaBoost": AdaBoostClassifier,
    "XGBoost": XGBClassifier,
    "LightGBM": LGBMClassifier,
    "CatBoost": CatBoostClassifier,
    "Naive Bayes": GaussianNB,
}


def get_model_configs(models: Optional[List[str]] = None, config_path: Optional[str] = None) -> Dict:
    """
    Get model configurations for training from config file

    Args:
        models: List of model names to include (optional, defaults to all from config)
        config_path: Path to config file (optional, defaults to src/config/config.yaml)

    Returns:
        Dictionary of model names with 'class' and 'params' structure
    """
    # Load configuration
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    config = load_config(str(config_path))
    model_config = config.get("model", {})
    hyperparameters = model_config.get("hyperparameters", {})

    # Build model configurations
    all_models = {}
    for model_name, model_class in MODEL_CLASSES.items():
        if model_name in hyperparameters:
            params = hyperparameters[model_name]
            # Ensure params is a dict (in case YAML returns None for empty)
            if params is None:
                params = {}

            all_models[model_name] = {"class": model_class, "params": params}

    # Filter models if specific ones requested
    if models:
        return {name: config for name, config in all_models.items() if name in models}

    return all_models


__all__ = [
    "get_model_configs",
]
