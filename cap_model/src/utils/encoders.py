"""
Feature encoding utilities
"""

from typing import List, Optional

import pandas as pd
from loguru import logger


class FeatureEncoder:
    """Handle feature encoding operations"""

    def __init__(self):
        """Initialize FeatureEncoder"""
        self.feature_names: Optional[List[str]] = None

    def one_hot_encode(self, X: pd.DataFrame, drop_first: bool = True) -> pd.DataFrame:
        """
        One-hot encode categorical features

        Args:
            X: Input features DataFrame
            drop_first: Whether to drop first category (default: True)

        Returns:
            Encoded DataFrame
        """
        logger.info("Encoding categorical features...")
        logger.info(f"Original features: {X.shape[1]}")

        # One-hot encode categorical variables
        X_encoded = pd.get_dummies(X, drop_first=drop_first)

        logger.info(f"Encoded features: {X_encoded.shape[1]}")
        logger.info(f"Feature columns: {list(X_encoded.columns)}")

        self.feature_names = list(X_encoded.columns)

        return X_encoded

    def align_features(self, X: pd.DataFrame, reference_columns: List[str]) -> pd.DataFrame:
        """
        Align DataFrame features with reference columns

        Args:
            X: Input DataFrame
            reference_columns: Reference column names

        Returns:
            Aligned DataFrame
        """
        logger.info("Aligning features with reference columns...")

        # Add missing columns with 0
        for col in reference_columns:
            if col not in X.columns:
                X[col] = 0

        # Keep only reference columns in same order
        X_aligned = X[reference_columns]

        logger.info(f"Aligned shape: {X_aligned.shape}")

        return X_aligned


__all__ = ["FeatureEncoder"]
