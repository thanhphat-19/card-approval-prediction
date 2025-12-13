import os

import mlflow
from loguru import logger

from app.core.config import get_settings


class ModelService:
    """Service for loading and managing ML models from MLflow"""

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.version = None
        self.run_id = None
        self._load_model()

    def _load_model(self):
        """Load model from MLflow registry"""
        try:
            # Setup GCS authentication if credentials path is provided
            if self.settings.GOOGLE_APPLICATION_CREDENTIALS:
                if os.path.exists(self.settings.GOOGLE_APPLICATION_CREDENTIALS):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.settings.GOOGLE_APPLICATION_CREDENTIALS
                    logger.info(f"Using GCS credentials from: {self.settings.GOOGLE_APPLICATION_CREDENTIALS}")
                else:
                    logger.warning(f"GCS credentials file not found: {self.settings.GOOGLE_APPLICATION_CREDENTIALS}")
            else:
                logger.info("No GCS credentials specified - using default authentication")

            mlflow.set_tracking_uri(self.settings.MLFLOW_TRACKING_URI)
            client = mlflow.tracking.MlflowClient()

            # Use search_model_versions instead of deprecated get_latest_versions
            filter_string = f"name='{self.settings.MODEL_NAME}'"
            model_versions = client.search_model_versions(filter_string=filter_string)

            # Filter by stage and get the latest
            stage_versions = [v for v in model_versions if v.current_stage == self.settings.MODEL_STAGE]

            if not stage_versions:
                raise ValueError(
                    f"No model version found for {self.settings.MODEL_NAME} in {self.settings.MODEL_STAGE} stage"
                )

            # Sort by version number (descending) and get the latest
            latest_version = sorted(stage_versions, key=lambda v: int(v.version), reverse=True)[0]
            self.version = latest_version.version
            self.run_id = latest_version.run_id  # Capture run_id for preprocessing artifacts

            model_uri = f"models:/{self.settings.MODEL_NAME}/{self.version}"
            logger.info(f"Loading model from: {model_uri} (stage: {self.settings.MODEL_STAGE})")
            logger.info(f"Model run ID: {self.run_id}")

            self.model = mlflow.pyfunc.load_model(model_uri)
            logger.info(f"✓ Model loaded: {self.settings.MODEL_NAME} v{self.version}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

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


# Global instance (will be initialized on app startup)
model_service = None


def get_model_service() -> ModelService:
    """Get or create model service instance"""
    global model_service
    if model_service is None:
        logger.info("Initializing model service")
        model_service = ModelService()
    else:
        logger.debug("Reusing cached model service")
    return model_service
