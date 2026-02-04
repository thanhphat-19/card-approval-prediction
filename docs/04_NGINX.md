# Accessing Services via NGINX Ingress

## Overview

All public services are exposed through NGINX Ingress Controller with a single LoadBalancer IP.

| Service | Path | Description |
|---------|------|-------------|
| **Card Approval API** | `/api/v1/*`, `/docs`, `/health` | ML prediction API |
| **Grafana** | `/grafana/` | Monitoring dashboards, trace viewer |
| **MLflow** | `/mlflow/` | Experiment tracking, model registry |

---

## Architecture

```
                                    ┌─────────────────────┐
                                    │   Internet User     │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │  GCP LoadBalancer   │
                                    │   (External IP)     │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                         ┌─────────────────────────────────────┐
                         │    NGINX Ingress Controller         │
                         │      (ingress-nginx namespace)      │
                         └──────────┬──────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │  /api/v1/*   │  │  /grafana/   │  │  /mlflow/    │
         │  /docs       │  │              │  │              │
         │  /health     │  │              │  │              │
         └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                │                 │                 │
                ▼                 ▼                 ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ card-approval   │  │ monitoring-     │  │ card-approval-  │
    │ -api            │  │ grafana         │  │ training-mlflow │
    │ (card-approval) │  │ (monitoring)    │  │ (training)      │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Key Points:**
- Single external IP for all services
- Path-based routing to different namespaces
- TLS termination at NGINX (if configured)
- Service-to-service communication within cluster

---

## Prerequisites

1. **NGINX Ingress Controller** deployed
2. **Services** running in Kubernetes
3. **Ingress resources** configured

---



## Card Approval API (Swagger)

### Access Swagger UI

```bash
# Open in browser
open http://<NGINX_IP>/docs

# Example
open http://34.139.72.244/docs
```


---

## Grafana (Monitoring)

### Access Grafana

```bash
open http://<NGINX_IP>/grafana/

# Example
open http://34.139.72.244/grafana/
```

### Get Admin Password

```bash
kubectl get secret monitoring-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d
```

### Default Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | (from secret above) |


---

## MLflow (Experiment Tracking)

### Access MLflow UI

```bash
open http://<NGINX_IP>/mlflow/

# Example
open http://34.139.72.244/mlflow/
```


---

## Test Prediction API

```bash
# Get LoadBalancer IP
export NGINX_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Health check
curl http://${NGINX_IP}/health

# Make prediction
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

**Expected Response:**
```json
{
  "prediction": 1,
  "probability": 0.9955,
  "decision": "APPROVED",
  "confidence": 0.9955,
  "version": "1",
  "timestamp": "2026-02-03T14:00:00.000000"
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **No LoadBalancer IP** | Pending state | Wait 2-5 minutes for GCP to provision |
| **Connection refused** | Service not running | Check pods are running |
| **404 Not Found** | Ingress not configured | Apply `kubectl apply -f manifests/ingress.yaml` |
| **502 Bad Gateway** | Backend service down | Check pod logs |
| **503 Service Unavailable** | No ready endpoints | Verify pod is Ready |

### Check Ingress Configuration

```bash
# View all ingress resources
kubectl get ingress -A

# Describe ingress for details
kubectl describe ingress <ingress-name> -n <namespace>

# Check ingress controller logs
kubectl logs -f deployment/nginx-ingress-ingress-nginx-controller -n ingress-nginx
```

### Service Connectivity Test

```bash
# Test from inside cluster
kubectl run test-curl --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://card-approval-api.card-approval/health

# Test MLflow
kubectl run test-curl --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://card-approval-training-mlflow.card-approval-training:5000/health
```

---

## Summary

Your services are now accessible through NGINX Ingress:

✅ **Single External IP** - All services behind one LoadBalancer
✅ **Path-based Routing** - Different paths route to different services
✅ **Swagger Documentation** - Interactive API docs at `/docs`
✅ **Health Monitoring** - Health endpoint at `/health`

**Access URLs:**
```bash
export NGINX_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "API: http://${NGINX_IP}/docs"
echo "Grafana: http://${NGINX_IP}/grafana/"
echo "MLflow: http://${NGINX_IP}/mlflow/"
```

---

## Next Steps

1. **[Monitoring](05_Monitoring.md)** - View logs, metrics, and request traces in Grafana
