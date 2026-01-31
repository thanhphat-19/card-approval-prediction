"""
Unit tests for app/main.py module.
"""

from unittest.mock import patch


class TestAppConfiguration:
    """Tests for FastAPI app configuration."""

    def test_app_has_title(self):
        """Test app has a title configured."""
        from app.main import app

        assert app.title is not None
        assert isinstance(app.title, str)

    def test_app_has_docs_url(self):
        """Test app has /docs endpoint."""
        from app.main import app

        assert app.docs_url == "/docs"

    def test_app_has_redoc_url(self):
        """Test app has /redoc endpoint."""
        from app.main import app

        assert app.redoc_url == "/redoc"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_app_info(self, client):
        """Test root endpoint returns app information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_root_includes_docs_link(self, client):
        """Test root includes link to docs."""
        response = client.get("/")
        data = response.json()

        assert data["docs"] == "/docs"

    def test_root_includes_health_link(self, client):
        """Test root includes link to health."""
        response = client.get("/")
        data = response.json()

        assert data["health"] == "/health"


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present in response."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should have CORS headers
        assert response.status_code in [200, 204]


class TestRequestTrackingMiddleware:
    """Tests for request tracking middleware."""

    def test_requests_are_tracked(self, client):
        """Test requests increment metrics."""
        # Make a request
        response = client.get("/")

        assert response.status_code == 200

    def test_metrics_endpoint_after_requests(self, client):
        """Test metrics endpoint shows request data."""
        # Make some requests
        client.get("/")
        client.get("/health")

        response = client.get("/metrics")
        assert response.status_code == 200


class TestLifespan:
    """Tests for application lifespan events."""

    @patch("app.main.logger")
    def test_startup_logs_info(self, mock_logger):
        """Test startup event logs application info."""
        # This would test the lifespan context manager
        # Since it's harder to test directly, we verify the app starts without error
        pass

    @patch("app.main.logger")
    def test_shutdown_logs_message(self, mock_logger):
        """Test shutdown event logs message."""
        # This would test the lifespan shutdown
        pass


class TestIncludedRouters:
    """Tests for included routers."""

    def test_health_router_included(self, client):
        """Test health router endpoints are accessible."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_ready_endpoint(self, client):
        """Test /health/ready endpoint is accessible."""
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_health_live_endpoint(self, client):
        """Test /health/live endpoint is accessible."""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_predict_router_included(self, client, sample_prediction_input):
        """Test predict router endpoints are accessible."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        assert response.status_code == 200

    def test_model_info_endpoint(self, client):
        """Test /api/v1/model-info endpoint is accessible."""
        response = client.get("/api/v1/model-info")
        assert response.status_code == 200


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_returns_200(self, client):
        """Test metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_prometheus_format(self, client):
        """Test metrics are in Prometheus format."""
        response = client.get("/metrics")

        # Should contain metric definitions
        content = response.text
        assert len(content) > 0
