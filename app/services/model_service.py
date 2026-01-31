"""Model service for loading and managing ML models."""

import json
from functools import lru_cache
from pathlib import Path

import mlflow
from loguru import logger

from app.core.config import get_settings
from app.utils.gcs import setup_gcs_credentials
from app.utils.mlflow_helpers import get_latest_model_version, load_model_with_flavor, setup_mlflow_tracking


class ModelService:
    """Service for loading and managing ML models."""

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.sklearn_model = None  # For predict_proba support
        self.version = None
        self.run_id = None
        self._load_model()

    def _load_model(self) -> None:
        """Load model from local path or MLflow registry."""
        try:
            if self.settings.MODEL_PATH:
                self._load_from_local_path()
            else:
                self._load_from_mlflow()
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def _load_from_local_path(self) -> None:
        """Load model from local path (embedded in Docker image)."""
        model_path = Path(self.settings.MODEL_PATH)
        logger.info(f"Loading model from local path: {model_path}")

        # Read metadata
        metadata_path = model_path / "model_metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
            self.version = metadata.get("version", "unknown")
            self.run_id = metadata.get("run_id", "unknown")
            logger.info(f"Model metadata: v{self.version}, run_id={self.run_id}")
        else:
            self.version = "embedded"
            self.run_id = "local"
            logger.warning("No model_metadata.json found, using defaults")

        # Find the model directory (MLflow downloads create a subdirectory)
        model_dir = self._find_model_directory(model_path)

        # Load pyfunc model
        self.model = mlflow.pyfunc.load_model(str(model_dir))

        # Try loading native model for predict_proba support
        self.sklearn_model = self._load_native_model(model_dir)

        self._log_model_load_status()

    def _find_model_directory(self, model_path: Path) -> Path:
        """Find the actual model directory within the downloaded artifacts."""
        # Check if MLmodel file exists directly
        if (model_path / "MLmodel").exists():
            return model_path

        # Look for model subdirectory (MLflow creates model_name/version structure)
        for subdir in model_path.iterdir():
            if subdir.is_dir() and (subdir / "MLmodel").exists():
                return subdir
            # Check one level deeper
            for nested in subdir.iterdir():
                if nested.is_dir() and (nested / "MLmodel").exists():
                    return nested

        raise FileNotFoundError(f"No MLmodel file found in {model_path}")

    def _load_native_model(self, model_dir: Path) -> object:
        """Load native model for predict_proba support from local path."""
        flavor_loaders = [
            ("xgboost", mlflow.xgboost.load_model),
            ("lightgbm", mlflow.lightgbm.load_model),
            ("catboost", mlflow.catboost.load_model),
            ("sklearn", mlflow.sklearn.load_model),
        ]

        for flavor_name, loader_func in flavor_loaders:
            try:
                model = loader_func(str(model_dir))
                logger.debug(f"Loaded native model with {flavor_name} flavor")
                return model
            except Exception:
                continue

        logger.warning("Could not load native model for predict_proba")
        return None

    def _load_from_mlflow(self) -> None:
        """Load model from MLflow registry (original behavior)."""
        self._setup_credentials()
        self._fetch_model_version()
        self._load_model_artifacts_from_mlflow()

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

    def _load_model_artifacts_from_mlflow(self) -> None:
        """Load model artifacts from MLflow (pyfunc and native model)."""
        model_uri = f"models:/{self.settings.MODEL_NAME}/{self.version}"
        logger.info(f"Loading model from MLflow: {model_uri} (stage: {self.settings.MODEL_STAGE})")
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
            "source": "local" if self.settings.MODEL_PATH else "mlflow",
        }


@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    """Get or create model service instance (cached singleton)"""
    logger.info("Initializing model service")
    return ModelService()
