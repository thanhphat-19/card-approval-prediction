"""
Unit tests for app/routers/health.py module.
"""

from datetime import datetime
from unittest.mock import patch

from app.routers.health import health_check, liveness_check, readiness_check
from app.schemas.health import HealthResponse


class TestHealthCheck:
    """Tests for health_check endpoint function."""

    @patch("app.routers.health.check_mlflow_connection")
    def test_returns_health_response(self, mock_check):
        """Test health_check returns HealthResponse."""
        mock_check.return_value = True

        result = health_check()

        assert isinstance(result, HealthResponse)

    @patch("app.routers.health.check_mlflow_connection")
    def test_healthy_when_mlflow_connected(self, mock_check):
        """Test status is healthy when MLflow connected."""
        mock_check.return_value = True

        result = health_check()

        assert result.status == "healthy"
        assert result.mlflow_connected is True

    @patch("app.routers.health.check_mlflow_connection")
    def test_degraded_when_mlflow_disconnected(self, mock_check):
        """Test status is degraded when MLflow disconnected."""
        mock_check.return_value = False

        result = health_check()

        assert result.status == "degraded"
        assert result.mlflow_connected is False

    @patch("app.routers.health.check_mlflow_connection")
    def test_includes_version(self, mock_check):
        """Test health response includes version from settings."""
        mock_check.return_value = True

        result = health_check()

        # Version comes from actual settings
        assert result.version is not None
        assert isinstance(result.version, str)

    @patch("app.routers.health.check_mlflow_connection")
    def test_includes_timestamp(self, mock_check):
        """Test health response includes timestamp."""
        mock_check.return_value = True

        result = health_check()

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)


class TestReadinessCheck:
    """Tests for readiness_check endpoint function."""

    def test_returns_ready_status(self):
        """Test readiness_check returns ready status."""
        result = readiness_check()

        assert result == {"status": "ready"}

    def test_returns_dict(self):
        """Test readiness_check returns dictionary."""
        result = readiness_check()

        assert isinstance(result, dict)
        assert "status" in result


class TestLivenessCheck:
    """Tests for liveness_check endpoint function."""

    def test_returns_alive_status(self):
        """Test liveness_check returns alive status."""
        result = liveness_check()

        assert result == {"status": "alive"}

    def test_returns_dict(self):
        """Test liveness_check returns dictionary."""
        result = liveness_check()

        assert isinstance(result, dict)
        assert "status" in result
