"""
MLflow Model Registry utilities for model versioning and deployment
"""

from typing import Dict, Optional

import mlflow
from loguru import logger
from mlflow.tracking import MlflowClient


class MLflowRegistry:
    """Handle MLflow Model Registry operations"""

    def __init__(self, tracking_uri: str = "http://127.0.0.1:5000"):
        """Initialize MLflow Registry client"""
        self.tracking_uri = tracking_uri
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri)
        logger.info(f"Connected to MLflow: {tracking_uri}")

    def register_model(self, run_id: str, model_name: str, artifact_path: str = "model") -> Dict:
        """
        Register a model from an MLflow run

        Args:
            run_id: MLflow run ID
            model_name: Name for the registered model
            artifact_path: Path to model artifact in run

        Returns:
            Dictionary with registration info
        """
        logger.info(f"Registering model '{model_name}' from run {run_id}")

        model_uri = f"runs:/{run_id}/{artifact_path}"
        model_version = mlflow.register_model(model_uri, model_name)

        logger.info(f"✓ Model registered: {model_name} (version {model_version.version})")

        return {"name": model_name, "version": model_version.version, "run_id": run_id, "source": model_uri}

    def transition_model_stage(self, model_name: str, version: int, stage: str = "Production") -> None:
        """
        Transition model to a specific stage

        Args:
            model_name: Name of registered model
            version: Model version number
            stage: Target stage ('Staging', 'Production', 'Archived')
        """
        logger.info(f"Transitioning {model_name} v{version} to {stage}")

        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=True,  # Archive old versions in this stage
        )

        logger.info(f"✓ Model transitioned to {stage}")

    def load_model_from_registry(self, model_name: str, stage: str = "Production"):
        """
        Load model from registry by name and stage

        Args:
            model_name: Name of registered model
            stage: Model stage ('Staging', 'Production')

        Returns:
            Loaded model
        """
        model_uri = f"models:/{model_name}/{stage}"
        logger.info(f"Loading model: {model_uri}")

        model = mlflow.pyfunc.load_model(model_uri)
        logger.info(f"✓ Model loaded successfully")

        return model

    def get_latest_version(self, model_name: str, stage: Optional[str] = None) -> int:
        """
        Get latest version number for a model

        Args:
            model_name: Name of registered model
            stage: Optional stage filter

        Returns:
            Latest version number
        """
        versions = self.client.get_latest_versions(model_name, stages=[stage] if stage else None)

        if not versions:
            raise ValueError(f"No versions found for model: {model_name}")

        latest_version = max([int(v.version) for v in versions])
        logger.info(f"Latest version of {model_name}: {latest_version}")

        return latest_version

    def list_registered_models(self) -> list:
        """List all registered models"""
        models = self.client.search_registered_models()

        logger.info(f"Found {len(models)} registered models")

        model_list = []
        for model in models:
            model_info = {
                "name": model.name,
                "creation_timestamp": model.creation_timestamp,
                "last_updated_timestamp": model.last_updated_timestamp,
                "description": model.description,
                "latest_versions": [
                    {"version": v.version, "stage": v.current_stage, "run_id": v.run_id} for v in model.latest_versions
                ],
            }
            model_list.append(model_info)

        return model_list

    def add_model_description(self, model_name: str, description: str) -> None:
        """Add description to registered model"""
        self.client.update_registered_model(name=model_name, description=description)
        logger.info(f"✓ Description added to {model_name}")

    def add_version_description(self, model_name: str, version: int, description: str) -> None:
        """Add description to specific model version"""
        self.client.update_model_version(name=model_name, version=version, description=description)
        logger.info(f"✓ Description added to {model_name} v{version}")


__all__ = ["MLflowRegistry"]
