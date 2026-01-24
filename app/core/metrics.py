"""
Prometheus metrics for monitoring
"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry
from starlette.responses import Response

# Create a custom registry
REGISTRY = CollectorRegistry()

# Define metrics - only those actually used in the application
REQUEST_COUNT = Counter(
    "fastapi_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"],
    registry=REGISTRY,
)

REQUEST_DURATION = Histogram(
    "fastapi_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    registry=REGISTRY,
)

ACTIVE_REQUESTS = Gauge("active_requests", "Number of active requests", registry=REGISTRY)


def track_request_metrics(method: str, endpoint: str, status_code: int):
    """Track request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()


async def metrics_endpoint():
    """Endpoint to expose metrics to Prometheus"""
    metrics = generate_latest(REGISTRY)
    return Response(content=metrics, media_type="text/plain")
