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

The Tempo datasource is **auto-configured** when you deploy the monitoring stack.

**Important:** The datasource is provisioned in `helm-charts/infrastructure/card-approval-monitoring/values.yaml` with the correct URL: `http://tempo.monitoring.svc.cluster.local:3200`

> **⚠️ Common Mistake:** Do NOT use port 3100 (Prometheus metrics port). Always use port **3200** for Tempo HTTP API.

If you need to manually add the datasource:

1. Go to **Configuration** → **Data Sources**
2. Click **Add data source** → Select **Tempo**
3. Configure:
   - **Name:** `Tempo`
   - **URL:** `http://tempo.monitoring.svc.cluster.local:3200` ← **Port 3200!**
   - **HTTP Method:** `GET`
4. Click **Save & Test**

**Tempo Ports Explained:**
- **Port 3200** - HTTP API (for Grafana queries) ✅
- **Port 4317** - OTLP gRPC (for trace ingestion from apps)
- **Port 3100** - Prometheus metrics (NOT for trace queries) ❌

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

---

## Common Issues & Troubleshooting

### Issue: Tempo Datasource Shows "Bad Gateway" Error

**Symptoms:**
- Tempo appears in Grafana datasources
- Clicking "Explore" → "Tempo" shows: `Error (Bad Gateway)`
- Service name dropdown shows "no option found"

**Root Cause:**
Wrong port configured in datasource URL.

**Solution:**
1. Check current datasource configuration:
```bash
source config.env
curl -s -u "admin:${GRAFANA_ADMIN_PASSWORD}" \
  "http://<NGINX_IP>/grafana/api/datasources" | jq '.[] | select(.name=="Tempo") | .url'
```

2. If URL shows port 3100, update `helm-charts/infrastructure/card-approval-monitoring/values.yaml`:
```yaml
- name: Tempo
  type: tempo
  uid: tempo
  url: http://tempo.monitoring.svc.cluster.local:3200  # ← Change from 3100 to 3200
```

3. Upgrade and restart:
```bash
helm upgrade monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring \
  --set kube-prometheus.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"

kubectl rollout restart deployment/monitoring-grafana -n monitoring
```

---

### Issue: Port 3200 Not Exposed in Tempo Service

**Symptoms:**
- Tempo pod is running
- Grafana cannot reach `http://tempo.monitoring:3200`
- `kubectl describe svc tempo -n monitoring` doesn't show port 3200

**Root Cause:**
The Tempo Helm chart may not expose the HTTP API port by default.

**Solution:**
```bash
# Patch the service to expose port 3200
kubectl patch svc tempo -n monitoring --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/ports/-",
    "value": {
      "name": "tempo-http",
      "port": 3200,
      "targetPort": 3200,
      "protocol": "TCP"
    }
  }
]'

# Verify the port is exposed
kubectl get svc tempo -n monitoring -o jsonpath='{.spec.ports[*].name}' | grep tempo-http

# Test connectivity from Grafana
kubectl exec -n monitoring $(kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -c grafana -- \
  wget -qO- "http://tempo.monitoring.svc.cluster.local:3200/ready"
```

---

### Issue: No Traces Appearing in Tempo

**Symptoms:**
- Tempo datasource works
- Service name dropdown is empty
- API is running but no traces found

**Diagnosis:**
```bash
# 1. Check if tracing is enabled in API
kubectl describe pod -n card-approval -l app.kubernetes.io/name=api | grep -A 5 "OTEL"

# Should show:
# OTEL_ENABLED: true
# OTEL_SERVICE_NAME: card-approval-api
# OTEL_EXPORTER_ENDPOINT: http://tempo.monitoring:4317
# OTEL_SAMPLING_RATE: 1.0

# 2. Check API logs for tracing initialization
kubectl logs -n card-approval -l app.kubernetes.io/name=api | grep -i "tracing\|otel"

# Should show:
# INFO | Initializing OpenTelemetry tracing: service=card-approval-api
# INFO | OTLP exporter configured: http://tempo.monitoring:4317
# INFO | Tracing initialized: sampling_rate=100.0%

# 3. Check if traces are reaching Tempo
kubectl exec -n monitoring tempo-0 -- wget -qO- \
  "http://localhost:3200/api/search/tag/service.name/values"

# Should return: {"tagValues":["card-approval-api"]}
```

**Solution if tracing not enabled:**
```bash
# Upgrade API with tracing enabled
source config.env
helm upgrade card-approval helm-charts/card-approval \
  -n card-approval \
  --set api.tracing.enabled=true \
  --set api.tracing.exporterEndpoint="http://tempo.monitoring:4317" \
  --set api.tracing.samplingRate="1.0" \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set postgres.password="${POSTGRES_APP_PASSWORD}"

# Restart API
kubectl rollout restart deployment/card-approval-api -n card-approval
```

---

### Issue: Grafana Doesn't Reload Datasource Changes

**Symptoms:**
- Updated monitoring Helm chart
- Tempo datasource still shows old configuration

**Solution:**
Always restart Grafana after updating the monitoring stack:
```bash
kubectl rollout restart deployment/monitoring-grafana -n monitoring

# Wait for new pod to be ready
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana -w
```

---

### Verification Checklist

Use this checklist after deploying tracing:

- [ ] Tempo pod is running: `kubectl get pods -n monitoring -l app.kubernetes.io/name=tempo`
- [ ] Port 3200 is exposed: `kubectl get svc tempo -n monitoring -o jsonpath='{.spec.ports[*].name}' | grep tempo-http`
- [ ] Grafana has Tempo datasource: `curl -s -u "admin:${GRAFANA_ADMIN_PASSWORD}" "http://<IP>/grafana/api/datasources" | jq '.[].name'`
- [ ] Datasource uses port 3200: `curl -s -u "admin:${GRAFANA_ADMIN_PASSWORD}" "http://<IP>/grafana/api/datasources" | jq '.[] | select(.name=="Tempo") | .url'`
- [ ] API has tracing enabled: `kubectl describe pod -n card-approval -l app.kubernetes.io/name=api | grep OTEL_ENABLED`
- [ ] API logs show tracing init: `kubectl logs -n card-approval -l app.kubernetes.io/name=api | grep "Tracing initialized"`
- [ ] Traces exist in Tempo: `kubectl exec -n monitoring tempo-0 -- wget -qO- "http://localhost:3200/api/search/tag/service.name/values"`
- [ ] Grafana can query Tempo: Navigate to Explore → Tempo → Search for service name
