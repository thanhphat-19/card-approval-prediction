# Monitoring Guide

Observability stack: Prometheus + Grafana + Loki.

```
FastAPI /metrics → Prometheus → Grafana (dashboards)
Pod logs → Alloy → Loki → Grafana (logs)
```

---

## Step 1: Deploy Monitoring

```bash
source config.env
helm upgrade --install monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring --create-namespace \
  --set kube-prometheus-stack.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"

kubectl get pods -n monitoring
```

---

## Step 2: Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
```

**Open:** http://localhost:3000
- Username: `admin`
- Password: Your `GRAFANA_ADMIN_PASSWORD`

---

## Step 3: View Metrics

### Option A: In Grafana

1. Go to **Explore** → Select **Prometheus**
2. Run queries:

```promql
# Request rate
rate(prediction_requests_total[5m])

# p95 latency
histogram_quantile(0.95, rate(prediction_latency_seconds_bucket[5m]))

# Error rate
rate(prediction_errors_total[5m]) / rate(prediction_requests_total[5m])
```

### Option B: Direct API

```bash
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
curl http://localhost:8000/metrics
```

### Option C: Prometheus UI

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring
# Open http://localhost:9090
```

---

## Step 4: View Logs

### Option A: In Grafana (Loki)

1. Go to **Explore** → Select **Loki**
2. Run queries:

```logql
# All API logs
{namespace="card-approval"}

# Error logs only
{namespace="card-approval"} |= "ERROR"

# Prediction logs
{namespace="card-approval"} |~ "predict"
```

### Option B: kubectl

```bash
# Follow API logs
kubectl logs -f deployment/card-approval-api -n card-approval

# MLflow logs
kubectl logs -f deployment/card-approval-training-mlflow -n card-approval-training
```

---

## Step 5: Create Dashboard

1. Grafana → **Dashboards** → **Import**
2. Paste dashboard JSON or ID
3. Select Prometheus data source

**Key panels to add:**
- Request rate (req/s)
- Latency p50, p95, p99
- Error rate %
- Model version

---

## Quick Reference

| Service | Port Forward | URL |
|---------|--------------|-----|
| Grafana | `3000:80` | http://localhost:3000 |
| Prometheus | `9090:9090` | http://localhost:9090 |
| API Metrics | `8000:80` | http://localhost:8000/metrics |

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| No metrics | `kubectl get pods -n card-approval -o yaml \| grep prometheus.io/scrape` |
| No logs in Loki | `kubectl get pods -n monitoring -l app.kubernetes.io/name=alloy` |
| Grafana login fails | Verify `GRAFANA_ADMIN_PASSWORD` in config.env |
