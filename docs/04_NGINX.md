# Accessing Services via NGINX Ingress

## Overview

Public services are exposed through NGINX Ingress Controller. Internal tools are accessed via port-forward.

**Public (via NGINX):**
- **Card Approval API** - Swagger UI, ReDoc, API endpoints
- **Grafana** - Monitoring dashboards
- **MLflow** - Experiment tracking UI

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





## Summary

| Service | URL | Notes |
|---------|-----|-------|
| **Swagger UI** | `http://<IP>/docs` | API documentation |
| **ReDoc** | `http://<IP>/redoc` | Alternative API docs |
| **Grafana** | `http://<IP>/grafana/` | Trailing slash required |
| **MLflow** | `http://<IP>/mlflow/` | Trailing slash required |
