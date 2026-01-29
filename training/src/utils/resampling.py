"""
Class balancing and resampling utilities
"""

from typing import Tuple

import pandas as pd
from imblearn.combine import SMOTETomek
from imblearn.over_sampling import SMOTE
from loguru import logger


class Resampler:
    """Handle class balancing operations"""

    def __init__(self, random_state: int = 42):
        """Initialize Resampler"""
        self.random_state = random_state

    def apply_smote_tomek(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Balance dataset using SMOTE + Tomek Links

        Args:
            X: Features DataFrame
            y: Target Series

        Returns:
            Tuple of (resampled_features, resampled_target)
        """
        logger.info("Applying SMOTE + Tomek Links for class balancing...")
        logger.info("Before resampling:")
        logger.info(f"  Total: {len(X):,}")
        logger.info(f"  Good (1): {(y == 1).sum():,} ({(y == 1).sum() / len(y) * 100:.2f}%)")
        logger.info(f"  Bad (0): {(y == 0).sum():,} ({(y == 0).sum() / len(y) * 100:.2f}%)")

        # Apply SMOTE + Tomek
        smote_tomek = SMOTETomek(random_state=self.random_state)
        X_resampled, y_resampled = smote_tomek.fit_resample(X, y)

        logger.info("After SMOTE + Tomek:")
        logger.info(f"  Total: {len(X_resampled):,}")
        logger.info(
            f"  Good (1): {(y_resampled == 1).sum():,} ({(y_resampled == 1).sum() / len(y_resampled) * 100:.2f}%)"
        )
        logger.info(
            f"  Bad (0): {(y_resampled == 0).sum():,} ({(y_resampled == 0).sum() / len(y_resampled) * 100:.2f}%)"
        )
        logger.info(f"  Balance Ratio: {(y_resampled == 1).sum() / (y_resampled == 0).sum():.2f}:1")

        # Convert to DataFrame with original column names
        if isinstance(X, pd.DataFrame):
            X_resampled = pd.DataFrame(X_resampled, columns=X.columns)

        return X_resampled, y_resampled

    def apply_smote(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Balance dataset using SMOTE only

        Args:
            X: Features DataFrame
            y: Target Series

        Returns:
            Tuple of (resampled_features, resampled_target)
        """
        logger.info("Applying SMOTE for class balancing...")
        logger.info("Before resampling:")
        logger.info(f"  Total: {len(X):,}")
        logger.info(f"  Good (1): {(y == 1).sum():,} ({(y == 1).sum() / len(y) * 100:.2f}%)")
        logger.info(f"  Bad (0): {(y == 0).sum():,} ({(y == 0).sum() / len(y) * 100:.2f}%)")

        # Apply SMOTE
        smote = SMOTE(random_state=self.random_state)
        X_resampled, y_resampled = smote.fit_resample(X, y)

        logger.info("After SMOTE:")
        logger.info(f"  Total: {len(X_resampled):,}")
        logger.info(
            f"  Good (1): {(y_resampled == 1).sum():,} ({(y_resampled == 1).sum() / len(y_resampled) * 100:.2f}%)"
        )
        logger.info(
            f"  Bad (0): {(y_resampled == 0).sum():,} ({(y_resampled == 0).sum() / len(y_resampled) * 100:.2f}%)"
        )

        # Convert to DataFrame with original column names
        if isinstance(X, pd.DataFrame):
            X_resampled = pd.DataFrame(X_resampled, columns=X.columns)

        return X_resampled, y_resampled


__all__ = ["Resampler"]
