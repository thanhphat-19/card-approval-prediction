# Helm Deployment Guide

Deploy all infrastructure components to Kubernetes using Helm.

> **Note:** The Card Approval API is deployed via CI/CD pipeline (see [03_CICD_Pipeline.md](03_CICD_Pipeline.md)). This guide covers infrastructure setup only.

```
helm-charts/
├── card-approval/              # API + PostgreSQL + Redis (deployed via CI/CD)
├── card-approval-training/     # MLflow + PostgreSQL
└── infrastructure/
    ├── nginx-ingress/          # NGINX Ingress Controller
    ├── card-approval-monitoring/ # Prometheus, Grafana, Loki
    └── tempo/                  # Distributed Tracing
```

## Deployment Order

```
Step 1: NGINX Ingress → Get LoadBalancer IP
        ↓
Step 2: MLflow Training Stack → Model Registry
        ↓
Step 3: Monitoring Stack → Prometheus, Grafana, Loki
        ↓
Step 4: Tempo → Distributed Tracing
        ↓
Step 5: Apply Ingress Rules
        ↓
(Train Model - see 02_MLflow_Training.md)
        ↓
(CI/CD deploys API - see 03_CICD_Pipeline.md)
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
# Build dependencies
helm dependency build helm-charts/card-approval-training

# Deploy
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
# All pods should be Running
```

> **Next:** Train a model using [02_MLflow_Training.md](02_MLflow_Training.md) before deploying the API.

---

## Step 3: Deploy Monitoring Stack

```bash
# Build dependencies
helm dependency build helm-charts/infrastructure/card-approval-monitoring

# Deploy
helm upgrade --install monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring --create-namespace \
  --set kube-prometheus.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"
```

**Verify:**
```bash
kubectl get pods -n monitoring
# All pods should be Running
```

---

## Step 4: Deploy Tempo (Distributed Tracing)

```bash
# Build dependencies
helm dependency build helm-charts/infrastructure/tempo

# Deploy
helm upgrade --install tempo helm-charts/infrastructure/tempo \
  -n monitoring --create-namespace \
  --set tempo.tempo.storage.trace.gcs.bucket_name="${GCS_BUCKET_NAME}" \
  --set tempo.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}"
```

**Verify:**
```bash
kubectl get pods -n monitoring -l app.kubernetes.io/name=tempo
# tempo-0 should be Running
```

---

## Step 5: Apply Ingress Rules

```bash
kubectl apply -f manifests/ingress.yaml

# Verify ingress
kubectl get ingress -A
```

---

## Step 6: Verify All Deployments

```bash
# Check all Helm releases
helm list -A

# All pods
kubectl get pods -A | grep -E "card-approval|monitoring|ingress"

# Check services
kubectl get svc -A | grep -E "card-approval|monitoring|nginx"
```

**Expected namespaces:**
- `ingress-nginx` - NGINX Ingress Controller
- `card-approval-training` - MLflow + PostgreSQL
- `monitoring` - Prometheus, Grafana, Loki, Tempo


## Port Forwarding (for local access)

```bash
# MLflow UI
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training

# Grafana
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

# Prometheus
kubectl port-forward svc/prometheus-monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring
```

---

## Uninstall

```bash
helm uninstall tempo -n monitoring
helm uninstall monitoring -n monitoring
helm uninstall card-approval-training -n card-approval-training
helm uninstall nginx-ingress -n ingress-nginx
kubectl delete namespace card-approval card-approval-training monitoring ingress-nginx
```

---

## Summary

| Component | Namespace | Access |
|-----------|-----------|--------|
| NGINX Ingress | `ingress-nginx` | LoadBalancer IP |
| MLflow | `card-approval-training` | `http://<IP>/mlflow` |
| Grafana | `monitoring` | `http://<IP>/grafana` |
| Prometheus | `monitoring` | Port-forward only |
| Tempo | `monitoring` | Internal only |

---

## Next Steps

1. **[Train Model](02_MLflow_Training.md)** - Register a model to MLflow
2. **[Setup CI/CD](03_CICD_Pipeline.md)** - Deploy API via Jenkins pipeline
3. **[Access Services](04_NGINX.md)** - Use LoadBalancer IP to access services
4. **[View Traces](05_Tracing.md)** - Monitor requests in Grafana
