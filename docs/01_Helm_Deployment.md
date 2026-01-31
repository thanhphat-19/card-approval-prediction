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

# Update Helm dependencies
helm dependency update helm-charts/infrastructure/nginx-ingress

# Deploy NGINX Ingress Controller
helm upgrade --install nginx-ingress helm-charts/infrastructure/nginx-ingress \
  -n ingress-nginx --create-namespace

# Wait for LoadBalancer IP
kubectl get svc -n ingress-nginx -w

# Get the external IP (save this for DNS/access)
kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

```

---

## Step 2: Deploy Training Stack (MLflow)

```bash
helm upgrade --install card-approval-training helm-charts/card-approval-training \
  -n card-approval-training --create-namespace \
  --set postgres.password="${POSTGRES_MLFLOW_PASSWORD}" \
  --set mlflow.postgres.password="${POSTGRES_MLFLOW_PASSWORD}" \
  --set mlflow.gcs.bucket="${GCS_BUCKET_NAME}" \
  --set mlflow.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}"
```

**Verify:**
```bash
kubectl get pods -n card-approval-training
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training
# Open http://localhost:5000
```

**Experiment with Mlflow**:
```bash

cd training
python scripts/download_data.py
python scripts/run_preprocessing.py
python scripts/run_training.py
```
**Noted**: You need to train the model and push to GCS before deploy the API Stack - Completed the [Model Training Guide](02_MLflow_Training.md)

---

## Step 3: Deploy API Stack

```bash
helm upgrade --install card-approval helm-charts/card-approval \
  -n card-approval --create-namespace \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}
```

**Verify:**
```bash
kubectl get pods -n card-approval
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
curl http://localhost:8000/health
```

## Step 4: Deploy Monitoring Stack

```bash
helm upgrade --install monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring --create-namespace \
  --set kube-prometheus.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"
```

**Verify:**
```bash
kubectl get pods -n monitoring
# Grafana
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
# Prometheus
kubectl port-forward svc/prometheus-monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring
# Open http://localhost:3000
```

---

## Step 5: Verify Deployments

```bash
# Check all releases
helm list -A
# All pods
kubectl get pods -A | grep -E "card-approval|monitoring"

# Specific namespace
kubectl get pods -n card-approval
kubectl get pods -n card-approval-training
kubectl get pods -n monitoring
```


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
