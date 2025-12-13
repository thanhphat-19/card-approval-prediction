"""
MLflow artifact utilities for logging and loading preprocessing artifacts
"""

import json
from pathlib import Path
from typing import Dict, Optional

import joblib
import mlflow
from loguru import logger


class MLflowArtifactManager:
    """Manage logging and loading of preprocessing artifacts in MLflow"""

    @staticmethod
    def log_preprocessing_artifacts(
        scaler=None, pca=None, feature_names: Optional[list] = None, artifact_path: str = "preprocessors"
    ):
        """
        Log preprocessing artifacts to MLflow

        Args:
            scaler: Fitted scaler object
            pca: Fitted PCA object
            feature_names: List of feature names after encoding
            artifact_path: Path within MLflow run to store artifacts
        """
        try:
            artifact_dir = Path("preprocessors")
            artifact_dir.mkdir(exist_ok=True)

            # Save scaler (extract inner sklearn object if it's a wrapper)
            if scaler is not None:
                scaler_path = artifact_dir / "scaler.pkl"
                # If it's a wrapper class with .scaler attribute, save the inner sklearn object
                scaler_to_save = scaler.scaler if hasattr(scaler, "scaler") else scaler
                joblib.dump(scaler_to_save, scaler_path)
                mlflow.log_artifact(str(scaler_path), artifact_path)
                logger.info(f"✓ Logged scaler to MLflow")

            # Save PCA (extract inner sklearn object if it's a wrapper)
            if pca is not None:
                pca_path = artifact_dir / "pca.pkl"
                # If it's a wrapper class with .pca attribute, save the inner sklearn object
                pca_to_save = pca.pca if hasattr(pca, "pca") else pca
                joblib.dump(pca_to_save, pca_path)
                mlflow.log_artifact(str(pca_path), artifact_path)
                logger.info(f"✓ Logged PCA to MLflow")

            # Save feature names
            if feature_names is not None:
                features_path = artifact_dir / "feature_names.json"
                with open(features_path, "w") as f:
                    json.dump({"feature_names": feature_names}, f, indent=2)
                mlflow.log_artifact(str(features_path), artifact_path)
                logger.info(f"✓ Logged feature names to MLflow ({len(feature_names)} features)")

        except Exception as e:
            logger.error(f"Failed to log preprocessing artifacts: {e}")

    @staticmethod
    def load_preprocessing_artifacts(run_id: str, artifact_path: str = "preprocessors") -> Dict:
        """
        Load preprocessing artifacts from MLflow

        Args:
            run_id: MLflow run ID
            artifact_path: Path within MLflow run where artifacts are stored

        Returns:
            Dictionary containing scaler, pca, and feature_names
        """
        artifacts = {}

        try:
            # Download artifacts to temp directory
            artifact_uri = f"runs:/{run_id}/{artifact_path}"
            local_path = mlflow.artifacts.download_artifacts(artifact_uri)
            local_path = Path(local_path)

            # Load scaler
            scaler_path = local_path / "scaler.pkl"
            if scaler_path.exists():
                artifacts["scaler"] = joblib.load(scaler_path)
                logger.info(f"✓ Loaded scaler from MLflow run {run_id}")
            else:
                logger.warning(f"Scaler not found in run {run_id}")

            # Load PCA
            pca_path = local_path / "pca.pkl"
            if pca_path.exists():
                artifacts["pca"] = joblib.load(pca_path)
                logger.info(f"✓ Loaded PCA from MLflow run {run_id}")
            else:
                logger.info(f"PCA not found in run {run_id} (may not be used)")

            # Load feature names
            features_path = local_path / "feature_names.json"
            if features_path.exists():
                with open(features_path, "r") as f:
                    data = json.load(f)
                    artifacts["feature_names"] = data.get("feature_names", [])
                logger.info(
                    f"✓ Loaded feature names from MLflow run {run_id} ({len(artifacts['feature_names'])} features)"
                )
            else:
                logger.warning(f"Feature names not found in run {run_id}")

        except Exception as e:
            logger.error(f"Failed to load artifacts from run {run_id}: {e}")

        return artifacts


__all__ = ["MLflowArtifactManager"]
