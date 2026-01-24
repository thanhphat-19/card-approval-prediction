# Helm Deployment Guide

Deploy all components to Kubernetes using Helm.

```
helm-charts/
├── card-approval/              # API + PostgreSQL + Redis
├── card-approval-training/     # MLflow + PostgreSQL
└── infrastructure/             # Monitoring, Ingress
```

---

## Step 1: Deploy Nginx Ingress

```bash
source config.env
helm upgrade --install nginx-ingress helm-charts/infrastructure/nginx-ingress \
  -n ingress-nginx --create-namespace
```

---

## Step 2: Deploy Training Stack (MLflow)

```bash
helm upgrade --install card-approval-training helm-charts/card-approval-training \
  -n card-approval-training --create-namespace \
  --set postgres.password="${POSTGRES_MLFLOW_PASSWORD}" \
  --set mlflow.postgres.password="${POSTGRES_MLFLOW_PASSWORD}" \
  --set mlflow.gcs.bucket="${GCS_BUCKET_NAME}"
```

**Verify:**
```bash
kubectl get pods -n card-approval-training
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training
# Open http://localhost:5000
```

---

## Step 3: Deploy API Stack

```bash
helm upgrade --install card-approval helm-charts/card-approval \
  -n card-approval --create-namespace \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}"
```

**Verify:**
```bash
kubectl get pods -n card-approval
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
curl http://localhost:8000/health
```

---

## Step 4: Verify Deployments

```bash
# Check pods
kubectl get pods -A | grep -E "card-approval"

# Port forward to access services
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
```

**Access:**
- MLflow: http://localhost:5000
- API: http://localhost:8000/docs

> For monitoring setup, see [05_Monitoring.md](05_Monitoring.md)

---

## Uninstall

```bash
helm uninstall card-approval -n card-approval
helm uninstall card-approval-training -n card-approval-training
helm uninstall monitoring -n monitoring
kubectl delete namespace card-approval card-approval-training monitoring
```

---

## Summary

| Component | Namespace | Port Forward |
|-----------|-----------|--------------|
| MLflow | `card-approval-training` | `5000:5000` |
| API | `card-approval` | `8000:80` |
| Grafana | `monitoring` | `3000:80` |
