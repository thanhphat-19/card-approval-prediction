"""
Unit tests for app/services/model_service.py module.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


class TestModelService:
    """Tests for ModelService class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies for ModelService."""
        with patch("app.services.model_service.get_settings") as mock_settings, patch(
            "app.services.model_service.setup_gcs_credentials"
        ) as mock_gcs, patch("app.services.model_service.setup_mlflow_tracking") as mock_mlflow_setup, patch(
            "app.services.model_service.get_latest_model_version"
        ) as mock_version, patch(
            "app.services.model_service.mlflow"
        ) as mock_mlflow, patch(
            "app.services.model_service.load_model_with_flavor"
        ) as mock_load_flavor:
            settings = MagicMock()
            settings.MLFLOW_TRACKING_URI = "http://mlflow:5000"
            settings.MODEL_NAME = "test_model"
            settings.MODEL_STAGE = "Production"
            settings.MODEL_PATH = None  # Force MLflow loading path
            settings.GOOGLE_APPLICATION_CREDENTIALS = ""
            mock_settings.return_value = settings

            # Mock MLflow client
            mock_client = MagicMock()
            mock_mlflow_setup.return_value = mock_client

            mock_version.return_value = ("1", "test-run-id")

            mock_pyfunc_model = MagicMock()
            mock_pyfunc_model.predict.return_value = np.array([1])
            mock_mlflow.pyfunc.load_model.return_value = mock_pyfunc_model

            mock_sklearn_model = MagicMock()
            mock_sklearn_model.predict_proba.return_value = np.array([[0.2, 0.8]])
            mock_load_flavor.return_value = mock_sklearn_model

            yield {
                "settings": mock_settings,
                "gcs": mock_gcs,
                "mlflow_setup": mock_mlflow_setup,
                "version": mock_version,
                "mlflow": mock_mlflow,
                "load_flavor": mock_load_flavor,
                "pyfunc_model": mock_pyfunc_model,
                "sklearn_model": mock_sklearn_model,
            }

    def test_init_loads_model(self, mock_dependencies):
        """Test ModelService initializes and loads model."""
        from app.services.model_service import ModelService

        service = ModelService()

        assert service.model is not None
        assert service.version == "1"
        assert service.run_id == "test-run-id"

    def test_init_sets_up_credentials(self, mock_dependencies):
        """Test ModelService sets up GCS credentials."""
        from app.services.model_service import ModelService

        ModelService()

        mock_dependencies["gcs"].assert_called_once()

    def test_predict_returns_prediction(self, mock_dependencies):
        """Test predict method returns model prediction."""
        from app.services.model_service import ModelService

        service = ModelService()
        features = pd.DataFrame({"PC1": [0.5], "PC2": [0.3]})

        result = service.predict(features)

        assert result[0] == 1
        mock_dependencies["pyfunc_model"].predict.assert_called_once()

    def test_predict_raises_when_model_not_loaded(self, mock_dependencies):
        """Test predict raises error when model is None."""
        from app.services.model_service import ModelService

        service = ModelService()
        service.model = None  # Simulate unloaded model

        with pytest.raises(RuntimeError) as exc_info:
            service.predict(pd.DataFrame({"PC1": [0.5]}))

        assert "Model not loaded" in str(exc_info.value)

    def test_predict_proba_returns_probabilities(self, mock_dependencies):
        """Test predict_proba returns probability array."""
        from app.services.model_service import ModelService

        service = ModelService()
        features = pd.DataFrame({"PC1": [0.5], "PC2": [0.3]})

        result = service.predict_proba(features)

        assert result is not None
        np.testing.assert_array_almost_equal(result, [[0.2, 0.8]])

    def test_predict_proba_returns_none_when_unavailable(self, mock_dependencies):
        """Test predict_proba returns None when sklearn_model is None."""
        from app.services.model_service import ModelService

        service = ModelService()
        service.sklearn_model = None

        result = service.predict_proba(pd.DataFrame({"PC1": [0.5]}))

        assert result is None

    def test_predict_proba_returns_none_on_error(self, mock_dependencies):
        """Test predict_proba returns None on exception."""
        from app.services.model_service import ModelService

        service = ModelService()
        service.sklearn_model.predict_proba.side_effect = Exception("Error")

        result = service.predict_proba(pd.DataFrame({"PC1": [0.5]}))

        assert result is None

    def test_get_model_info(self, mock_dependencies):
        """Test get_model_info returns correct information."""
        from app.services.model_service import ModelService

        service = ModelService()

        info = service.get_model_info()

        assert info["name"] == "test_model"
        assert info["stage"] == "Production"
        assert info["version"] == "1"
        assert info["run_id"] == "test-run-id"
        assert info["loaded"] is True


class TestGetModelService:
    """Tests for get_model_service function."""

    @patch("app.services.model_service.ModelService")
    def test_returns_model_service_instance(self, mock_model_service):
        """Test get_model_service returns ModelService instance."""
        from app.services.model_service import get_model_service

        # Clear cache
        get_model_service.cache_clear()

        mock_instance = MagicMock()
        mock_model_service.return_value = mock_instance

        result = get_model_service()

        assert result == mock_instance

    @patch("app.services.model_service.ModelService")
    def test_caches_instance(self, mock_model_service):
        """Test get_model_service caches the instance."""
        from app.services.model_service import get_model_service

        get_model_service.cache_clear()

        mock_instance = MagicMock()
        mock_model_service.return_value = mock_instance

        result1 = get_model_service()
        result2 = get_model_service()

        assert result1 is result2
        # ModelService should only be instantiated once
        assert mock_model_service.call_count == 1
