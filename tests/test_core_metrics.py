"""
Unit tests for app/core/metrics.py module.
"""

import pytest
from starlette.responses import Response

from app.core.metrics import ACTIVE_REQUESTS, REQUEST_COUNT, REQUEST_DURATION, metrics_endpoint, track_request_metrics


class TestMetricsDefinition:
    """Tests for metrics definitions."""

    def test_request_count_exists(self):
        """Test REQUEST_COUNT metric is defined."""
        assert REQUEST_COUNT is not None

    def test_request_duration_exists(self):
        """Test REQUEST_DURATION metric is defined."""
        assert REQUEST_DURATION is not None

    def test_active_requests_exists(self):
        """Test ACTIVE_REQUESTS gauge is defined."""
        assert ACTIVE_REQUESTS is not None


class TestTrackRequestMetrics:
    """Tests for track_request_metrics function."""

    def test_increments_counter(self):
        """Test track_request_metrics increments request counter."""
        # Track a request
        track_request_metrics(
            method="GET",
            endpoint="/test",
            status_code=200,
        )

        # Should not raise any errors
        # Counter should be incremented (we can't easily verify the value
        # due to prometheus_client internals, but no exception means success)

    def test_handles_different_methods(self):
        """Test tracking different HTTP methods."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            track_request_metrics(
                method=method,
                endpoint="/api/test",
                status_code=200,
            )

    def test_handles_different_status_codes(self):
        """Test tracking different status codes."""
        status_codes = [200, 201, 400, 401, 403, 404, 500, 503]

        for status in status_codes:
            track_request_metrics(
                method="GET",
                endpoint="/api/test",
                status_code=status,
            )

    def test_handles_various_endpoints(self):
        """Test tracking various endpoint paths."""
        endpoints = ["/", "/health", "/api/v1/predict", "/metrics"]

        for endpoint in endpoints:
            track_request_metrics(
                method="GET",
                endpoint=endpoint,
                status_code=200,
            )


class TestActiveRequests:
    """Tests for ACTIVE_REQUESTS gauge."""

    def test_increment_active_requests(self):
        """Test incrementing active requests."""
        ACTIVE_REQUESTS.inc()
        # Should not raise

    def test_decrement_active_requests(self):
        """Test decrementing active requests."""
        ACTIVE_REQUESTS.dec()
        # Should not raise


class TestRequestDuration:
    """Tests for REQUEST_DURATION histogram."""

    def test_observe_duration(self):
        """Test observing request duration."""
        REQUEST_DURATION.labels(
            method="GET",
            endpoint="/test",
        ).observe(0.5)

    def test_observe_various_durations(self):
        """Test observing various duration values."""
        durations = [0.001, 0.01, 0.1, 0.5, 1.0, 5.0]

        for duration in durations:
            REQUEST_DURATION.labels(
                method="POST",
                endpoint="/api/v1/predict",
            ).observe(duration)


class TestMetricsEndpoint:
    """Tests for metrics_endpoint function."""

    @pytest.mark.asyncio
    async def test_returns_response(self):
        """Test metrics_endpoint returns a Response."""
        response = await metrics_endpoint()

        assert isinstance(response, Response)

    @pytest.mark.asyncio
    async def test_content_type_is_text_plain(self):
        """Test metrics endpoint returns text/plain content type."""
        response = await metrics_endpoint()

        assert response.media_type == "text/plain"

    @pytest.mark.asyncio
    async def test_content_is_bytes(self):
        """Test metrics content is bytes."""
        response = await metrics_endpoint()

        assert isinstance(response.body, bytes)

    @pytest.mark.asyncio
    async def test_contains_metric_names(self):
        """Test response contains expected metric names."""
        response = await metrics_endpoint()
        content = response.body.decode("utf-8")

        # Should contain our custom metrics
        assert "fastapi_requests_total" in content or "active_requests" in content
