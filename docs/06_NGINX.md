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

Then, run

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

### API Documentation Endpoints

| Endpoint | Description |
|----------|-------------|
| `/docs` | Swagger UI (Interactive) |
| `/redoc` | ReDoc (Alternative UI) |
| `/openapi.json` | OpenAPI Schema (JSON) |
| `/health` | Health check |
| `/metrics` | Prometheus metrics |

---

### Test via Swagger

1. Open `http://<NGINX_IP>/docs`
2. Click `POST /api/v1/predict` → "Try it out"
3. Use sample body:
```json
{
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
}
```

---

## Grafana (Monitoring)

### Access Grafana

```bash
open http://<NGINX_IP>/grafana/

# Example
open http://34.139.72.244/grafana/
```

> ⚠️ **Note:** Trailing slash `/grafana/` is required!

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

> ⚠️ **Note:** Trailing slash `/mlflow/` is required!

### MLflow Features

- **Experiments** - View training runs and metrics
- **Models** - Registered models and versions
- **Artifacts** - Model files, plots, configs

### View Registered Models

1. Open MLflow UI
2. Click "Models" tab
3. Find `card_approval_model`
4. Check versions and stages (Staging/Production)

---

## Ingress Configuration Reference

| Path | Service | Namespace | Port |
|------|---------|-----------|------|
| `/` | card-approval-api | card-approval | 80 |
| `/grafana/` | monitoring-grafana | monitoring | 80 |
| `/mlflow/` | card-approval-training-mlflow | card-approval-training | 5000 |

---

## Troubleshooting

### Service returns 404

```bash
# Check pods are running
kubectl get pods -n card-approval
kubectl get pods -n monitoring
kubectl get pods -n card-approval-training

# Check ingress status
kubectl describe ingress -A
```

### Grafana shows "Page not found"

**Ensure trailing slash:**
```bash
# Wrong
http://34.139.72.244/grafana

# Correct
http://34.139.72.244/grafana/
```

**Check Grafana root_url config:**
```bash
kubectl get cm monitoring-grafana -n monitoring -o yaml | grep root_url
# Should show: root_url = %(protocol)s://%(domain)s/grafana/
```

### MLflow shows blank page

**Ensure trailing slash:**
```bash
# Wrong
http://34.139.72.244/mlflow

# Correct
http://34.139.72.244/mlflow/
```

**Check MLflow static files:**
```bash
kubectl logs -n card-approval-training -l app=mlflow --tail=50
```

### Connection timeout

```bash
# Check NGINX Ingress Controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50
```

---

## Quick Reference Commands

```bash
# Get LoadBalancer IP
export NGINX_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo $NGINX_IP



# Test all services
curl -I http://$NGINX_IP/health          # API
curl -I http://$NGINX_IP/docs             # Swagger
curl -I http://$NGINX_IP/grafana/         # Grafana
curl -I http://$NGINX_IP/mlflow/          # MLflow

# View logs
kubectl logs -n card-approval -l app=card-approval-api --tail=50
kubectl logs -n monitoring -l app.kubernetes.io/name=grafana --tail=50
kubectl logs -n card-approval-training -l app=mlflow --tail=50
```

---

## Summary

| Service | URL | Notes |
|---------|-----|-------|
| **Swagger UI** | `http://<IP>/docs` | API documentation |
| **ReDoc** | `http://<IP>/redoc` | Alternative API docs |
| **Grafana** | `http://<IP>/grafana/` | Trailing slash required |
| **MLflow** | `http://<IP>/mlflow/` | Trailing slash required |
| **Health Check** | `http://<IP>/health` | API health |
| **Metrics** | `http://<IP>/metrics` | Prometheus metrics |
