"""OpenTelemetry tracing configuration for distributed tracing."""

from typing import Optional

from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from app.core.config import get_settings

# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def setup_tracing(app=None) -> None:
    """
    Initialize OpenTelemetry tracing.

    Args:
        app: FastAPI application instance for auto-instrumentation
    """
    settings = get_settings()

    if not settings.OTEL_ENABLED:
        logger.info("Tracing disabled (OTEL_ENABLED=false)")
        return

    logger.info(f"Initializing OpenTelemetry tracing: service={settings.OTEL_SERVICE_NAME}")

    # Configure sampling rate
    sampling_rate = settings.OTEL_SAMPLING_RATE
    sampler = ParentBasedTraceIdRatio(sampling_rate)

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": "production" if not settings.DEBUG else "development",
        }
    )

    # Create tracer provider with sampler
    provider = TracerProvider(resource=resource, sampler=sampler)

    # Configure exporter based on endpoint
    if settings.OTEL_EXPORTER_ENDPOINT:
        # OTLP exporter for Tempo
        exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_ENDPOINT,
            insecure=True,  # Use insecure for internal K8s communication
        )
        logger.info(f"OTLP exporter configured: {settings.OTEL_EXPORTER_ENDPOINT}")
    else:
        # Console exporter for development
        exporter = ConsoleSpanExporter()
        logger.info("Console exporter configured (no OTEL_EXPORTER_ENDPOINT)")

    # Add batch processor for efficient export
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI
    if app:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI auto-instrumentation enabled")

    # Auto-instrument requests library (for MLflow API calls)
    RequestsInstrumentor().instrument()
    logger.info("Requests auto-instrumentation enabled")

    logger.info(f"Tracing initialized: sampling_rate={sampling_rate * 100}%")


def get_tracer(name: str = "card-approval-api") -> trace.Tracer:
    """
    Get a tracer instance for creating custom spans.

    Args:
        name: Name of the tracer (usually module name)

    Returns:
        Tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(name)
    return _tracer


def get_current_trace_id() -> Optional[str]:
    """
    Get the current trace ID for log correlation.

    Returns:
        Trace ID as hex string, or None if no active span
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_current_span_id() -> Optional[str]:
    """
    Get the current span ID for log correlation.

    Returns:
        Span ID as hex string, or None if no active span
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return None


def add_span_attributes(attributes: dict) -> None:
    """
    Add attributes to the current span.

    Args:
        attributes: Dictionary of attribute key-value pairs
    """
    span = trace.get_current_span()
    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception) -> None:
    """
    Record an exception in the current span.

    Args:
        exception: The exception to record
    """
    span = trace.get_current_span()
    if span:
        span.record_exception(exception)
        span.set_attribute("error", True)
