"""
Health check tests for Card Approval Prediction API.
"""

from unittest.mock import patch


class TestHealthCheck:
    """Comprehensive health check tests."""

    def test_health_endpoint_exists(self, client):
        """Test health endpoint exists."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Test health response has correct structure."""
        response = client.get("/health")
        data = response.json()

        required_fields = ["status", "version", "mlflow_connected"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_health_status_values(self, client):
        """Test health status has valid values."""
        response = client.get("/health")
        data = response.json()

        valid_statuses = ["healthy", "degraded", "unhealthy"]
        assert data["status"] in valid_statuses

    def test_health_boolean_fields(self, client):
        """Test connection status fields are boolean."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["mlflow_connected"], bool)


class TestHealthDegraded:
    """Tests for degraded health scenarios."""

    def test_health_with_mlflow_down(self, client):
        """Test health when MLflow is unavailable."""
        # Mock check_mlflow_connection to return False
        with patch(
            "app.routers.health.check_mlflow_connection",
            return_value=False,
        ):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            # Status should be degraded when MLflow is down
            assert data["status"] in ["degraded", "unhealthy"]


class TestLiveness:
    """Liveness probe tests (Kubernetes)."""

    def test_root_as_liveness(self, client):
        """Test root endpoint can serve as liveness probe."""
        response = client.get("/")
        assert response.status_code == 200

    def test_liveness_fast_response(self, client):
        """Test liveness responds quickly."""
        import time

        start = time.time()
        response = client.get("/")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should be very fast


class TestReadiness:
    """Readiness probe tests (Kubernetes)."""

    def test_health_as_readiness(self, client):
        """Test health endpoint can serve as readiness probe."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_readiness_checks_dependencies(self, client):
        """Test readiness probe checks all dependencies."""
        response = client.get("/health")
        data = response.json()

        # Should check core services
        assert "mlflow_connected" in data
