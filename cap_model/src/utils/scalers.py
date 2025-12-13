"""
Feature scaling utilities
"""

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


class FeatureScaler:
    """Handle feature scaling operations"""

    def __init__(self, method: str = "standard"):
        """
        Initialize FeatureScaler

        Args:
            method: Scaling method ('standard', 'minmax', 'robust')
        """
        self.method = method
        self.scaler = None
        self._initialize_scaler()

    def _initialize_scaler(self):
        """Initialize the appropriate scaler"""
        if self.method == "standard":
            self.scaler = StandardScaler()
        elif self.method == "minmax":
            self.scaler = MinMaxScaler()
        elif self.method == "robust":
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaling method: {self.method}")

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Fit scaler and transform features

        Args:
            X: Features DataFrame

        Returns:
            Scaled features as numpy array
        """
        logger.info(f"Fitting and transforming features with {self.method} scaler...")
        X_scaled = self.scaler.fit_transform(X)
        logger.info(f"Scaled shape: {X_scaled.shape}")
        return X_scaled

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform features using fitted scaler

        Args:
            X: Features DataFrame

        Returns:
            Scaled features as numpy array
        """
        if self.scaler is None:
            raise ValueError("Scaler not fitted. Call fit_transform first.")

        logger.info(f"Transforming features with existing {self.method} scaler...")
        X_scaled = self.scaler.transform(X)
        logger.info(f"Scaled shape: {X_scaled.shape}")
        return X_scaled

    def save(self, filepath: str):
        """Save scaler to disk"""
        joblib.dump(self.scaler, filepath)
        logger.info(f"Saved scaler to {filepath}")

    def load(self, filepath: str):
        """Load scaler from disk"""
        self.scaler = joblib.load(filepath)
        logger.info(f"Loaded scaler from {filepath}")


__all__ = ["FeatureScaler"]
