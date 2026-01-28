"""
Dimensionality reduction utilities
"""

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.decomposition import PCA


class DimensionalityReducer:
    """Handle dimensionality reduction operations"""

    def __init__(self, n_components: int = 5, random_state: int = 42):
        """
        Initialize DimensionalityReducer

        Args:
            n_components: Number of principal components
            random_state: Random seed for reproducibility
        """
        self.n_components = n_components
        self.random_state = random_state
        self.pca = PCA(n_components=n_components, random_state=random_state)

    def fit_transform(self, X: np.ndarray) -> pd.DataFrame:
        """
        Fit PCA and transform features

        Args:
            X: Scaled features array

        Returns:
            PCA-transformed DataFrame
        """
        logger.info("Applying PCA for dimensionality reduction...")
        X_pca = self.pca.fit_transform(X)

        logger.info(f"PCA components: {X_pca.shape[1]}")
        logger.info("Explained variance ratio:")
        for i, var in enumerate(self.pca.explained_variance_ratio_, 1):
            logger.info(f"  PC{i}: {var:.4f} ({var*100:.2f}%)")
        total_var = self.pca.explained_variance_ratio_.sum()
        logger.info(f"Total variance explained: {total_var:.4f} ({total_var*100:.2f}%)")

        # Convert to DataFrame
        X_pca_df = pd.DataFrame(X_pca, columns=[f"PC{i+1}" for i in range(self.n_components)])

        return X_pca_df

    def transform(self, X: np.ndarray) -> pd.DataFrame:
        """
        Transform features using fitted PCA

        Args:
            X: Scaled features array

        Returns:
            PCA-transformed DataFrame
        """
        logger.info("Transforming features with existing PCA...")
        X_pca = self.pca.transform(X)

        # Convert to DataFrame
        X_pca_df = pd.DataFrame(X_pca, columns=[f"PC{i+1}" for i in range(self.n_components)])

        return X_pca_df

    def save(self, filepath: str):
        """Save PCA model to disk"""
        joblib.dump(self.pca, filepath)
        logger.info(f"Saved PCA to {filepath}")

    def load(self, filepath: str):
        """Load PCA model from disk"""
        self.pca = joblib.load(filepath)
        logger.info(f"Loaded PCA from {filepath}")


__all__ = ["DimensionalityReducer"]
