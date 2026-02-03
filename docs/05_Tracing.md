# Distributed Tracing with OpenTelemetry and Grafana Tempo

This document describes the distributed tracing implementation for the Card Approval Prediction API.

## Overview

The project uses **OpenTelemetry** for instrumentation and **Grafana Tempo** as the trace backend, providing end-to-end visibility into request flows.

## Architecture

```
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   FastAPI     │──OTLP───▶│    Tempo      │◀─Query──│   Grafana     │
│   App         │          │   Backend     │          │  Dashboard    │
└───────────────┘          └───────────────┘          └───────────────┘
```

## Components

| Component | Purpose |
|-----------|---------|
| OpenTelemetry SDK | Instrumentation library |
| Grafana Tempo | Trace storage and query backend |
| Grafana | Visualization and trace exploration |

## Configuration

### Environment Variables (`config.env`)

Configure tracing in your `config.env` file:

```bash
# OpenTelemetry Tracing Configuration
OTEL_ENABLED=true
OTEL_SERVICE_NAME=card-approval-api
OTEL_EXPORTER_ENDPOINT=http://tempo.monitoring:4317
OTEL_SAMPLING_RATE=0.1  # 10% for production, 1.0 for development
```

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_ENABLED` | Enable/disable tracing | `true` |
| `OTEL_SERVICE_NAME` | Service name in traces | `card-approval-api` |
| `OTEL_EXPORTER_ENDPOINT` | Tempo OTLP endpoint | `http://tempo.monitoring:4317` |
| `OTEL_SAMPLING_RATE` | Sampling rate (0.0-1.0) | `0.1` (10%) |

### Helm Configuration

**Helm Values** (`helm-charts/card-approval/values.yaml`):
```yaml
api:
  tracing:
    enabled: true
    serviceName: "card-approval-api"
    exporterEndpoint: "http://tempo.monitoring:4317"
    samplingRate: "0.1"
```

## Traced Operations

### Automatic Instrumentation

OpenTelemetry automatically traces:
- All HTTP requests to FastAPI endpoints
- HTTP client calls (requests library) to MLflow

### Custom Spans

The following custom spans are implemented:

| Span Name | Location | Attributes |
|-----------|----------|------------|
| `preprocessing` | `preprocessing_service.py` | `feature_count`, `input_rows` |
| `preprocessing.encode` | `preprocessing_service.py` | `encoded_features` |
| `preprocessing.align` | `preprocessing_service.py` | `aligned_features` |
| `preprocessing.scale` | `preprocessing_service.py` | `scaler_type` |
| `preprocessing.pca` | `preprocessing_service.py` | `n_components` |
| `model_inference.predict` | `model_service.py` | `model.name`, `model.version`, `batch_size` |
| `model_inference.predict_proba` | `model_service.py` | `has_proba` |

## Example Trace

A typical prediction request trace looks like:

```
predict_request (150ms) ─────────────────────────────────────────────►
├── preprocessing (45ms) ────────────────────►
│   ├── encode (10ms) ────►
│   ├── align (5ms) ──►
│   ├── scale (15ms) ─────────►
│   └── pca (15ms) ───────────►
└── model_inference (100ms) ─────────────────────────────────────────►
    ├── predict (60ms) ────────────────────────►
    └── predict_proba (35ms) ──────────────────►
```

## Trace-Log Correlation

Logs automatically include trace context for correlation:

```json
{
  "time": "2025-01-24T15:47:00.000Z",
  "level": "INFO",
  "message": "Prediction completed",
  "trace_id": "abc123def456...",
  "span_id": "789xyz..."
}
```

In Grafana, configure derived fields in Loki to link logs to traces.

## Deployment

### Deploy Tempo

```bash
# Add Grafana Helm repo
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Build dependencies
cd helm-charts/infrastructure/tempo
helm dependency build
cd ../../..

# Set values from config.env
source config.env

# Deploy Tempo
helm upgrade --install tempo helm-charts/infrastructure/tempo \
  --namespace monitoring \
  --create-namespace \
  --set tempo.tempo.storage.trace.gcs.bucket_name="${GCS_BUCKET_NAME}" \
  --set tempo.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}"
```

### Configure Grafana Datasource

The Tempo datasource is **auto-configured** when you deploy the monitoring stack. If needed, manually add:

1. Go to **Configuration** → **Data Sources**
2. Click **Add data source** → Select **Tempo**
3. Configure:
   - **Name:** `Tempo`
   - **URL:** `http://tempo.monitoring.svc.cluster.local:3100`
4. Click **Save & Test**

---

## View Traces in Grafana

### Step 1: Access Grafana

```bash
# Get LoadBalancer IP
export NGINX_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Open in browser
echo "http://${NGINX_IP}/grafana"
```

**Login:** `admin` / `<GRAFANA_ADMIN_PASSWORD from config.env>`

### Step 2: Generate Test Traces

```bash
# Make prediction requests to generate traces
curl -X POST "http://${NGINX_IP}/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 12345,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 150000,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -3000,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 1,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2
  }'
```

### Step 3: View Traces in Grafana

1. In Grafana, click the **compass icon** (🧭) → **Explore**
2. Select **Tempo** from the datasource dropdown (top-left)
3. Choose query type:

**Option A - Search:**
- Click **Search** tab
- Select **Service Name** = `card-approval-api`
- Click **Run query**

**Option B - TraceQL:**
- Click **TraceQL** tab
- Enter query and click **Run query**

### Step 4: Analyze Trace Details

Click on any trace to see:
- **Timeline view** - Spans with timing
- **Span details** - Attributes, events, logs
- **Service graph** - Request flow visualization

---

### Deploy API with Tracing

```bash
# Load configuration from config.env
source config.env

# Deploy with values from config.env
helm upgrade --install card-approval helm-charts/card-approval \
  --namespace ${GKE_NAMESPACE} \
  --create-namespace \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --set api.tracing.samplingRate="${OTEL_SAMPLING_RATE}"

# Or adjust sampling rate for development
helm upgrade --install card-approval helm-charts/card-approval \
  --namespace ${GKE_NAMESPACE} \
  --set api.tracing.samplingRate="1.0"  # 100% sampling
```

## Sampling Strategy

| Environment | Sampling Rate | Rationale |
|-------------|---------------|-----------|
| Development | 100% | Full visibility for debugging |
| Staging | 100% | Validate trace quality |
| Production | 10% | Balance cost vs visibility |
| Production (incident) | 100% | Temporary for debugging |

### Always Sample Errors

Errors are always sampled regardless of the sampling rate configuration.

## Grafana Dashboard Queries

### Request Duration by Endpoint

```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{service="card-approval-api"}[5m])) by (le, path)
)
```

### TraceQL Examples

Find slow predictions:
```
{ span.name = "model_inference.predict" } | duration > 100ms
```

Find errors:
```
{ status = error && resource.service.name = "card-approval-api" }
```

Find by customer ID:
```
{ span.customer_id = "5008804" }
```

## Troubleshooting

### No Traces Appearing

1. Check `OTEL_ENABLED=true`
2. Verify Tempo is running: `kubectl get pods -n monitoring -l app.kubernetes.io/name=tempo`
3. Check OTLP endpoint connectivity
4. Review API logs for tracing initialization

### Missing Spans

1. Verify custom spans are in the code path
2. Check sampling rate isn't filtering traces
3. Ensure parent context is propagated

### High Latency

1. Check batch processor settings
2. Verify Tempo has adequate resources
3. Consider increasing sampling rate temporarily to debug

## Files Modified

| File | Changes |
|------|---------|
| `app/core/tracing.py` | OTel initialization |
| `app/core/config.py` | Tracing settings |
| `app/main.py` | Tracing setup |
| `app/services/model_service.py` | Custom spans |
| `app/services/preprocessing_service.py` | Custom spans |
| `app/core/logging.py` | Trace-log correlation |
| `pyproject.toml` | OTel dependencies |
| `helm-charts/infrastructure/tempo/` | Tempo Helm chart |
| `helm-charts/card-approval/values.yaml` | Tracing config |

## Dependencies

```
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-requests==0.43b0
opentelemetry-instrumentation-logging==0.43b0
opentelemetry-exporter-otlp==1.22.0
```
