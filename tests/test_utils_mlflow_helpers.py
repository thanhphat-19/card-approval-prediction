"""
Unit tests for app/utils/mlflow_helpers.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.utils.mlflow_helpers import (
    check_mlflow_connection,
    get_latest_model_version,
    load_model_with_flavor,
    setup_mlflow_tracking,
)


class TestSetupMlflowTracking:
    """Tests for setup_mlflow_tracking function."""

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_sets_tracking_uri(self, mock_mlflow):
        """Test tracking URI is set correctly."""
        tracking_uri = "http://mlflow:5000"

        setup_mlflow_tracking(tracking_uri)

        mock_mlflow.set_tracking_uri.assert_called_once_with(tracking_uri)

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_returns_mlflow_client(self, mock_mlflow):
        """Test returns MlflowClient instance."""
        mock_client = MagicMock()
        mock_mlflow.tracking.MlflowClient.return_value = mock_client

        result = setup_mlflow_tracking("http://localhost:5000")

        assert result == mock_client
        mock_mlflow.tracking.MlflowClient.assert_called_once()


class TestGetLatestModelVersion:
    """Tests for get_latest_model_version function."""

    def test_returns_version_and_run_id(self):
        """Test returns tuple of version and run_id."""
        mock_client = MagicMock()
        mock_version = MagicMock()
        mock_version.version = "5"
        mock_version.run_id = "test-run-id-123"
        mock_version.current_stage = "Production"

        mock_client.search_model_versions.return_value = [mock_version]

        version, run_id = get_latest_model_version(
            client=mock_client,
            model_name="test_model",
            stage="Production",
        )

        assert version == "5"
        assert run_id == "test-run-id-123"

    def test_filters_by_stage(self):
        """Test filters versions by stage."""
        mock_client = MagicMock()

        # Multiple versions with different stages
        prod_version = MagicMock()
        prod_version.version = "3"
        prod_version.run_id = "prod-run"
        prod_version.current_stage = "Production"

        staging_version = MagicMock()
        staging_version.version = "4"
        staging_version.run_id = "staging-run"
        staging_version.current_stage = "Staging"

        mock_client.search_model_versions.return_value = [prod_version, staging_version]

        version, run_id = get_latest_model_version(
            client=mock_client,
            model_name="test_model",
            stage="Production",
        )

        assert version == "3"
        assert run_id == "prod-run"

    def test_returns_latest_version(self):
        """Test returns the latest (highest) version number."""
        mock_client = MagicMock()

        # Multiple Production versions
        version1 = MagicMock()
        version1.version = "1"
        version1.run_id = "run-1"
        version1.current_stage = "Production"

        version3 = MagicMock()
        version3.version = "3"
        version3.run_id = "run-3"
        version3.current_stage = "Production"

        version2 = MagicMock()
        version2.version = "2"
        version2.run_id = "run-2"
        version2.current_stage = "Production"

        mock_client.search_model_versions.return_value = [version1, version3, version2]

        version, run_id = get_latest_model_version(
            client=mock_client,
            model_name="test_model",
            stage="Production",
        )

        assert version == "3"
        assert run_id == "run-3"

    def test_raises_when_no_versions_found(self):
        """Test raises ValueError when no versions found for stage."""
        mock_client = MagicMock()
        mock_client.search_model_versions.return_value = []

        with pytest.raises(ValueError) as exc_info:
            get_latest_model_version(
                client=mock_client,
                model_name="test_model",
                stage="Production",
            )

        assert "No model version found" in str(exc_info.value)

    def test_raises_when_no_matching_stage(self):
        """Test raises ValueError when no versions match stage."""
        mock_client = MagicMock()

        staging_version = MagicMock()
        staging_version.version = "1"
        staging_version.current_stage = "Staging"

        mock_client.search_model_versions.return_value = [staging_version]

        with pytest.raises(ValueError):
            get_latest_model_version(
                client=mock_client,
                model_name="test_model",
                stage="Production",  # No Production versions
            )


class TestLoadModelWithFlavor:
    """Tests for load_model_with_flavor function."""

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_tries_xgboost_first(self, mock_mlflow):
        """Test tries XGBoost flavor first."""
        mock_model = MagicMock()
        mock_mlflow.xgboost.load_model.return_value = mock_model

        result = load_model_with_flavor("models:/test/1")

        assert result == mock_model
        mock_mlflow.xgboost.load_model.assert_called_once_with("models:/test/1")

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_tries_lightgbm_when_xgboost_fails(self, mock_mlflow):
        """Test tries LightGBM when XGBoost fails."""
        mock_model = MagicMock()
        mock_mlflow.xgboost.load_model.side_effect = Exception("Not XGBoost")
        mock_mlflow.lightgbm.load_model.return_value = mock_model

        result = load_model_with_flavor("models:/test/1")

        assert result == mock_model

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_tries_catboost_when_lightgbm_fails(self, mock_mlflow):
        """Test tries CatBoost when LightGBM fails."""
        mock_model = MagicMock()
        mock_mlflow.xgboost.load_model.side_effect = Exception("Not XGBoost")
        mock_mlflow.lightgbm.load_model.side_effect = Exception("Not LightGBM")
        mock_mlflow.catboost.load_model.return_value = mock_model

        result = load_model_with_flavor("models:/test/1")

        assert result == mock_model

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_tries_sklearn_when_others_fail(self, mock_mlflow):
        """Test tries sklearn when other flavors fail."""
        mock_model = MagicMock()
        mock_mlflow.xgboost.load_model.side_effect = Exception("Not XGBoost")
        mock_mlflow.lightgbm.load_model.side_effect = Exception("Not LightGBM")
        mock_mlflow.catboost.load_model.side_effect = Exception("Not CatBoost")
        mock_mlflow.sklearn.load_model.return_value = mock_model

        result = load_model_with_flavor("models:/test/1")

        assert result == mock_model

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_returns_none_when_all_fail(self, mock_mlflow):
        """Test returns None when all flavors fail."""
        mock_mlflow.xgboost.load_model.side_effect = Exception("Not XGBoost")
        mock_mlflow.lightgbm.load_model.side_effect = Exception("Not LightGBM")
        mock_mlflow.catboost.load_model.side_effect = Exception("Not CatBoost")
        mock_mlflow.sklearn.load_model.side_effect = Exception("Not sklearn")

        result = load_model_with_flavor("models:/test/1")

        assert result is None


class TestCheckMlflowConnection:
    """Tests for check_mlflow_connection function."""

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_returns_true_on_success(self, mock_mlflow):
        """Test returns True when connection succeeds."""
        mock_mlflow.search_experiments.return_value = []

        result = check_mlflow_connection("http://mlflow:5000")

        assert result is True

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_returns_false_on_failure(self, mock_mlflow):
        """Test returns False when connection fails."""
        mock_mlflow.search_experiments.side_effect = Exception("Connection refused")

        result = check_mlflow_connection("http://mlflow:5000")

        assert result is False

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_sets_tracking_uri(self, mock_mlflow):
        """Test sets tracking URI before checking."""
        mock_mlflow.search_experiments.return_value = []
        tracking_uri = "http://custom-mlflow:5000"

        check_mlflow_connection(tracking_uri)

        mock_mlflow.set_tracking_uri.assert_called_with(tracking_uri)

    @patch("app.utils.mlflow_helpers.mlflow")
    def test_logs_warning_on_failure(self, mock_mlflow):
        """Test logs warning when connection fails."""
        mock_mlflow.search_experiments.side_effect = Exception("Failed")

        with patch("app.utils.mlflow_helpers.logger") as mock_logger:
            check_mlflow_connection("http://mlflow:5000")
            mock_logger.warning.assert_called()
