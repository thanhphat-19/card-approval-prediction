"""Model service for loading and managing ML models from MLflow."""

from functools import lru_cache

import mlflow
from loguru import logger

from app.core.config import get_settings
from app.utils.gcs import setup_gcs_credentials
from app.utils.mlflow_helpers import get_latest_model_version, load_model_with_flavor, setup_mlflow_tracking


class ModelService:
    """Service for loading and managing ML models from MLflow."""

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.sklearn_model = None  # For predict_proba support
        self.version = None
        self.run_id = None
        self._load_model()

    def _load_model(self) -> None:
        """Load model from MLflow registry."""
        try:
            self._setup_credentials()
            self._fetch_model_version()
            self._load_model_artifacts()
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def _setup_credentials(self) -> None:
        """Setup GCS credentials for MLflow artifact access."""
        setup_gcs_credentials(self.settings.GOOGLE_APPLICATION_CREDENTIALS)

    def _fetch_model_version(self) -> None:
        """Fetch the latest model version from MLflow registry."""
        client = setup_mlflow_tracking(self.settings.MLFLOW_TRACKING_URI)

        self.version, self.run_id = get_latest_model_version(
            client=client,
            model_name=self.settings.MODEL_NAME,
            stage=self.settings.MODEL_STAGE,
        )

    def _load_model_artifacts(self) -> None:
        """Load model artifacts (pyfunc and native model for predict_proba)."""
        model_uri = f"models:/{self.settings.MODEL_NAME}/{self.version}"
        logger.info(f"Loading model from: {model_uri} (stage: {self.settings.MODEL_STAGE})")
        logger.info(f"Model run ID: {self.run_id}")

        # Load pyfunc model
        self.model = mlflow.pyfunc.load_model(model_uri)

        # Try loading native model for predict_proba support
        self.sklearn_model = load_model_with_flavor(model_uri)

        self._log_model_load_status()

    def _log_model_load_status(self) -> None:
        """Log the model load status."""
        model_info = f"{self.settings.MODEL_NAME} v{self.version}"
        if self.sklearn_model is not None:
            logger.info(f"✓ Model loaded with predict_proba support: {model_info}")
        else:
            logger.info(f"✓ Model loaded (pyfunc only): {model_info}")

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
