# Helm Deployment Guide

## Overview

This guide covers deploying all components to Kubernetes using Helm charts.

```
helm-charts/
├── card-approval/              # API stack (FastAPI + PostgreSQL + Redis)
├── card-approval-training/     # Training stack (MLflow + PostgreSQL)
└── infrastructure/             # Shared infrastructure
    ├── postgres/
    ├── mlflow/
    └── card-approval-monitoring/
```

---

# **Step 1: Verify Cluster Connection**

```bash
kubectl get nodes
```

**What this does:**
- Verifies you're connected to the GKE cluster
- Shows available nodes

**Expected output:**
```bash
NAME                                          STATUS   ROLES    AGE   VERSION
gke-card-approval-primary-node-pool-xxxxx     Ready    <none>   1d    v1.28.x
```

**If no nodes or error:**
```bash
gcloud container clusters get-credentials card-approval-prediction-mlops-gke \
  --zone us-east1-b --project product-recsys-mlops
```

---

# **Step 2: Deploy Training Stack**

```bash
helm upgrade --install card-approval-training helm-charts/card-approval-training \
  -n card-approval-training --create-namespace
```

**What this does:**
1. Creates namespace `card-approval-training`
2. Deploys PostgreSQL for MLflow metadata
3. Deploys MLflow tracking server
4. Configures GCS for artifact storage

**Output you'll see:**
```bash
Release "card-approval-training" does not exist. Installing it now.
NAME: card-approval-training
NAMESPACE: card-approval-training
STATUS: deployed
```

**Verify deployment:**
```bash
kubectl get pods -n card-approval-training
```

**Expected output:**
```bash
NAME                                          READY   STATUS    RESTARTS   AGE
card-approval-training-mlflow-xxxxx           1/1     Running   0          2m
card-approval-training-postgres-0             1/1     Running   0          2m
```

**Access MLflow UI:**
```bash
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training
# Open http://localhost:5000
```

---

# **Step 3: Deploy API Stack**

```bash
helm upgrade --install card-approval helm-charts/card-approval \
  -n card-approval --create-namespace
```

**What this does:**
1. Creates namespace `card-approval`
2. Deploys PostgreSQL for application data
3. Deploys Redis for caching
4. Deploys FastAPI application
5. Configures connection to MLflow

**Output you'll see:**
```bash
Release "card-approval" does not exist. Installing it now.
NAME: card-approval
NAMESPACE: card-approval
STATUS: deployed
```

**Verify deployment:**
```bash
kubectl get pods -n card-approval
```

**Expected output:**
```bash
NAME                                    READY   STATUS    RESTARTS   AGE
card-approval-api-xxxxx                 1/1     Running   0          2m
card-approval-postgres-0                1/1     Running   0          2m
card-approval-redis-0                   1/1     Running   0          2m
```

**Test API:**
```bash
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
curl http://localhost:8000/health
```

---

# **Step 4: Deploy Monitoring Stack**

```bash
helm upgrade --install monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring --create-namespace
```

**What this does:**
1. Creates namespace `monitoring`
2. Deploys Prometheus for metrics
3. Deploys Grafana for dashboards
4. Deploys Loki for logs
5. Deploys Alloy for log collection

**Verify deployment:**
```bash
kubectl get pods -n monitoring
```

**Expected output:**
```bash
NAME                                    READY   STATUS    RESTARTS   AGE
prometheus-server-xxxxx                 1/1     Running   0          2m
grafana-xxxxx                           1/1     Running   0          2m
loki-0                                  1/1     Running   0          2m
alloy-xxxxx                             1/1     Running   0          2m
```

**Access Grafana:**
```bash
kubectl port-forward svc/grafana 3000:80 -n monitoring
# Open http://localhost:3000
# Default: admin / admin
```

---

# **Step 5: Verify All Deployments**

```bash
kubectl get pods -A | grep -E "card-approval|monitoring"
```

**Expected output:**
```bash
card-approval           card-approval-api-xxxxx           1/1     Running   0     5m
card-approval           card-approval-postgres-0          1/1     Running   0     5m
card-approval           card-approval-redis-0             1/1     Running   0     5m
card-approval-training  card-approval-training-mlflow-xx  1/1     Running   0     5m
card-approval-training  card-approval-training-postgres-0 1/1     Running   0     5m
monitoring              prometheus-server-xxxxx           1/1     Running   0     5m
monitoring              grafana-xxxxx                     1/1     Running   0     5m
```

---

# **Step 6: Uninstall (if needed)**

```bash
# Uninstall API stack
helm uninstall card-approval -n card-approval

# Uninstall training stack
helm uninstall card-approval-training -n card-approval-training

# Uninstall monitoring
helm uninstall monitoring -n monitoring

# Delete namespaces
kubectl delete namespace card-approval card-approval-training monitoring
```

---

## Summary

| Component | Namespace | Helm Release | Main Service |
|-----------|-----------|--------------|--------------|
| API | `card-approval` | `card-approval` | `card-approval-api:80` |
| Training | `card-approval-training` | `card-approval-training` | `card-approval-training-mlflow:5000` |
| Monitoring | `monitoring` | `monitoring` | `grafana:80` |

**Total deployment time:** ~5-10 minutes
