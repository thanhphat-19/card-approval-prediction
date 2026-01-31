"""
Unit tests for app/services/preprocessing_service.py module.
"""

from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pandas as pd
import pytest


class TestPreprocessingService:
    """Tests for PreprocessingService class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies for PreprocessingService."""
        with patch("app.services.preprocessing_service.get_settings") as mock_settings, patch(
            "app.services.preprocessing_service.mlflow"
        ) as mock_mlflow, patch("app.services.preprocessing_service.joblib") as mock_joblib, patch(
            "builtins.open", mock_open(read_data='{"feature_names": ["feat1", "feat2", "feat3"]}')
        ):
            settings = MagicMock()
            settings.MLFLOW_TRACKING_URI = "http://mlflow:5000"
            mock_settings.return_value = settings

            mock_mlflow.artifacts.download_artifacts.return_value = "/tmp/mock_artifacts"

            mock_scaler = MagicMock()
            mock_scaler.transform.return_value = np.array([[0.5, -0.3, 0.1]])

            mock_pca = MagicMock()
            mock_pca.transform.return_value = np.array([[0.5, -0.3, 0.1]])

            mock_joblib.load.side_effect = [mock_scaler, mock_pca]

            yield {
                "settings": mock_settings,
                "mlflow": mock_mlflow,
                "joblib": mock_joblib,
                "scaler": mock_scaler,
                "pca": mock_pca,
            }

    def test_init_loads_artifacts(self, mock_dependencies):
        """Test PreprocessingService loads artifacts on init."""
        from app.services.preprocessing_service import PreprocessingService

        service = PreprocessingService(run_id="test-run-id")

        assert service.scaler is not None
        assert service.pca is not None
        assert service.feature_names is not None

    def test_init_sets_mlflow_tracking_uri(self, mock_dependencies):
        """Test PreprocessingService sets MLflow tracking URI."""
        from app.services.preprocessing_service import PreprocessingService

        PreprocessingService(run_id="test-run-id")

        mock_dependencies["mlflow"].set_tracking_uri.assert_called_once()

    def test_align_features_adds_missing_columns(self, mock_dependencies):
        """Test align_features adds missing columns with zeros."""
        from app.services.preprocessing_service import PreprocessingService

        service = PreprocessingService(run_id="test-run-id")

        # DataFrame with some features
        df = pd.DataFrame({"feat1": [1.0], "feat2": [2.0]})
        reference = ["feat1", "feat2", "feat3", "feat4"]

        result = service.align_features(df, reference)

        assert list(result.columns) == reference
        assert result["feat3"].iloc[0] == 0
        assert result["feat4"].iloc[0] == 0

    def test_align_features_reorders_columns(self, mock_dependencies):
        """Test align_features reorders columns to match reference."""
        from app.services.preprocessing_service import PreprocessingService

        service = PreprocessingService(run_id="test-run-id")

        df = pd.DataFrame({"feat2": [2.0], "feat1": [1.0]})
        reference = ["feat1", "feat2"]

        result = service.align_features(df, reference)

        assert list(result.columns) == reference

    def test_preprocess_drops_id_column(self, mock_dependencies):
        """Test preprocess drops ID column."""
        from app.services.preprocessing_service import PreprocessingService

        service = PreprocessingService(run_id="test-run-id")
        service.feature_names = ["feat1", "feat2"]
        service.scaler = mock_dependencies["scaler"]
        service.pca = mock_dependencies["pca"]

        df = pd.DataFrame(
            {
                "ID": [123],
                "feat1": [1.0],
                "feat2": [2.0],
            }
        )

        # The preprocess method will drop ID and process
        result = service.preprocess(df)

        # Result should not contain ID
        assert "ID" not in result.columns

    def test_preprocess_returns_pca_dataframe(self, mock_dependencies):
        """Test preprocess returns DataFrame with PC columns."""
        from app.services.preprocessing_service import PreprocessingService

        service = PreprocessingService(run_id="test-run-id")
        service.feature_names = ["feat1", "feat2"]
        service.scaler = mock_dependencies["scaler"]
        service.pca = mock_dependencies["pca"]

        df = pd.DataFrame({"feat1": [1.0], "feat2": [2.0]})

        result = service.preprocess(df)

        assert isinstance(result, pd.DataFrame)
        # Should have PC columns
        assert all(col.startswith("PC") for col in result.columns)


class TestGetPreprocessingService:
    """Tests for get_preprocessing_service function."""

    @patch("app.services.preprocessing_service.PreprocessingService")
    def test_returns_preprocessing_service(self, mock_service):
        """Test get_preprocessing_service returns PreprocessingService."""
        from app.services.preprocessing_service import get_preprocessing_service

        get_preprocessing_service.cache_clear()

        mock_instance = MagicMock()
        mock_service.return_value = mock_instance

        result = get_preprocessing_service(run_id="test-run")

        assert result == mock_instance

    @patch("app.services.preprocessing_service.PreprocessingService")
    def test_caches_instance(self, mock_service):
        """Test get_preprocessing_service caches the instance."""
        from app.services.preprocessing_service import get_preprocessing_service

        get_preprocessing_service.cache_clear()

        mock_instance = MagicMock()
        mock_service.return_value = mock_instance

        result1 = get_preprocessing_service(run_id="test-run")
        result2 = get_preprocessing_service(run_id="test-run")

        assert result1 is result2
        assert mock_service.call_count == 1
