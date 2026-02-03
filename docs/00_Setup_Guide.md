# Setup & Configuration Guide

Complete guide to setup and configure the Card Approval Prediction MLOps project.

---

## Deployment Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROJECT DEPLOYMENT FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Setup & Config (this doc)                                               │
│         ↓                                                                   │
│  2. Terraform → GKE, GCS, Artifact Registry                                │
│         ↓                                                                   │
│  3. Helm Deployments (01_Helm_Deployment.md)                               │
│      ├── NGINX Ingress                                                      │
│      ├── MLflow Training Stack                                              │
│      ├── Monitoring (Prometheus, Grafana, Loki)                            │
│      └── Tempo (Distributed Tracing)                                       │
│         ↓                                                                   │
│  4. Train Model (02_MLflow_Training.md)                                    │
│         ↓                                                                   │
│  5. CI/CD Pipeline (03_CICD_Pipeline.md)                                   │
│      └── Git Push → Jenkins → Build → Deploy API                           │
│         ↓                                                                   │
│  6. Access Services (04_NGINX.md)                                          │
│         ↓                                                                   │
│  7. View Traces (05_Tracing.md)                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| `gcloud` CLI | Latest | [Install Guide](https://cloud.google.com/sdk/docs/install) |
| `kubectl` | 1.28+ | `gcloud components install kubectl` |
| `helm` | 3.12+ | [Install Guide](https://helm.sh/docs/intro/install/) |
| `terraform` | 1.6+ | [Install Guide](https://developer.hashicorp.com/terraform/install) |
| `docker` | 24+ | [Install Guide](https://docs.docker.com/engine/install/) |
| `ansible` | 2.15+ | `pip install ansible` |
| `python` | 3.11 | [Install Guide](https://www.python.org/downloads/) |

### Verify Installation

```bash
# Check all tools are installed
gcloud version
kubectl version --client
helm version
terraform version
docker --version
ansible --version
python --version
```

### GCP Project Setup

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  compute.googleapis.com
```

---

## Configuration Reference

### GCP Resources

| Resource | Value | Description |
|----------|-------|-------------|
| **Project ID** | `product-recsys-mlops` | GCP Project |
| **Region** | `us-east1` | Primary region |
| **Zone** | `us-east1-b` | Primary zone |
| **GKE Cluster** | `card-approval-prediction-mlops-gke` | Kubernetes cluster |
| **GCS Bucket** | `product-recsys-mlops-recsys-data` | MLflow artifacts |
| **Service Account** | `mlflow-gcs@product-recsys-mlops.iam.gserviceaccount.com` | Workload Identity |
| **Artifact Registry** | `us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys` | Docker images |

### Key Configuration Files

| File | Purpose |
|------|---------|
| `config.env` | Infrastructure variables (passwords, GCP settings) |
| `terraform/terraform.tfvars` | Terraform input variables |
| `Jenkinsfile` | CI/CD pipeline configuration |
| `helm-charts/*/values.yaml` | Kubernetes deployment settings |

---

## Step 1: Clone & Configure

```bash
git clone https://github.com/thanhphat-19/card-approval-prediction.git
cd card-approval-prediction

# Copy and edit configuration files
cp config-example.env config.env
# Edit config.env: Set GCP_PROJECT_ID, passwords, service accounts

cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars: Set project_id
```

**Key variables to configure in `config.env`:**
```bash
GCP_PROJECT_ID=product-recsys-mlops
GCP_REGION=us-east1
GCP_ZONE=us-east1-b
GCS_BUCKET_NAME=product-recsys-mlops-recsys-data
POSTGRES_APP_PASSWORD=<strong-password>
POSTGRES_MLFLOW_PASSWORD=<strong-password>
GRAFANA_ADMIN_PASSWORD=<strong-password>
```

## Step 2: Development Environment

```bash
# Install MiniConda (if not already installed)
# https://docs.conda.io/en/latest/miniconda.html#installing

# Create virtual environment
conda create -n card-approval python=3.11
conda activate card-approval

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pip install pre-commit
pre-commit install
```

---

## Step 3: Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply
```

This creates: GKE cluster, GCS bucket, Artifact Registry, IAM roles.

---

## Step 4: Connect to Cluster

```bash
gcloud container clusters get-credentials card-approval-prediction-mlops-gke \
  --zone us-east1-b --project $GCP_PROJECT_ID
kubectl get nodes
```

---

## Step 5: Setup Workload Identity

Workload Identity allows Kubernetes pods to access GCP services without service account keys.

```bash
source config.env

# 1. Bind K8s Service Accounts to GCP Service Account
# For MLflow (card-approval-training namespace)
gcloud iam service-accounts add-iam-policy-binding ${GCP_MLFLOW_SERVICE_ACCOUNT} \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[card-approval-training/card-approval-training-mlflow-sa]" \
  --project=${GCP_PROJECT_ID}

# For API (card-approval namespace)
gcloud iam service-accounts add-iam-policy-binding ${GCP_MLFLOW_SERVICE_ACCOUNT} \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[card-approval/card-approval-api-sa]" \
  --project=${GCP_PROJECT_ID}

# For Tempo (monitoring namespace)
gcloud iam service-accounts add-iam-policy-binding ${GCP_MLFLOW_SERVICE_ACCOUNT} \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[monitoring/tempo-sa]" \
  --project=${GCP_PROJECT_ID}

# 2. Grant bucket-level permissions (required for Tempo)
gcloud storage buckets add-iam-policy-binding gs://${GCS_BUCKET_NAME} \
  --member="serviceAccount:${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --role="roles/storage.legacyBucketReader"
```

---

## Step 6: Build & Push Docker Image

```bash
source config.env

# Configure Docker for Artifact Registry
gcloud auth configure-docker ${DOCKER_REGISTRY}

# Build and push
docker build -t card-approval-api:latest .
docker tag card-approval-api:latest \
  ${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest
docker push ${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest
```

---

## Configuration Details

### Jenkins CI/CD Variables

Configured in `Jenkinsfile` environment block:

| Variable | Value | Purpose |
|----------|-------|---------|
| `PROJECT_ID` | `product-recsys-mlops` | GCP Project |
| `GKE_CLUSTER` | `card-approval-prediction-mlops-gke` | Target cluster |
| `GKE_NAMESPACE` | `card-approval` | Deployment namespace |
| `IMAGE_NAME` | `card-approval-api` | Docker image name |
| `MLFLOW_TRACKING_URI` | `http://<IP>/mlflow` | MLflow server |
| `MODEL_NAME` | `card_approval_model` | Model registry name |
| `MODEL_STAGE` | `Production` | Model stage |
| `F1_THRESHOLD` | `0.90` | Quality gate |

### Jenkins Credentials

Configure in **Manage Jenkins → Credentials**:

| ID | Type | Purpose |
|----|------|---------|
| `gcp-service-account` | Secret file | GCP authentication |
| `gcp-project-id` | Secret text | Project reference |
| `github-credentials` | Username/password | Clone repository |
| `github-pat` | Secret text | PR status updates |
| `sonarqube-token` | Secret text | Code analysis |

### Helm Chart Values

**API Stack** (`helm-charts/card-approval/values.yaml`):
```yaml
api:
  image:
    repository: us-east1-docker.pkg.dev/.../card-approval-api
    tag: latest
  env:
    MLFLOW_TRACKING_URI: "http://card-approval-training-mlflow:5000"
    MODEL_NAME: "card_approval_model"
    MODEL_STAGE: "Production"
```

**MLflow Stack** (`helm-charts/card-approval-training/values.yaml`):
```yaml
mlflow:
  gcs:
    bucket: "product-recsys-mlops-recsys-data"
    artifactPath: "mlflow-artifacts"
```

---

## Next Steps

1. **[Helm Deployment](01_Helm_Deployment.md)** - Deploy NGINX, MLflow, Monitoring, Tempo
2. **[Model Training](02_MLflow_Training.md)** - Train and register models to MLflow
3. **[CI/CD Pipeline](03_CICD_Pipeline.md)** - Setup Jenkins for automated deployments
4. **[NGINX Access](04_NGINX.md)** - Access all services via LoadBalancer
5. **[Distributed Tracing](05_Tracing.md)** - View traces in Grafana
