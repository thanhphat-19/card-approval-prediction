"""
Unit tests for training/src/utils/mlflow_registry.py module.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add training/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "training"))

from src.utils.mlflow_registry import MLflowRegistry  # noqa: E402


class TestMLflowRegistry:
    """Tests for MLflowRegistry class."""

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_init_sets_tracking_uri(self, mock_mlflow, mock_client):
        """Test initialization sets tracking URI."""
        registry = MLflowRegistry(tracking_uri="http://mlflow:5000")

        assert registry.tracking_uri == "http://mlflow:5000"
        mock_mlflow.set_tracking_uri.assert_called_once_with("http://mlflow:5000")

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_init_creates_client(self, mock_mlflow, mock_client):
        """Test initialization creates MLflow client."""
        registry = MLflowRegistry()

        assert registry.client is not None
        mock_client.assert_called_once()

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_register_model_success(self, mock_mlflow, mock_client):
        """Test register_model successfully registers model."""
        mock_version = MagicMock()
        mock_version.version = "1"
        mock_mlflow.register_model.return_value = mock_version

        registry = MLflowRegistry()
        result = registry.register_model(run_id="test-run-id", model_name="test_model")

        assert result["name"] == "test_model"
        assert result["version"] == "1"
        assert result["run_id"] == "test-run-id"
        mock_mlflow.register_model.assert_called_once()

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_register_model_custom_artifact_path(self, mock_mlflow, mock_client):
        """Test register_model with custom artifact path."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_version = MagicMock()
        mock_version.version = "2"
        mock_mlflow.register_model.return_value = mock_version

        registry = MLflowRegistry()
        registry.register_model(run_id="test-run", model_name="custom_model", artifact_path="custom_path")

        # Check model URI includes custom path
        call_args = mock_mlflow.register_model.call_args[0]
        assert "custom_path" in call_args[0]

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_transition_model_stage_to_production(self, mock_mlflow, mock_client_class):
        """Test transition_model_stage moves to production."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        registry.transition_model_stage(model_name="test_model", version=1, stage="Production")

        mock_client.transition_model_version_stage.assert_called_once_with(
            name="test_model", version=1, stage="Production", archive_existing_versions=True
        )

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_transition_model_stage_to_staging(self, mock_mlflow, mock_client_class):
        """Test transition_model_stage moves to staging."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        registry.transition_model_stage(model_name="test_model", version=2, stage="Staging")

        call_kwargs = mock_client.transition_model_version_stage.call_args[1]
        assert call_kwargs["stage"] == "Staging"

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_transition_archives_existing(self, mock_mlflow, mock_client_class):
        """Test transition archives existing versions."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        registry.transition_model_stage("model", 1, "Production")

        call_kwargs = mock_client.transition_model_version_stage.call_args[1]
        assert call_kwargs["archive_existing_versions"] is True

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_load_model_from_registry_production(self, mock_mlflow, mock_client):
        """Test load_model_from_registry loads from production."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_model = MagicMock()
        mock_mlflow.pyfunc.load_model.return_value = mock_model

        registry = MLflowRegistry()
        result = registry.load_model_from_registry("test_model", "Production")

        assert result == mock_model
        mock_mlflow.pyfunc.load_model.assert_called_once_with("models:/test_model/Production")

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_load_model_from_registry_staging(self, mock_mlflow, mock_client):
        """Test load_model_from_registry loads from staging."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_model = MagicMock()
        mock_mlflow.pyfunc.load_model.return_value = mock_model

        registry = MLflowRegistry()
        registry.load_model_from_registry("staging_model", "Staging")

        mock_mlflow.pyfunc.load_model.assert_called_once_with("models:/staging_model/Staging")

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_get_latest_version(self, mock_mlflow, mock_client_class):
        """Test get_latest_version returns latest version number."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_version1 = MagicMock()
        mock_version1.version = "1"
        mock_version2 = MagicMock()
        mock_version2.version = "3"

        mock_client.get_latest_versions.return_value = [mock_version1, mock_version2]
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        result = registry.get_latest_version("test_model")

        assert result == 3
        mock_client.get_latest_versions.assert_called_once()

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_get_latest_version_with_stage_filter(self, mock_mlflow, mock_client_class):
        """Test get_latest_version with stage filter."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_version = MagicMock()
        mock_version.version = "2"

        mock_client.get_latest_versions.return_value = [mock_version]
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        result = registry.get_latest_version("test_model", stage="Production")

        assert result == 2
        call_args = mock_client.get_latest_versions.call_args
        assert call_args[0][0] == "test_model"
        assert call_args[1]["stages"] == ["Production"]

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_get_latest_version_raises_when_no_versions(self, mock_mlflow, mock_client_class):
        """Test get_latest_version raises error when no versions found."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_client.get_latest_versions.return_value = []
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()

        with pytest.raises(ValueError, match="No versions found"):
            registry.get_latest_version("nonexistent_model")

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_list_registered_models(self, mock_mlflow, mock_client_class):
        """Test list_registered_models returns all models."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.name = "test_model"
        mock_model.creation_timestamp = 123456
        mock_model.last_updated_timestamp = 123457
        mock_model.description = "Test model"

        mock_version = MagicMock()
        mock_version.version = "1"
        mock_version.current_stage = "Production"
        mock_version.run_id = "run-123"
        mock_model.latest_versions = [mock_version]

        mock_client.search_registered_models.return_value = [mock_model]
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        result = registry.list_registered_models()

        assert len(result) == 1
        assert result[0]["name"] == "test_model"
        assert len(result[0]["latest_versions"]) == 1

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_add_model_description(self, mock_mlflow, mock_client_class):
        """Test add_model_description adds description to model."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        registry.add_model_description("test_model", "Model description")

        mock_client.update_registered_model.assert_called_once_with(name="test_model", description="Model description")

    @patch("src.utils.mlflow_registry.MlflowClient")
    @patch("src.utils.mlflow_registry.mlflow")
    def test_add_version_description(self, mock_mlflow, mock_client_class):
        """Test add_version_description adds description to version."""
        from src.utils.mlflow_registry import MLflowRegistry

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        registry = MLflowRegistry()
        registry.add_version_description("test_model", 1, "Version description")

        mock_client.update_model_version.assert_called_once_with(
            name="test_model", version=1, description="Version description"
        )
