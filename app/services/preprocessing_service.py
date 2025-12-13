"""Preprocessing service for encoding categorical features before prediction"""

import json
from pathlib import Path
from typing import List, Optional

import joblib
import mlflow
import pandas as pd
from loguru import logger

from app.core.config import get_settings


class PreprocessingService:
    """Service for preprocessing input data before model prediction"""

    def __init__(self, run_id: Optional[str] = None):
        """Initialize preprocessing service and load artifacts from MLflow"""
        self.settings = get_settings()
        self.run_id = run_id
        self.scaler, self.pca, self.feature_names = self._load_from_mlflow(run_id)
        logger.info(f"Preprocessing service ready ({len(self.feature_names)} features)")

    def _load_from_mlflow(self, run_id: str):
        """Load preprocessing artifacts from MLflow run"""
        mlflow.set_tracking_uri(self.settings.MLFLOW_TRACKING_URI)
        artifact_uri = f"runs:/{run_id}/preprocessors"
        local_path = Path(mlflow.artifacts.download_artifacts(artifact_uri))

        # Load artifacts
        scaler = joblib.load(local_path / "scaler.pkl")
        pca = joblib.load(local_path / "pca.pkl")

        with open(local_path / "feature_names.json", "r") as f:
            feature_names = json.load(f)["feature_names"]

        return scaler, pca, feature_names

    def align_features(self, X: pd.DataFrame, reference_columns: List[str]) -> pd.DataFrame:
        """Align DataFrame features with reference columns"""
        for col in reference_columns:
            if col not in X.columns:
                X[col] = 0
        return X[reference_columns]

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess input for model prediction: encode → align → scale → PCA"""
        # Drop ID column - it's not a feature
        if "ID" in df.columns:
            df = df.drop("ID", axis=1)

        # One-hot encode
        df_encoded = pd.get_dummies(df.copy(), drop_first=True)

        # Align features
        df_aligned = self.align_features(df_encoded, self.feature_names)

        # Scale
        df_scaled = self.scaler.transform(df_aligned)

        # PCA
        df_pca = self.pca.transform(df_scaled)

        # Return as DataFrame with PC column names
        return pd.DataFrame(df_pca, columns=[f"PC{i+1}" for i in range(df_pca.shape[1])], index=df.index)


# Global instance (will be initialized lazily)
preprocessing_service = None


def get_preprocessing_service(run_id: Optional[str] = None) -> PreprocessingService:
    """Get or create preprocessing service instance"""
    global preprocessing_service
    if preprocessing_service is None or (run_id and preprocessing_service.run_id != run_id):
        preprocessing_service = PreprocessingService(run_id)
    return preprocessing_service
