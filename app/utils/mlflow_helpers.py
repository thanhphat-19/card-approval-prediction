"""MLflow utility functions for model loading and management."""

from typing import Any, Optional, Tuple

import mlflow
from loguru import logger


def setup_mlflow_tracking(tracking_uri: str) -> mlflow.tracking.MlflowClient:
    """
    Setup MLflow tracking and return a client instance.

    Args:
        tracking_uri: MLflow tracking server URI.

    Returns:
        Configured MlflowClient instance.
    """
    mlflow.set_tracking_uri(tracking_uri)
    return mlflow.tracking.MlflowClient()


def get_latest_model_version(
    client: mlflow.tracking.MlflowClient,
    model_name: str,
    stage: str,
) -> Tuple[str, str]:
    """
    Get the latest model version for a given model name and stage.

    Args:
        client: MLflow client instance.
        model_name: Name of the registered model.
        stage: Model stage (e.g., 'Production', 'Staging').

    Returns:
        Tuple of (version, run_id) for the latest model.

    Raises:
        ValueError: If no model version is found for the given stage.
    """
    filter_string = f"name='{model_name}'"
    model_versions = client.search_model_versions(filter_string=filter_string)

    # Filter by stage
    stage_versions = [v for v in model_versions if v.current_stage == stage]

    if not stage_versions:
        raise ValueError(f"No model version found for {model_name} in {stage} stage")

    # Sort by version number (descending) and get the latest
    latest_version = sorted(stage_versions, key=lambda v: int(v.version), reverse=True)[0]

    return latest_version.version, latest_version.run_id


def load_model_with_flavor(model_uri: str) -> Optional[Any]:
    """
    Try loading a model with native MLflow flavors for predict_proba support.

    Attempts to load the model using different MLflow flavors in order:
    xgboost, lightgbm, catboost, sklearn.

    Args:
        model_uri: MLflow model URI (e.g., 'models:/model_name/version').

    Returns:
        Native model object if successful, None otherwise.
    """
    flavor_loaders = [
        ("xgboost", mlflow.xgboost.load_model),
        ("lightgbm", mlflow.lightgbm.load_model),
        ("catboost", mlflow.catboost.load_model),
        ("sklearn", mlflow.sklearn.load_model),
    ]

    for flavor_name, loader_func in flavor_loaders:
        try:
            model = loader_func(model_uri)
            logger.debug(f"Loaded model with {flavor_name} flavor")
            return model
        except Exception:
            continue

    logger.warning("Could not load native model for predict_proba - probabilities will be unavailable")
    return None


def check_mlflow_connection(tracking_uri: str) -> bool:
    """
    Check if MLflow server is accessible.

    Args:
        tracking_uri: MLflow tracking server URI.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.search_experiments(max_results=1)
        return True
    except Exception as e:
        logger.warning(f"MLflow connection failed: {e}")
        return False
