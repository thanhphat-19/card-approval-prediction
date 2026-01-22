# Monitoring Guide

## Overview

Observability stack: Prometheus + Grafana + Loki.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │───▶│ Prometheus  │───▶│   Grafana   │
│  /metrics   │    │   (scrape)  │    │ (visualize) │
└─────────────┘    └─────────────┘    └─────────────┘
       │                                     │
       ▼                                     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Logs     │───▶│    Alloy    │───▶│    Loki     │
│  (stdout)   │    │  (collect)  │    │   (store)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

# **Step 1: Deploy Monitoring Stack**

```bash
helm upgrade --install monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring --create-namespace
```

**What gets deployed:**
- Prometheus - Metrics collection
- Grafana - Dashboards
- Loki - Log aggregation
- Alloy - Log collector

**Verify:**
```bash
kubectl get pods -n monitoring
```

---

# **Step 2: Access Grafana**

```bash
kubectl port-forward svc/grafana 3000:80 -n monitoring
```

**Login:**
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`

---

# **Step 3: Configure Data Sources**

**Prometheus (auto-configured):**
- URL: `http://prometheus-server:80`
- Access: Server

**Loki (auto-configured):**
- URL: `http://loki:3100`
- Access: Server

---

# **Step 4: API Metrics**

The API exposes these metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

**Available metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `prediction_requests_total` | Counter | Total predictions |
| `prediction_latency_seconds` | Histogram | Response time |
| `prediction_errors_total` | Counter | Failed predictions |
| `model_version_info` | Gauge | Current model version |
| `active_requests` | Gauge | In-flight requests |

---

# **Step 5: Create Dashboard**

**Import pre-built dashboard:**
1. Go to Dashboards → Import
2. Upload JSON or paste ID
3. Select Prometheus data source

**Key panels:**
- Request rate (req/s)
- Latency percentiles (p50, p95, p99)
- Error rate
- Model version

**PromQL examples:**

```promql
# Request rate
rate(prediction_requests_total[5m])

# p95 latency
histogram_quantile(0.95, rate(prediction_latency_seconds_bucket[5m]))

# Error rate
rate(prediction_errors_total[5m]) / rate(prediction_requests_total[5m])
```

---

# **Step 6: View Logs in Grafana**

1. Go to Explore
2. Select Loki data source
3. Query logs:

```logql
# All API logs
{namespace="card-approval", app="card-approval-api"}

# Error logs only
{namespace="card-approval"} |= "ERROR"

# Prediction logs
{namespace="card-approval"} |~ "prediction|predict"
```

---

# **Step 7: Set Up Alerts**

**Example alert rule:**

```yaml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(prediction_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(prediction_latency_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency > 1 second"
```

---

# **Step 8: Quick Checks**

**Check Prometheus targets:**
```bash
kubectl port-forward svc/prometheus-server 9090:80 -n monitoring
open http://localhost:9090/targets
```

**Check Loki logs:**
```bash
kubectl logs -l app.kubernetes.io/name=loki -n monitoring
```

**Check Alloy status:**
```bash
kubectl logs -l app.kubernetes.io/name=alloy -n monitoring
```

---

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Grafana | 80 | Dashboards |
| Prometheus | 80 | Metrics |
| Loki | 3100 | Logs |

---

## Troubleshooting

**No metrics in Prometheus:**
```bash
# Check API annotations
kubectl get pods -n card-approval -o yaml | grep -A5 annotations
# Should have: prometheus.io/scrape: "true"
```

**No logs in Loki:**
```bash
# Check Alloy is running
kubectl get pods -n monitoring -l app.kubernetes.io/name=alloy

# Check log collection
kubectl logs -l app.kubernetes.io/name=alloy -n monitoring | grep card-approval
```
