"""
Unit tests for training/src/utils modules.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

# Add training/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "training"))

from src.utils.dimensionality import DimensionalityReducer  # noqa: E402
from src.utils.encoders import FeatureEncoder  # noqa: E402
from src.utils.helpers import ensure_dir, load_config, save_config  # noqa: E402
from src.utils.metrics import calculate_metrics, find_optimal_threshold, get_classification_report  # noqa: E402
from src.utils.resampling import Resampler  # noqa: E402
from src.utils.scalers import FeatureScaler  # noqa: E402


class TestFeatureEncoder:
    """Tests for FeatureEncoder class."""

    @pytest.fixture
    def encoder(self):
        """Create FeatureEncoder instance."""
        return FeatureEncoder()

    def test_init(self, encoder):
        """Test FeatureEncoder initializes correctly."""
        assert encoder.feature_names is None

    def test_one_hot_encode(self, encoder):
        """Test one_hot_encode encodes categorical features."""
        df = pd.DataFrame(
            {
                "category": ["A", "B", "A", "C"],
                "numeric": [1, 2, 3, 4],
            }
        )

        result = encoder.one_hot_encode(df)

        # Should have numeric + one-hot encoded columns
        assert "numeric" in result.columns
        assert result.shape[1] > df.shape[1]  # More columns after encoding

    def test_one_hot_encode_drop_first(self, encoder):
        """Test one_hot_encode drops first category by default."""
        df = pd.DataFrame(
            {
                "category": ["A", "B", "C"],
            }
        )

        result = encoder.one_hot_encode(df, drop_first=True)

        # Should have n-1 columns for n categories
        assert result.shape[1] == 2  # B and C, not A

    def test_one_hot_encode_stores_feature_names(self, encoder):
        """Test one_hot_encode stores feature names."""
        df = pd.DataFrame(
            {
                "category": ["A", "B"],
                "numeric": [1, 2],
            }
        )

        encoder.one_hot_encode(df)

        assert encoder.feature_names is not None
        assert len(encoder.feature_names) > 0

    def test_align_features_adds_missing(self, encoder):
        """Test align_features adds missing columns."""
        df = pd.DataFrame({"feat1": [1], "feat2": [2]})
        reference = ["feat1", "feat2", "feat3"]

        result = encoder.align_features(df, reference)

        assert "feat3" in result.columns
        assert result["feat3"].iloc[0] == 0

    def test_align_features_keeps_order(self, encoder):
        """Test align_features maintains reference order."""
        df = pd.DataFrame({"feat2": [2], "feat1": [1]})
        reference = ["feat1", "feat2"]

        result = encoder.align_features(df, reference)

        assert list(result.columns) == reference


class TestFeatureScaler:
    """Tests for FeatureScaler class."""

    @pytest.fixture
    def scaler(self):
        """Create FeatureScaler instance."""

        return FeatureScaler(method="standard")

    def test_init_standard(self, scaler):
        """Test FeatureScaler initializes with StandardScaler."""

        assert isinstance(scaler.scaler, StandardScaler)

    def test_init_minmax(self):
        """Test FeatureScaler initializes with MinMaxScaler."""
        scaler = FeatureScaler(method="minmax")
        assert isinstance(scaler.scaler, MinMaxScaler)

    def test_init_robust(self):
        """Test FeatureScaler initializes with RobustScaler."""
        scaler = FeatureScaler(method="robust")
        assert isinstance(scaler.scaler, RobustScaler)

    def test_init_invalid_method(self):
        """Test FeatureScaler raises for invalid method."""
        with pytest.raises(ValueError):
            FeatureScaler(method="invalid")

    def test_fit_transform(self, scaler):
        """Test fit_transform scales data."""
        df = pd.DataFrame(
            {
                "feat1": [1, 2, 3, 4, 5],
                "feat2": [10, 20, 30, 40, 50],
            }
        )

        result = scaler.fit_transform(df)

        assert isinstance(result, np.ndarray)
        assert result.shape == df.shape
        # Standard scaling should have mean ~0
        assert np.abs(result.mean()) < 0.1

    def test_transform_after_fit(self, scaler):
        """Test transform uses fitted scaler."""
        df1 = pd.DataFrame({"feat": [1, 2, 3, 4, 5]})
        df2 = pd.DataFrame({"feat": [6, 7, 8]})

        scaler.fit_transform(df1)
        result = scaler.transform(df2)

        assert isinstance(result, np.ndarray)
        assert result.shape == df2.shape

    def test_transform_before_fit_raises(self):
        """Test transform raises if not fitted."""

        scaler = FeatureScaler(method="standard")
        scaler.scaler = None

        with pytest.raises(ValueError):
            scaler.transform(pd.DataFrame({"feat": [1]}))


class TestMetrics:
    """Tests for metrics module."""

    @pytest.fixture
    def y_true(self):
        """True labels."""
        return pd.Series([0, 0, 1, 1, 1, 0, 1, 0])

    @pytest.fixture
    def y_pred(self):
        """Predicted labels."""
        return np.array([0, 1, 1, 1, 0, 0, 1, 0])

    @pytest.fixture
    def y_pred_proba(self):
        """Predicted probabilities."""
        return np.array([0.2, 0.6, 0.8, 0.9, 0.4, 0.3, 0.7, 0.1])

    def test_calculate_metrics(self, y_true, y_pred):
        """Test calculate_metrics returns correct metrics."""

        result = calculate_metrics(y_true, y_pred)

        assert "accuracy" in result
        assert "precision" in result
        assert "recall" in result
        assert "f1_score" in result
        assert 0 <= result["accuracy"] <= 1

    def test_calculate_metrics_with_proba(self, y_true, y_pred, y_pred_proba):
        """Test calculate_metrics includes ROC AUC with probabilities."""

        result = calculate_metrics(y_true, y_pred, y_pred_proba)

        assert "roc_auc" in result
        assert 0 <= result["roc_auc"] <= 1

    def test_get_classification_report(self, y_true, y_pred):
        """Test get_classification_report returns string report."""

        result = get_classification_report(y_true, y_pred)

        assert isinstance(result, str)
        assert "precision" in result.lower()
        assert "recall" in result.lower()

    def test_find_optimal_threshold_f1(self, y_true, y_pred_proba):
        """Test find_optimal_threshold finds best F1 threshold."""

        result = find_optimal_threshold(y_true, y_pred_proba, metric="f1")

        assert 0.1 <= result <= 1.0

    def test_find_optimal_threshold_precision(self, y_true, y_pred_proba):
        """Test find_optimal_threshold with precision metric."""

        result = find_optimal_threshold(y_true, y_pred_proba, metric="precision")

        assert 0.1 <= result <= 1.0

    def test_find_optimal_threshold_recall(self, y_true, y_pred_proba):
        """Test find_optimal_threshold with recall metric."""

        result = find_optimal_threshold(y_true, y_pred_proba, metric="recall")

        assert 0.1 <= result <= 1.0

    def test_find_optimal_threshold_invalid_metric(self, y_true, y_pred_proba):
        """Test find_optimal_threshold raises for invalid metric."""

        with pytest.raises(ValueError):
            find_optimal_threshold(y_true, y_pred_proba, metric="invalid")


class TestHelpers:
    """Tests for helpers module."""

    def test_load_config(self, tmp_path):
        """Test load_config loads YAML file."""

        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value\nnested:\n  inner: 123")

        result = load_config(str(config_file))

        assert result["key"] == "value"
        assert result["nested"]["inner"] == 123

    def test_save_config(self, tmp_path):
        """Test save_config saves YAML file."""

        config = {"key": "value", "number": 42}
        output_file = tmp_path / "output.yaml"

        save_config(config, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "key: value" in content

    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test ensure_dir creates directory."""

        new_dir = tmp_path / "new" / "nested" / "dir"

        ensure_dir(str(new_dir))

        assert new_dir.exists()

    def test_ensure_dir_existing(self, tmp_path):
        """Test ensure_dir handles existing directory."""

        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        ensure_dir(str(existing_dir))  # Should not raise

        assert existing_dir.exists()


class TestDimensionalityReducer:
    """Tests for DimensionalityReducer class."""

    @pytest.fixture
    def reducer(self):
        """Create DimensionalityReducer instance."""

        return DimensionalityReducer(n_components=3, random_state=42)

    def test_init(self, reducer):
        """Test DimensionalityReducer initializes correctly."""
        assert reducer.n_components == 3
        assert reducer.random_state == 42

    def test_fit_transform(self, reducer):
        """Test fit_transform reduces dimensionality."""
        X = np.random.randn(100, 10)

        result = reducer.fit_transform(X)

        assert isinstance(result, pd.DataFrame)
        assert result.shape == (100, 3)
        assert list(result.columns) == ["PC1", "PC2", "PC3"]

    def test_transform_after_fit(self, reducer):
        """Test transform uses fitted PCA."""
        X_train = np.random.randn(100, 10)
        X_test = np.random.randn(20, 10)

        reducer.fit_transform(X_train)
        result = reducer.transform(X_test)

        assert result.shape == (20, 3)

    def test_save_and_load(self, reducer, tmp_path):
        """Test save and load PCA model."""
        X = np.random.randn(100, 10)
        reducer.fit_transform(X)

        filepath = tmp_path / "pca.pkl"
        reducer.save(str(filepath))

        assert filepath.exists()

        # Create new reducer and load

        new_reducer = DimensionalityReducer(n_components=3)
        new_reducer.load(str(filepath))

        # Should produce same results
        X_test = np.random.randn(10, 10)
        result1 = reducer.transform(X_test)
        result2 = new_reducer.transform(X_test)
        np.testing.assert_array_almost_equal(result1.values, result2.values)


class TestResampler:
    """Tests for Resampler class."""

    @pytest.fixture
    def resampler(self):
        """Create Resampler instance."""

        return Resampler(random_state=42)

    @pytest.fixture
    def imbalanced_data(self):
        """Create imbalanced dataset."""
        np.random.seed(42)
        X = pd.DataFrame(
            {
                "feat1": np.random.randn(100),
                "feat2": np.random.randn(100),
            }
        )
        # Highly imbalanced: 90 class 1, 10 class 0
        y = pd.Series([1] * 90 + [0] * 10)
        return X, y

    def test_init(self, resampler):
        """Test Resampler initializes correctly."""
        assert resampler.random_state == 42

    def test_apply_smote_tomek_balances(self, resampler, imbalanced_data):
        """Test apply_smote_tomek balances dataset."""
        X, y = imbalanced_data

        X_resampled, y_resampled = resampler.apply_smote_tomek(X, y)

        # Class distribution should be more balanced
        class_counts = pd.Series(y_resampled).value_counts()
        ratio = class_counts.min() / class_counts.max()
        assert ratio > 0.5  # At least 50% balance

    def test_apply_smote_tomek_returns_dataframe(self, resampler, imbalanced_data):
        """Test apply_smote_tomek returns DataFrame."""
        X, y = imbalanced_data

        X_resampled, y_resampled = resampler.apply_smote_tomek(X, y)

        assert isinstance(X_resampled, pd.DataFrame)
        assert list(X_resampled.columns) == list(X.columns)

    def test_apply_smote(self, resampler, imbalanced_data):
        """Test apply_smote balances dataset."""
        X, y = imbalanced_data

        X_resampled, y_resampled = resampler.apply_smote(X, y)

        # Classes should be balanced
        class_counts = pd.Series(y_resampled).value_counts()
        assert class_counts[0] == class_counts[1]
