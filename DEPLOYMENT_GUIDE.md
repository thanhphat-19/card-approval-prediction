# Card Approval Prediction API - Deployment Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Deployment Steps](#deployment-steps)
- [Configuration](#configuration)
- [Monitoring Setup](#monitoring-setup)
- [Accessing Services](#accessing-services)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## 🎯 Overview

This guide provides complete instructions for deploying the Card Approval Prediction API using **Helm charts** on Google Kubernetes Engine (GKE). The deployment includes:

- **FastAPI application** serving ML predictions
- **PostgreSQL** for data storage
- **Redis** for caching
- **MLflow integration** for model serving
- **Prometheus & Grafana** for monitoring (optional)
- **Auto-scaling** based on resource usage

### Why Helm?

We use Helm charts following the established pattern in this project (`recsys-training`):
- ✅ **Version management** - Easy rollbacks
- ✅ **Dependency management** - Reusable components
- ✅ **Templating** - Environment-specific configurations
- ✅ **Consistency** - Follows existing infrastructure pattern

## 🏗️ Architecture

```
card-approval (Helm umbrella chart)
├── postgres (infrastructure/postgres)
│   ├── PersistentVolumeClaim (5Gi)
│   ├── Deployment
│   └── Service
├── redis (infrastructure/redis)
│   ├── PersistentVolumeClaim (1Gi)
│   ├── Deployment
│   └── Service
└── api (infrastructure/api)
    ├── Deployment (2-10 replicas, HPA)
    ├── Service (ClusterIP)
    ├── ServiceAccount (Workload Identity)
    ├── HorizontalPodAutoscaler
    └── Ingress (optional)

MLflow Connection:
└── Connects to existing recsys-training-mlflow service
```

## 📦 Prerequisites

### Required Tools
```bash
# Check if tools are installed
helm version          # Helm 3.x required
kubectl version       # Kubernetes client
gcloud version        # Google Cloud SDK
docker --version      # Docker (for local testing)
```

### Install Missing Tools
```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kubectl
gcloud components install kubectl

# Configure gcloud
gcloud auth login
gcloud config set project product-recsys-mlops
```

### GKE Cluster
```bash
# Create GKE cluster (if not exists)
gcloud container clusters create mlops-cluster \
    --region us-east1 \
    --num-nodes 3 \
    --machine-type n1-standard-2 \
    --enable-autoscaling \
    --min-nodes 2 \
    --max-nodes 5

# Get credentials
gcloud container clusters get-credentials mlops-cluster \
    --region us-east1
```

### Prerequisites Check
```bash
# Verify MLflow is deployed (required dependency)
kubectl get svc -n recsys-training recsys-training-mlflow

# Should show MLflow service
```

## 📁 Project Structure

```
card-approval-prediction/
├── helm-charts/
│   ├── infrastructure/              # Reusable components
│   │   ├── postgres/               # PostgreSQL chart
│   │   ├── mlflow/                 # MLflow chart
│   │   ├── redis/                  # Redis chart
│   │   └── api/                    # FastAPI application chart
│   │
│   ├── recsys-training/            # Existing: MLflow stack
│   │   ├── Chart.yaml
│   │   └── values.yaml
│   │
│   └── card-approval/              # NEW: API stack
│       ├── Chart.yaml              # Dependencies
│       ├── values.yaml             # Configuration
│       ├── README.md               # Chart documentation
│       └── deploy.sh               # Deployment script
│
├── app/                            # FastAPI application
├── ansible/                        # Jenkins infrastructure
├── Jenkinsfile                     # CI/CD pipeline
└── docker-compose.yml              # Local development
```

## 🚀 Deployment Steps

### Step 1: Review Configuration

Edit the configuration file:
```bash
nano helm-charts/card-approval/values.yaml
```

**Critical settings to review:**
```yaml
# Database credentials (CHANGE THESE!)
postgres:
  password: "CHANGE_ME_STRONG_PASSWORD"

# Redis configuration
redis:
  enabled: true

# API configuration
api:
  image:
    repository: us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api
    tag: "latest"

  # MLflow connection (verify this matches your setup)
  mlflow:
    trackingUri: "http://recsys-training-mlflow.recsys-training.svc.cluster.local:5000"
```

### Step 2: Build Helm Dependencies

```bash
cd helm-charts/card-approval
helm dependency build
cd ../..
```

This creates the `charts/` folder with linked dependencies.

### Step 3: Deploy Using Script (Recommended)

```bash
cd helm-charts
./deploy.sh
```

The script will:
1. Build dependencies
2. Validate chart
3. Create namespace
4. Check MLflow connectivity
5. Install/upgrade the release
6. Verify deployment

### Step 4: Manual Deployment (Alternative)

```bash
helm install card-approval ./helm-charts/card-approval \
  --namespace card-approval \
  --create-namespace \
  --wait \
  --timeout 10m
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n card-approval

# Expected output:
# NAME                                  READY   STATUS    RESTARTS   AGE
# card-approval-api-xxx                 1/1     Running   0          2m
# card-approval-postgres-xxx            1/1     Running   0          2m
# card-approval-redis-xxx               1/1     Running   0          2m

# Check services
kubectl get svc -n card-approval

# Check Helm release
helm list -n card-approval
```

## ⚙️ Configuration

### Environment-Specific Deployments

Create environment-specific value files:

**values-dev.yaml** (Development):
```yaml
api:
  replicaCount: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"
  autoscaling:
    enabled: false
```

**values-prod.yaml** (Production):
```yaml
api:
  replicaCount: 3
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
```

Deploy to specific environment:
```bash
# Development
helm install card-approval-dev ./helm-charts/card-approval \
  -n card-approval-dev \
  -f values-dev.yaml

# Production
helm install card-approval-prod ./helm-charts/card-approval \
  -n card-approval-prod \
  -f values-prod.yaml
```

### Using External Databases

To use external PostgreSQL/Redis instead of bundled ones:

```yaml
# Disable internal databases
postgres:
  enabled: false

redis:
  enabled: false

# Configure external connections
api:
  postgres:
    host: "external-db.example.com"
    port: 5432
    database: "card_approval_db"
    username: "app_user"
    password: "secure_password"

  redis:
    host: "external-redis.example.com"
    port: 6379
```

### Secrets Management (Recommended)

Instead of storing passwords in `values.yaml`:

```bash
# Create Kubernetes secret
kubectl create secret generic db-credentials \
  --from-literal=username=app_user \
  --from-literal=password=<strong-password> \
  -n card-approval

# Reference in deployment (future enhancement)
```

### Workload Identity (GKE)

For accessing GCS or other GCP services:

```yaml
api:
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: "card-approval-api@product-recsys-mlops.iam.gserviceaccount.com"
```

Then bind the GCP service account:
```bash
gcloud iam service-accounts add-iam-policy-binding \
  card-approval-api@product-recsys-mlops.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:product-recsys-mlops.svc.id.goog[card-approval/card-approval-api-sa]"
```

## 📊 Monitoring Setup

### Option 1: Using Kube-Prometheus Stack (Recommended)

```bash
# Add Prometheus community repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install monitoring stack
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin123

# Access Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Open: http://localhost:3000 (admin/admin123)
```

### Option 2: Minimal Prometheus (Lightweight)

```bash
# Install Prometheus only
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --create-namespace

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus-server 9090:80
```

### Verify Metrics Collection

```bash
# Port-forward to API
kubectl port-forward -n card-approval svc/card-approval-api 8000:80

# Check metrics endpoint
curl http://localhost:8000/metrics

# Should show Prometheus metrics:
# fastapi_requests_total
# fastapi_request_duration_seconds
# etc.
```

## 🔌 Accessing Services

### Local Access (Development)

**API:**
```bash
kubectl port-forward -n card-approval svc/card-approval-api 8000:80

# Access endpoints:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
# - Metrics: http://localhost:8000/metrics
```

**PostgreSQL:**
```bash
kubectl port-forward -n card-approval svc/card-approval-postgres 5432:5432

# Connect with psql
psql -h localhost -U app_user -d card_approval_db
```

**Redis:**
```bash
kubectl port-forward -n card-approval svc/card-approval-redis 6379:6379

# Connect with redis-cli
redis-cli -h localhost -p 6379
```

### External Access (Production)

**Option 1: LoadBalancer**
```bash
helm upgrade card-approval ./helm-charts/card-approval \
  -n card-approval \
  --set api.service.type=LoadBalancer \
  --reuse-values

# Get external IP
kubectl get svc card-approval-api -n card-approval
```

**Option 2: Ingress (Recommended)**
```yaml
# In values.yaml
api:
  ingress:
    enabled: true
    className: "nginx"
    host: "card-approval-api.example.com"
    annotations:
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

## 🔧 Maintenance

### Upgrading the Deployment

**Update image tag:**
```bash
helm upgrade card-approval ./helm-charts/card-approval \
  -n card-approval \
  --set api.image.tag=v1.2.3 \
  --reuse-values
```

**Update configuration:**
```bash
# Edit values.yaml, then:
helm upgrade card-approval ./helm-charts/card-approval \
  -n card-approval \
  --values values.yaml
```

**With atomic rollback:**
```bash
helm upgrade card-approval ./helm-charts/card-approval \
  -n card-approval \
  --atomic \
  --timeout 10m
```

### Rollback

```bash
# View release history
helm history card-approval -n card-approval

# Rollback to previous version
helm rollback card-approval -n card-approval

# Rollback to specific revision
helm rollback card-approval 3 -n card-approval
```

### Scaling

**Manual scaling:**
```bash
kubectl scale deployment card-approval-api \
  -n card-approval \
  --replicas=5
```

**Update HPA:**
```yaml
api:
  autoscaling:
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 60
```

### Backup

**Database backup:**
```bash
# Dump PostgreSQL
kubectl exec -n card-approval deployment/card-approval-postgres -- \
  pg_dump -U app_user card_approval_db > backup.sql

# Restore
kubectl exec -i -n card-approval deployment/card-approval-postgres -- \
  psql -U app_user card_approval_db < backup.sql
```

### Uninstalling

```bash
# Uninstall release
helm uninstall card-approval -n card-approval

# PVCs are retained by default. To delete:
kubectl delete pvc -n card-approval --all

# Delete namespace
kubectl delete namespace card-approval
```

## 🔍 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n card-approval

# Describe pod for events
kubectl describe pod <pod-name> -n card-approval

# Check logs
kubectl logs -f deployment/card-approval-api -n card-approval

# Check recent events
kubectl get events -n card-approval --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
kubectl run -it --rm debug \
  --image=postgres:15-alpine \
  --restart=Never \
  -n card-approval -- \
  psql -h card-approval-postgres -U app_user -d card_approval_db

# Check PostgreSQL logs
kubectl logs -f deployment/card-approval-postgres -n card-approval
```

### MLflow Connection Issues

```bash
# Verify MLflow is accessible from card-approval namespace
kubectl run -it --rm debug \
  --image=curlimages/curl \
  --restart=Never \
  -n card-approval -- \
  curl http://recsys-training-mlflow.recsys-training.svc.cluster.local:5000/health

# Should return {"status": "OK"}
```

### Helm Issues

```bash
# Check Helm release status
helm status card-approval -n card-approval

# View history
helm history card-approval -n card-approval

# Get rendered manifests
helm get manifest card-approval -n card-approval

# Validate chart before installing
helm lint ./helm-charts/card-approval

# Dry run
helm install card-approval ./helm-charts/card-approval \
  -n card-approval \
  --dry-run \
  --debug
```

### Image Pull Issues

```bash
# Check if image exists
gcloud artifacts docker images list \
  us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys

# Configure Docker auth (if needed)
gcloud auth configure-docker us-east1-docker.pkg.dev

# Create image pull secret (if using private registry)
kubectl create secret docker-registry gcr-secret \
  --docker-server=us-east1-docker.pkg.dev \
  --docker-username=_json_key \
  --docker-password="$(cat gcp-key.json)" \
  -n card-approval
```

## 📝 Testing

### Health Check
```bash
kubectl port-forward -n card-approval svc/card-approval-api 8000:80
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "mlflow_connected": true,
#   "database_connected": true,
#   "redis_connected": true
# }
```

### Prediction Test
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008804,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 180000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -14000,
    "DAYS_EMPLOYED": -2500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2.0
  }'
```

### Load Testing
```bash
# Install hey
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 http://localhost:8000/health
```

## 🎓 Best Practices

1. **Always use `--atomic` flag** for production deployments
2. **Test in dev/staging** before production
3. **Use Kubernetes secrets** for sensitive data
4. **Enable monitoring** from day one
5. **Regular backups** of PostgreSQL data
6. **Pin image tags** (avoid `latest` in production)
7. **Set resource limits** to prevent resource exhaustion
8. **Use HPA** for automatic scaling
9. **Monitor logs and metrics** continuously
10. **Document configuration** changes

## 📚 Additional Resources

- [Helm Chart Documentation](helm-charts/card-approval/README.md)
- [CI/CD Pipeline Guide](CI_CD_README.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

## 🆘 Support

### Useful Commands Cheatsheet
```bash
# Check all resources
kubectl get all -n card-approval

# View Helm releases
helm list -A

# Get pod logs
kubectl logs -f deployment/card-approval-api -n card-approval

# Execute command in pod
kubectl exec -it deployment/card-approval-api -n card-approval -- /bin/bash

# Port-forward multiple services
kubectl port-forward -n card-approval svc/card-approval-api 8000:80 &
kubectl port-forward -n card-approval svc/card-approval-postgres 5432:5432 &
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &

# Clean up port-forwards
killall kubectl
```

### Getting Help
For issues or questions:
1. Check logs: `kubectl logs -f deployment/card-approval-api -n card-approval`
2. Check events: `kubectl get events -n card-approval --sort-by='.lastTimestamp'`
3. Review Helm status: `helm status card-approval -n card-approval`
4. Open an issue in the repository

---

**Happy Deploying! 🚀**
