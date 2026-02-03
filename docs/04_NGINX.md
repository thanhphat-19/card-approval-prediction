# Accessing Services via NGINX Ingress

## Overview

All public services are exposed through NGINX Ingress Controller with a single LoadBalancer IP.

| Service | Path | Description |
|---------|------|-------------|
| **Card Approval API** | `/api/v1/*`, `/docs`, `/health` | ML prediction API |
| **Grafana** | `/grafana/` | Monitoring dashboards, trace viewer |
| **MLflow** | `/mlflow/` | Experiment tracking, model registry |

---

## Quick Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Swagger UI** | `http://<NGINX_IP>/docs` | None |
| **ReDoc** | `http://<NGINX_IP>/redoc` | None |
| **Grafana** | `http://<NGINX_IP>/grafana/` | admin / (from secret) |
| **MLflow** | `http://<NGINX_IP>/mlflow/` | None |

---

## Prerequisites

1. **NGINX Ingress Controller** deployed
2. **Services** running in Kubernetes
3. **Ingress resources** configured

---

## Step 1: Get NGINX LoadBalancer IP

```bash
kubectl get svc -n ingress-nginx
```

**Expected output:**
```
NAME                                 TYPE           EXTERNAL-IP     PORT(S)
nginx-ingress-ingress-nginx-controller             LoadBalancer   34.139.72.244   80:30080/TCP,443:30443/TCP
```

Or get the IP directly:
```bash
export NGINX_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo $NGINX_IP
```


Apply Ingress

```bash
kubectl apply -f manifests/ingress.yaml
```
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

### Available Dashboards

- **Card Approval API** - Request rates, latency, errors
- **Kubernetes Cluster** - Node/pod metrics
- **NGINX Ingress** - Traffic and response codes

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

## Summary

| Service | URL | Notes |
|---------|-----|-------|
| **Swagger UI** | `http://<IP>/docs` | Interactive API documentation |
| **Health Check** | `http://<IP>/health` | API health status |
| **Grafana** | `http://<IP>/grafana/` | Dashboards & trace viewer |
| **MLflow** | `http://<IP>/mlflow/` | Model registry |

---

## Next Steps

1. **[View Traces](05_Tracing.md)** - See request traces in Grafana
