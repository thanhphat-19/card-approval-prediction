"""
Feature engineering and preprocessing module
"""

from pathlib import Path
from typing import Optional, Tuple

import joblib
import pandas as pd
from loguru import logger
from sklearn.model_selection import train_test_split
from src.utils.dimensionality import DimensionalityReducer
from src.utils.encoders import FeatureEncoder
from src.utils.resampling import Resampler
from src.utils.scalers import FeatureScaler


class FeatureEngineer:
    """Handle feature engineering using utility modules"""

    def __init__(self, random_state: int = 42):
        """Initialize FeatureEngineer"""
        self.random_state = random_state
        self.encoder = FeatureEncoder()
        self.resampler = Resampler(random_state)
        self.scaler = FeatureScaler(method="standard")
        self.pca = None
        self.feature_names = None

    def encode_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features"""
        return self.encoder.one_hot_encode(X)

    def apply_smote_tomek(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Balance dataset using SMOTE + Tomek Links"""
        return self.resampler.apply_smote_tomek(X, y)

    def scale_features(self, X: pd.DataFrame, fit: bool = True):
        """Scale features using StandardScaler"""
        if fit:
            return self.scaler.fit_transform(X)
        return self.scaler.transform(X)

    def apply_pca(self, X, n_components: int = 5, fit: bool = True) -> pd.DataFrame:
        """Apply PCA for dimensionality reduction"""
        if fit:
            self.pca = DimensionalityReducer(n_components, self.random_state)
            return self.pca.fit_transform(X)
        return self.pca.transform(X)

    def train_test_split_data(
        self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into training and test sets

        Args:
            X: Features DataFrame
            y: Target Series
            test_size: Proportion of test set

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        logger.info("Splitting data into train and test sets...")

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=self.random_state)

        logger.info("Data Split:")
        logger.info(f"  Training: {X_train.shape[0]:,} samples")
        logger.info(f"    - Good (1): {(y_train == 1).sum():,} ({(y_train == 1).sum() / len(y_train) * 100:.2f}%)")
        logger.info(f"    - Bad (0): {(y_train == 0).sum():,} ({(y_train == 0).sum() / len(y_train) * 100:.2f}%)")
        logger.info(f"  Test: {X_test.shape[0]:,} samples")
        logger.info(f"    - Good (1): {(y_test == 1).sum():,} ({(y_test == 1).sum() / len(y_test) * 100:.2f}%)")
        logger.info(f"    - Bad (0): {(y_test == 0).sum():,} ({(y_test == 0).sum() / len(y_test) * 100:.2f}%)")

        return X_train, X_test, y_train, y_test

    def full_pipeline(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        apply_smote: bool = True,
        apply_pca_transform: bool = True,
        n_components: int = 5,
        test_size: float = 0.2,
        save_preprocessors: bool = True,
        output_dir: Optional[str] = None,
    ) -> dict:
        """
        Complete feature engineering pipeline

        Args:
            X: Raw features DataFrame
            y: Target Series
            apply_smote: Whether to apply SMOTE+Tomek
            apply_pca_transform: Whether to apply PCA
            n_components: Number of PCA components
            test_size: Proportion of test set
            save_preprocessors: Whether to save scaler and PCA
            output_dir: Directory to save preprocessors

        Returns:
            Dictionary containing processed data and metadata
        """
        logger.info("=" * 80)
        logger.info("FEATURE ENGINEERING PIPELINE")
        logger.info("=" * 80)

        # 1. Encode features
        X_encoded = self.encode_features(X)
        self.feature_names = X_encoded.columns.tolist()

        # 2. Apply SMOTE+Tomek if requested
        if apply_smote:
            X_resampled, y_resampled = self.apply_smote_tomek(X_encoded, y)
        else:
            X_resampled, y_resampled = X_encoded, y
            logger.info("Skipping SMOTE+Tomek resampling")

        # 3. Scale features
        X_scaled = self.scale_features(X_resampled, fit=True)

        # 4. Apply PCA if requested
        if apply_pca_transform:
            X_transformed = self.apply_pca(X_scaled, n_components=n_components, fit=True)
        else:
            X_transformed = pd.DataFrame(X_scaled, columns=X_resampled.columns)
            logger.info("Skipping PCA transformation")

        # 5. Train-test split
        X_train, X_test, y_train, y_test = self.train_test_split_data(X_transformed, y_resampled, test_size=test_size)

        # 6. Save preprocessors if requested
        if save_preprocessors and output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            if self.scaler:
                scaler_path = output_path / "scaler.pkl"
                joblib.dump(self.scaler, scaler_path)
                logger.info(f"Saved scaler to {scaler_path}")

            if self.pca:
                pca_path = output_path / "pca.pkl"
                joblib.dump(self.pca, pca_path)
                logger.info(f"Saved PCA to {pca_path}")

        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETED")
        logger.info("=" * 80)

        return {
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "scaler": self.scaler,
            "pca": self.pca,
            "feature_names": self.feature_names,
            "n_features": X_train.shape[1],
        }

    def save_preprocessors(self, output_dir: str):
        """Save fitted scaler and PCA"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.scaler.save(output_path / "scaler.pkl")
        if self.pca:
            self.pca.save(output_path / "pca.pkl")

    def load_preprocessors(self, input_dir: str):
        """Load fitted scaler and PCA"""
        input_path = Path(input_dir)
        self.scaler.load(input_path / "scaler.pkl")
        if (input_path / "pca.pkl").exists():
            self.pca = DimensionalityReducer(n_components=5)
            self.pca.load(input_path / "pca.pkl")

    def transform_new_data(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform new data using fitted preprocessors"""
        X_encoded = self.encoder.one_hot_encode(X)

        # Align features
        if self.encoder.feature_names:
            X_encoded = self.encoder.align_features(X_encoded, self.encoder.feature_names)

        X_scaled = self.scale_features(X_encoded, fit=False)

        if self.pca:
            return self.apply_pca(X_scaled, fit=False)
        return pd.DataFrame(X_scaled, columns=X_encoded.columns)
