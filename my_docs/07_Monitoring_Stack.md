# Component 7: Monitoring Stack

## Executive Summary

The monitoring stack provides full observability for the ML API through three pillars: **Metrics** (Prometheus), **Logs** (structured JSON), and **Traces** (Grafana Tempo). Grafana serves as the unified visualization layer. This enables proactive monitoring, debugging, and performance optimization of ML inference workloads.

---

## 1. Concept & Theory

### Three Pillars of Observability

| Pillar | Tool | Purpose |
|--------|------|---------|
| **Metrics** | Prometheus | Quantitative measurements over time |
| **Logs** | Loguru + Loki | Detailed event records |
| **Traces** | Tempo + OpenTelemetry | Request flow through services |

### Why Observability for ML APIs?

| Challenge | Observability Solution |
|-----------|----------------------|
| Slow predictions | Latency histograms identify bottlenecks |
| Model degradation | Track prediction distributions over time |
| Error debugging | Traces show exact failure point |
| Capacity planning | Request rate and resource metrics |

### Observability Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Metrics   │  │    Logs     │  │   Traces    │             │
│  │ /metrics    │  │  Loguru     │  │ OpenTelemetry│            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ↓                ↓                ↓
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │Prometheus │    │   Loki    │    │   Tempo   │
    │  (TSDB)   │    │(Log Store)│    │(Trace DB) │
    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                    ┌───────────┐
                    │  Grafana  │
                    │(Dashboard)│
                    └───────────┘
```

### ML-Specific Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| `prediction_count` | Counter | Total predictions made |
| `prediction_latency` | Histogram | Inference time distribution |
| `model_version` | Gauge | Currently loaded model |
| `approval_rate` | Gauge | % of approved predictions |
| `confidence_distribution` | Histogram | Model confidence scores |

---

## 2. Architecture & Design Decisions

### Stack Components

```
helm-charts/infrastructure/
├── monitoring/             # Prometheus + Grafana (kube-prometheus-stack)
├── tempo/                  # Grafana Tempo for distributed tracing
└── card-approval-monitoring/  # Custom dashboards
```

### Key Design Decisions

#### 1. Prometheus Client Integration
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "fastapi_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "fastapi_request_duration_seconds",
    "Request duration",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
```

**Rationale**: Native Prometheus client for zero-overhead metrics.

#### 2. OpenTelemetry for Tracing
```python
# app/core/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_tracing(app: FastAPI):
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT))
    )
    FastAPIInstrumentor.instrument_app(app)
```

**Benefit**: Auto-instruments FastAPI routes; manual spans for ML inference.

#### 3. Custom Spans for ML Operations
```python
# app/services/model_service.py
with tracer.start_as_current_span("model_inference.predict") as span:
    span.set_attribute("model.name", self.settings.MODEL_NAME)
    span.set_attribute("model.version", str(self.version))
    span.set_attribute("batch_size", len(features))
    prediction = self.model.predict(features)
```

---

## 3. Implementation Guide

### Prometheus Metrics Implementation

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
from starlette.responses import Response

# Custom registry to avoid default metrics
REGISTRY = CollectorRegistry()

# Request metrics
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
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)

ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Number of active requests",
    registry=REGISTRY,
)

# ML-specific metrics
PREDICTION_COUNT = Counter(
    "ml_predictions_total",
    "Total predictions made",
    ["model_version", "decision"],
    registry=REGISTRY,
)

PREDICTION_LATENCY = Histogram(
    "ml_prediction_latency_seconds",
    "Model inference latency",
    ["model_name"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=REGISTRY,
)

MODEL_CONFIDENCE = Histogram(
    "ml_model_confidence",
    "Prediction confidence distribution",
    ["model_version"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99],
    registry=REGISTRY,
)


def track_request_metrics(method: str, endpoint: str, status_code: int):
    """Track request metrics"""
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status=str(status_code)
    ).inc()


def track_prediction(model_version: str, decision: str, confidence: float, latency: float):
    """Track ML prediction metrics"""
    PREDICTION_COUNT.labels(
        model_version=model_version,
        decision=decision
    ).inc()
    MODEL_CONFIDENCE.labels(model_version=model_version).observe(confidence)
    PREDICTION_LATENCY.labels(model_name="card_approval").observe(latency)


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    metrics = generate_latest(REGISTRY)
    return Response(content=metrics, media_type="text/plain")
```

### Request Tracking Middleware

```python
# app/main.py
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Middleware to track request metrics"""
    start_time = time.time()
    ACTIVE_REQUESTS.inc()

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        track_request_metrics(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        )
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response
    finally:
        ACTIVE_REQUESTS.dec()
```

### OpenTelemetry Tracing Setup

```python
# app/core/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import NoOpTracer

from app.core.config import get_settings

_tracer = None


def setup_tracing(app):
    """Initialize OpenTelemetry tracing"""
    global _tracer
    settings = get_settings()

    if not settings.OTEL_ENABLED or not settings.OTEL_EXPORTER_ENDPOINT:
        _tracer = NoOpTracer()
        return

    # Configure resource
    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": settings.APP_VERSION,
    })

    # Configure tracer provider
    provider = TracerProvider(resource=resource)

    # Configure exporter
    exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT,
        insecure=True,
    )

    # Add span processor
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    _tracer = trace.get_tracer(__name__)


def get_tracer():
    """Get configured tracer"""
    global _tracer
    if _tracer is None:
        _tracer = NoOpTracer()
    return _tracer
```

### Structured Logging

```python
# app/core/logging.py
import sys
from loguru import logger
from app.core.config import get_settings


def setup_logging():
    """Configure Loguru for structured logging"""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console handler
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    if settings.LOG_FORMAT == "json":
        # JSON format for production
        logger.add(
            sys.stdout,
            format="{message}",
            level=settings.LOG_LEVEL,
            serialize=True,  # JSON output
        )
    else:
        # Pretty format for development
        logger.add(
            sys.stdout,
            format=log_format,
            level=settings.LOG_LEVEL,
            colorize=True,
        )

    # File handler with rotation
    logger.add(
        settings.LOG_FILE,
        format=log_format,
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="gz",
    )
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Card Approval API",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(fastapi_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Request Latency (p99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(fastapi_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p99 latency"
          }
        ]
      },
      {
        "title": "Prediction Count by Decision",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(ml_predictions_total) by (decision)",
            "legendFormat": "{{decision}}"
          }
        ]
      },
      {
        "title": "Model Inference Latency",
        "type": "heatmap",
        "targets": [
          {
            "expr": "rate(ml_prediction_latency_seconds_bucket[5m])"
          }
        ]
      },
      {
        "title": "Model Confidence Distribution",
        "type": "histogram",
        "targets": [
          {
            "expr": "rate(ml_model_confidence_bucket[5m])"
          }
        ]
      }
    ]
  }
}
```

### Helm Values for Monitoring

```yaml
# helm-charts/infrastructure/monitoring/values.yaml
prometheus:
  enabled: true
  serviceMonitor:
    enabled: true
    namespace: card-approval
    selector:
      matchLabels:
        app: card-approval-api

grafana:
  enabled: true
  adminPassword: admin
  datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus-server:80
    - name: Tempo
      type: tempo
      url: http://tempo:3100
    - name: Loki
      type: loki
      url: http://loki:3100
```

### Tempo Configuration

```yaml
# helm-charts/infrastructure/tempo/values.yaml
tempo:
  tempo:
    storage:
      trace:
        backend: gcs
        gcs:
          bucket_name: "${GCS_BUCKET_NAME}"

    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| High cardinality labels | Limit label values (no user IDs) |
| Missing trace context | Use `trace.get_current_span()` |
| No sampling in production | Set `OTEL_SAMPLING_RATE=0.1` |
| Metrics endpoint unprotected | Consider auth for `/metrics` |

### Alert Rules

```yaml
# Prometheus alert rules
groups:
  - name: ml-api-alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(fastapi_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency (p99 > 1s)"

      - alert: HighErrorRate
        expr: rate(fastapi_requests_total{status=~"5.."}[5m]) / rate(fastapi_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 5%"

      - alert: ModelLoadFailure
        expr: up{job="card-approval-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API pod is down"

      - alert: LowApprovalRate
        expr: sum(rate(ml_predictions_total{decision="APPROVED"}[1h])) / sum(rate(ml_predictions_total[1h])) < 0.3
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Approval rate dropped below 30%"
```

### Tracing Best Practices

```python
# Add custom attributes to spans
with tracer.start_as_current_span("preprocessing") as span:
    span.set_attribute("input.customer_id", customer_id)
    span.set_attribute("input.income", income)
    span.set_attribute("feature_count", len(features))

    # Record events
    span.add_event("Starting feature encoding")
    encoded = encode_features(data)
    span.add_event("Feature encoding complete", {"encoded_count": len(encoded)})
```

---

## 5. Testing & Validation

### Verify Metrics

```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus-server 9090:80 -n monitoring

# Query metrics
curl 'http://localhost:9090/api/v1/query?query=fastapi_requests_total'

# Check API metrics endpoint
curl http://localhost:8000/metrics
```

### Verify Traces

```bash
# Port-forward Tempo
kubectl port-forward svc/tempo 3100:3100 -n monitoring

# Port-forward Grafana
kubectl port-forward svc/grafana 3000:80 -n monitoring

# Open Grafana → Explore → Tempo → Search for traces
```

### Grafana Dashboard Validation

1. Navigate to Grafana → Dashboards
2. Verify data appears in all panels
3. Test time range selection
4. Verify drill-down to traces works

---

## 6. Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_ENABLED` | `true` | Enable tracing |
| `OTEL_SERVICE_NAME` | `card-approval-api` | Service name in traces |
| `OTEL_EXPORTER_ENDPOINT` | "" | Tempo gRPC endpoint |
| `OTEL_SAMPLING_RATE` | `1.0` | Trace sampling (1.0 = 100%) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LOG_FORMAT` | `text` | `text` or `json` |

### Useful PromQL Queries

```promql
# Request rate
rate(fastapi_requests_total[5m])

# Error rate
sum(rate(fastapi_requests_total{status=~"5.."}[5m])) / sum(rate(fastapi_requests_total[5m]))

# P99 latency
histogram_quantile(0.99, rate(fastapi_request_duration_seconds_bucket[5m]))

# Prediction throughput
rate(ml_predictions_total[5m])

# Approval rate
sum(rate(ml_predictions_total{decision="APPROVED"}[5m])) / sum(rate(ml_predictions_total[5m]))
```

---

## 7. Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Tempo](https://grafana.com/docs/tempo/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Loguru Documentation](https://loguru.readthedocs.io/)
- [SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
