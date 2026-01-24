"""Model service for loading and managing ML models from MLflow."""
import os
from functools import lru_cache

import mlflow
from loguru import logger

from app.core.config import get_settings


class ModelService:
    """Service for loading and managing ML models from MLflow"""

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.sklearn_model = None  # For predict_proba support
        self.version = None
        self.run_id = None
        self._load_model()

    def _load_model(self):
        """Load model from MLflow registry"""
        try:
            # Setup GCS authentication if credentials path is provided
            if self.settings.GOOGLE_APPLICATION_CREDENTIALS:
                if os.path.exists(self.settings.GOOGLE_APPLICATION_CREDENTIALS):
                    creds_path = self.settings.GOOGLE_APPLICATION_CREDENTIALS
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                    logger.info(f"Using GCS credentials from: {creds_path}")
                else:
                    creds_path = self.settings.GOOGLE_APPLICATION_CREDENTIALS
                    logger.warning(f"GCS credentials file not found: {creds_path}")
            else:
                logger.info("No GCS credentials specified - using default authentication")

            mlflow.set_tracking_uri(self.settings.MLFLOW_TRACKING_URI)
            client = mlflow.tracking.MlflowClient()

            # Use search_model_versions instead of deprecated get_latest_versions
            filter_string = f"name='{self.settings.MODEL_NAME}'"
            model_versions = client.search_model_versions(filter_string=filter_string)

            # Filter by stage and get the latest
            stage_versions = [v for v in model_versions if v.current_stage == self.settings.MODEL_STAGE]  # noqa: E501

            if not stage_versions:
                raise ValueError(
                    f"No model version found for {self.settings.MODEL_NAME} "
                    f"in {self.settings.MODEL_STAGE} stage"  # noqa: E501
                )

            # Sort by version number (descending) and get the latest
            latest_version = sorted(stage_versions, key=lambda v: int(v.version), reverse=True)[0]
            self.version = latest_version.version
            self.run_id = latest_version.run_id

            model_uri = f"models:/{self.settings.MODEL_NAME}/{self.version}"
            logger.info(f"Loading model from: {model_uri} (stage: {self.settings.MODEL_STAGE})")
            logger.info(f"Model run ID: {self.run_id}")

            self.model = mlflow.pyfunc.load_model(model_uri)

            # Try loading native model for predict_proba support
            # Models are logged with specific flavors (xgboost, lightgbm, catboost, sklearn)
            self.sklearn_model = self._try_load_native_model(model_uri)
            if self.sklearn_model is not None:
                logger.info(
                    f"✓ Model loaded with predict_proba support: {self.settings.MODEL_NAME} v{self.version}"
                )  # noqa: E501
            else:
                logger.info(f"✓ Model loaded (pyfunc only): {self.settings.MODEL_NAME} v{self.version}")  # noqa: E501

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def _try_load_native_model(self, model_uri: str):
        """Try loading model with different MLflow flavors for predict_proba support"""
        loaders = [
            ("xgboost", lambda: mlflow.xgboost.load_model(model_uri)),
            ("lightgbm", lambda: mlflow.lightgbm.load_model(model_uri)),
            ("catboost", lambda: mlflow.catboost.load_model(model_uri)),
            ("sklearn", lambda: mlflow.sklearn.load_model(model_uri)),
        ]
        for flavor, loader in loaders:
            try:
                model = loader()
                logger.debug(f"Loaded model with {flavor} flavor")
                return model
            except Exception:  # noqa: S110
                continue
        logger.warning("Could not load native model for predict_proba - probabilities will be unavailable")
        return None

    def predict(self, features):
        """Make prediction with loaded model"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            prediction = self.model.predict(features)
            return prediction
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    def predict_proba(self, features):
        """Get prediction probabilities from loaded model"""
        if self.sklearn_model is not None and hasattr(self.sklearn_model, "predict_proba"):
            try:
                return self.sklearn_model.predict_proba(features)
            except Exception as e:
                logger.warning(f"predict_proba failed: {e}")
                return None

        # Fallback: return None if predict_proba not available
        return None

    def get_model_info(self):
        """Get model information"""
        return {
            "name": self.settings.MODEL_NAME,
            "stage": self.settings.MODEL_STAGE,
            "version": self.version,
            "run_id": self.run_id,
            "loaded": self.model is not None,
        }

    def reload_model(self):
        """Reload model from MLflow"""
        logger.info("Reloading model...")
        self._load_model()


@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    """Get or create model service instance (cached singleton)"""
    logger.info("Initializing model service")
    return ModelService()
