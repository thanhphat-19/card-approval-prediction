# Helm Deployment Guide

Deploy all infrastructure components to Kubernetes using Helm.

## Chart Structure

```
helm-charts/
├── card-approval/                  # Application stack (umbrella chart)
│   └── dependencies:
│       ├── api      → infrastructure/card-approval-api
│       ├── postgres → infrastructure/postgres
│       └── redis    → infrastructure/redis
│
├── card-approval-training/         # Training stack (umbrella chart)
│   └── dependencies:
│       ├── mlflow   → infrastructure/mlflow
│       └── postgres → infrastructure/postgres
│
└── infrastructure/                 # Reusable base charts
    ├── card-approval-api/          # API deployment templates
    ├── card-approval-monitoring/   # Prometheus + Grafana + Loki + Alloy
    ├── mlflow/                     # MLflow tracking server
    ├── nginx-ingress/              # NGINX Ingress Controller
    ├── postgres/                   # PostgreSQL database
    ├── redis/                      # Redis cache
    └── tempo/                      # Distributed tracing
```

**Design principle:** `card-approval/` and `card-approval-training/` are umbrella charts that compose infrastructure charts as dependencies. This enables reuse and consistent configuration.

---

## Deployment Order

Follow this exact order to ensure all dependencies are met:

1. **NGINX Ingress** - Entry point for all external traffic
2. **MLflow Training Stack** - Deploy and train model first
3. **Train Model** - Follow [02_MLflow_Training.md](02_MLflow_Training.md)
4. **Monitoring Stack** - Prometheus, Grafana, Loki for observability
5. **Tempo** - Distributed tracing backend
6. **Application Stack** - Deploy API (via CI/CD or manual)
7. **Ingress Rules** - Configure routing

> **Prerequisites:** Ensure `config.env` is sourced: `source config.env`

## Step 1: Deploy Nginx Ingress

```bash

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

> **Next:** Train a model using [02_MLflow_Training.md](02_MLflow_Training.md) before continuing.

---
## Step 3: Deploy Application Stacks


> **Note:** The Card Approval API will be deployed via CI/CD pipeline (see [03_CICD_Pipeline.md](03_CICD_Pipeline.md)). But, at the first time, you need to manually download the model from MLflow and deploy it.

```bash
helm upgrade --install card-approval helm-charts/card-approval \
  -n card-approval --create-namespace \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --set api.config.modelPath="" \
  --set api.tracing.enabled=true \
  --set api.tracing.exporterEndpoint="http://tempo.monitoring:4317" \
  --set api.tracing.samplingRate="1.0"
```

**Key Parameter:** `--set api.config.modelPath=""` tells the API to load the model from MLflow instead of the embedded `/app/models` directory.

**Verify:**
```bash
kubectl get pods -n card-approval
# All pods should be Running
```


---


## Step 4: Deploy Monitoring Stack

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

## Step 5: Deploy Tempo

```bash
# Build dependencies
helm dependency build helm-charts/infrastructure/tempo

# Add Workload Identity binding for Tempo
gcloud iam service-accounts add-iam-policy-binding ${GCP_MLFLOW_SERVICE_ACCOUNT} \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[monitoring/tempo-sa]" \
  --project=${GCP_PROJECT_ID}

# Grant bucket access for traces storage
gcloud storage buckets add-iam-policy-binding gs://${GCS_BUCKET_NAME} \
  --member="serviceAccount:${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --role="roles/storage.legacyBucketReader"

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

# Verify port 3200 is exposed (critical for Grafana queries)
kubectl get svc tempo -n monitoring -o jsonpath='{.spec.ports[*].name}' | grep tempo-http

# If tempo-http is missing, patch the service:
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
```

> **⚠️ Important:** Port 3200 must be exposed for Grafana to query traces. Port 4317 (OTLP gRPC) is for receiving traces from applications.

---

## Step 6: Apply Ingress Rules

```bash
kubectl apply -f manifests/ingress.yaml

# Verify ingress
kubectl get ingress -A
```

---

## Step 7: Verify All Deployments

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

---



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

3. **[Setup CI/CD](03_CICD_Pipeline.md)** - Deploy API via Jenkins pipeline
