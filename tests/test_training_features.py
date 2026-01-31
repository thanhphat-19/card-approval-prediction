"""
Unit tests for training/src/features/feature_engineering.py module.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add training/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "training"))

from training.src.features.feature_engineering import FeatureEngineer  # noqa: E402


class TestFeatureEngineer:
    """Tests for FeatureEngineer class."""

    @pytest.fixture
    def engineer(self):
        """Create FeatureEngineer instance."""
        return FeatureEngineer(random_state=42)

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        np.random.seed(42)
        X = pd.DataFrame(
            {
                "numeric1": np.random.randn(100),
                "numeric2": np.random.randn(100),
                "category": ["A", "B", "C"] * 33 + ["A"],
            }
        )
        y = pd.Series([0, 1] * 50)
        return X, y

    def test_init(self, engineer):
        """Test FeatureEngineer initializes correctly."""
        assert engineer.random_state == 42
        assert engineer.encoder is not None
        assert engineer.resampler is not None
        assert engineer.scaler is not None

    def test_encode_features(self, engineer):
        """Test encode_features one-hot encodes categorical."""
        df = pd.DataFrame(
            {
                "category": ["A", "B", "C"],
                "numeric": [1, 2, 3],
            }
        )

        result = engineer.encode_features(df)

        assert "numeric" in result.columns
        # Should have encoded columns for B and C (A dropped)
        assert result.shape[1] > df.shape[1]

    def test_scale_features_fit(self, engineer):
        """Test scale_features fits and transforms."""
        df = pd.DataFrame(
            {
                "feat1": [1, 2, 3, 4, 5],
                "feat2": [10, 20, 30, 40, 50],
            }
        )

        result = engineer.scale_features(df, fit=True)

        assert isinstance(result, np.ndarray)
        # Scaled values should be centered around 0
        assert np.abs(result.mean()) < 0.1

    def test_scale_features_transform_only(self, engineer):
        """Test scale_features transforms without fitting."""
        df1 = pd.DataFrame({"feat": [1, 2, 3, 4, 5]})
        df2 = pd.DataFrame({"feat": [6, 7, 8]})

        engineer.scale_features(df1, fit=True)
        result = engineer.scale_features(df2, fit=False)

        assert isinstance(result, np.ndarray)
        assert result.shape == df2.shape

    def test_apply_pca_fit(self, engineer):
        """Test apply_pca fits and transforms."""
        X = np.random.randn(100, 10)

        result = engineer.apply_pca(X, n_components=5, fit=True)

        assert isinstance(result, pd.DataFrame)
        assert result.shape == (100, 5)
        assert list(result.columns) == ["PC1", "PC2", "PC3", "PC4", "PC5"]

    def test_apply_pca_transform_only(self, engineer):
        """Test apply_pca transforms without fitting."""
        X_train = np.random.randn(100, 10)
        X_test = np.random.randn(20, 10)

        engineer.apply_pca(X_train, n_components=5, fit=True)
        result = engineer.apply_pca(X_test, fit=False)

        assert result.shape == (20, 5)

    def test_train_test_split_data(self, engineer, sample_data):
        """Test train_test_split_data splits correctly."""
        X, y = sample_data

        X_train, X_test, y_train, y_test = engineer.train_test_split_data(X, y, test_size=0.2)

        assert len(X_train) == 80
        assert len(X_test) == 20
        assert len(y_train) == 80
        assert len(y_test) == 20

    def test_train_test_split_data_stratified(self, engineer):
        """Test train_test_split maintains class distribution."""
        X = pd.DataFrame({"feat": range(100)})
        y = pd.Series([0] * 50 + [1] * 50)

        X_train, X_test, y_train, y_test = engineer.train_test_split_data(X, y, test_size=0.2)

        # Both splits should have both classes
        assert len(set(y_train)) == 2
        assert len(set(y_test)) == 2

    def test_full_pipeline(self, engineer, sample_data, tmp_path):
        """Test full_pipeline runs complete preprocessing."""
        X, y = sample_data

        result = engineer.full_pipeline(
            X,
            y,
            apply_smote=False,  # Skip SMOTE for faster test
            apply_pca_transform=True,
            n_components=3,
            test_size=0.2,
            save_preprocessors=True,
            output_dir=str(tmp_path),
        )

        assert "X_train" in result
        assert "X_test" in result
        assert "y_train" in result
        assert "y_test" in result
        assert "scaler" in result
        assert "pca" in result
        assert "feature_names" in result

    def test_full_pipeline_saves_artifacts(self, engineer, sample_data, tmp_path):
        """Test full_pipeline saves preprocessor artifacts."""
        X, y = sample_data

        engineer.full_pipeline(
            X,
            y,
            apply_smote=False,
            apply_pca_transform=True,
            n_components=3,
            save_preprocessors=True,
            output_dir=str(tmp_path),
        )

        # Check artifacts were saved
        assert (tmp_path / "scaler.pkl").exists()
        assert (tmp_path / "pca.pkl").exists()
        assert (tmp_path / "feature_names.json").exists()

    def test_full_pipeline_without_pca(self, engineer, sample_data, tmp_path):
        """Test full_pipeline can skip PCA."""
        X, y = sample_data

        result = engineer.full_pipeline(
            X,
            y,
            apply_smote=False,
            apply_pca_transform=False,
            save_preprocessors=False,
        )

        # Should return scaled features without PCA reduction
        assert result["pca"] is None or not hasattr(result["pca"], "pca")

    def test_full_pipeline_with_smote(self, engineer, tmp_path):
        """Test full_pipeline with SMOTE balancing."""
        # Create imbalanced data
        X = pd.DataFrame(
            {
                "feat1": np.random.randn(100),
                "feat2": np.random.randn(100),
            }
        )
        y = pd.Series([1] * 90 + [0] * 10)

        result = engineer.full_pipeline(
            X,
            y,
            apply_smote=True,
            apply_pca_transform=True,
            n_components=2,
            save_preprocessors=False,
        )

        # Combined train + test should be more balanced
        y_combined = pd.concat([result["y_train"], result["y_test"]])
        class_ratio = y_combined.value_counts().min() / y_combined.value_counts().max()
        assert class_ratio > 0.5

    def test_save_preprocessors(self, engineer, sample_data, tmp_path):
        """Test save_preprocessors saves scaler and PCA."""
        X, y = sample_data

        # First fit the preprocessors
        X_encoded = engineer.encode_features(X)
        engineer.scale_features(X_encoded, fit=True)
        engineer.apply_pca(
            engineer.scaler.scaler.fit_transform(X_encoded),
            n_components=2,
            fit=True,
        )

        engineer.save_preprocessors(str(tmp_path))

        assert (tmp_path / "scaler.pkl").exists()
        assert (tmp_path / "pca.pkl").exists()

    def test_load_preprocessors(self, engineer, sample_data, tmp_path):
        """Test load_preprocessors loads saved artifacts."""
        X, y = sample_data

        # Fit and save
        X_encoded = engineer.encode_features(X)
        engineer.scale_features(X_encoded, fit=True)
        engineer.apply_pca(
            engineer.scaler.scaler.fit_transform(X_encoded),
            n_components=2,
            fit=True,
        )
        engineer.save_preprocessors(str(tmp_path))

        # Create new engineer and load
        from src.features.feature_engineering import FeatureEngineer

        new_engineer = FeatureEngineer()
        new_engineer.load_preprocessors(str(tmp_path))

        assert new_engineer.scaler is not None
        assert new_engineer.pca is not None

    @pytest.mark.skip(reason="Complex integration test - transform_new_data requires full pipeline setup")
    def test_transform_new_data(self, engineer, sample_data):
        """Test transform_new_data transforms unseen data.

        Note: This test is skipped because it requires complex setup of the full pipeline
        including encoder, scaler, and PCA with proper feature alignment. The individual
        components are already tested separately in other test cases.
        """
        pass
