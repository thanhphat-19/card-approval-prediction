"""
Prometheus metrics for monitoring
"""
import time
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry
from starlette.responses import Response

# Create a custom registry
REGISTRY = CollectorRegistry()

# Define metrics
REQUEST_COUNT = Counter(
    "fastapi_requests_total", "Total number of requests", ["method", "endpoint", "status"], registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    "fastapi_request_duration_seconds", "Request duration in seconds", ["method", "endpoint"], registry=REGISTRY
)

PREDICTION_COUNT = Counter("predictions_total", "Total number of predictions", ["result"], registry=REGISTRY)

PREDICTION_DURATION = Histogram("prediction_duration_seconds", "Prediction duration in seconds", registry=REGISTRY)

MODEL_VERSION = Gauge("model_version_info", "Current model version", ["version", "stage"], registry=REGISTRY)

ACTIVE_REQUESTS = Gauge("active_requests", "Number of active requests", registry=REGISTRY)

ERROR_COUNT = Counter("errors_total", "Total number of errors", ["error_type"], registry=REGISTRY)


def track_request_metrics(method: str, endpoint: str, status_code: int):
    """Track request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()


def track_prediction_metrics(result: str, duration: float):
    """Track prediction metrics"""
    PREDICTION_COUNT.labels(result=result).inc()
    PREDICTION_DURATION.observe(duration)


def track_error(error_type: str):
    """Track error metrics"""
    ERROR_COUNT.labels(error_type=error_type).inc()


def update_model_info(version: str, stage: str):
    """Update model version info"""
    MODEL_VERSION.labels(version=version, stage=stage).set(1)


async def metrics_endpoint():
    """Endpoint to expose metrics to Prometheus"""
    metrics = generate_latest(REGISTRY)
    return Response(content=metrics, media_type="text/plain")


def monitor_performance(func):
    """Decorator to monitor function performance"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        ACTIVE_REQUESTS.inc()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            ACTIVE_REQUESTS.dec()
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=kwargs.get("request", {}).get("method", "UNKNOWN"),
                endpoint=kwargs.get("request", {}).get("path", "UNKNOWN"),
            ).observe(duration)

    return wrapper
