import mlflow
from loguru import logger

from app.core.config import get_settings


class ModelService:
    """Service for loading and managing ML models from MLflow"""

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.model_version = None
        self._load_model()

    def _load_model(self):
        """Load model from MLflow registry"""
        try:
            mlflow.set_tracking_uri(self.settings.MLFLOW_TRACKING_URI)
            model_uri = f"models:/{self.settings.MODEL_NAME}/{self.settings.MODEL_STAGE}"

            logger.info(f"Loading model from: {model_uri}")
            self.model = mlflow.pyfunc.load_model(model_uri)

            # Get model version info
            client = mlflow.tracking.MlflowClient()
            model_versions = client.get_latest_versions(self.settings.MODEL_NAME, stages=[self.settings.MODEL_STAGE])

            if model_versions:
                self.model_version = model_versions[0].version
                logger.info(f"✓ Model loaded: {self.settings.MODEL_NAME} v{self.model_version}")
            else:
                logger.warning("Model version info not available")

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
            "version": self.model_version,
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
        model_service = ModelService()
    return model_service
