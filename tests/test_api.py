"""
API endpoint tests for Card Approval Prediction API.
"""


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_200(self, client):
        """Test root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_app_info(self, client):
        """Test root endpoint returns application info."""
        response = client.get("/")
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_root_contains_docs_link(self, client):
        """Test root endpoint contains documentation links."""
        response = client.get("/")
        data = response.json()

        assert "docs" in data
        assert data["docs"] == "/docs"


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client):
        """Test health endpoint returns status field."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_returns_version(self, client):
        """Test health endpoint returns version."""
        response = client.get("/health")
        data = response.json()

        assert "version" in data

    def test_health_returns_connection_status(self, client):
        """Test health endpoint returns connection statuses."""
        response = client.get("/health")
        data = response.json()

        # These fields should exist
        assert "mlflow_connected" in data
        assert "database_connected" in data


class TestDocsEndpoint:
    """Tests for documentation endpoints."""

    def test_swagger_ui_available(self, client):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client):
        """Test ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_available(self, client):
        """Test OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestMetricsEndpoint:
    """Tests for Prometheus metrics endpoint."""

    def test_metrics_returns_200(self, client):
        """Test metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_contains_prometheus_format(self, client):
        """Test metrics are in Prometheus format."""
        response = client.get("/metrics")
        # Prometheus metrics should be text/plain
        assert response.status_code == 200
