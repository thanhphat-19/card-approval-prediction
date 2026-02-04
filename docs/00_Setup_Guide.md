# Setup & Configuration Guide

Complete guide to setup and configure the Card Approval Prediction MLOps project.



## Prerequisites

### Required Tools:
- GCP Account with billing enabled
- `gcloud` CLI installed and authenticated
- `kubectl` installed
- `helm` v3+ installed
- `terraform` v1.6+ installed
- `ansible` installed (for Jenkins deployment)
- `docker` installed

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
| **Project ID** | `card-appoval-prediction-mlops` | GCP Project |
| **Region** | `us-east1` | Primary region |
| **Zone** | `us-east1-b` | Primary zone |
| **GKE Cluster** | `card-approval-prediction-mlops-gke` | Kubernetes cluster |
| **GCS Bucket** | `card-appoval-prediction-data` | MLflow artifacts |
| **Service Account** | `mlflow-gcs@card-appoval-prediction-mlops.iam.gserviceaccount.com` | Workload Identity |
| **Artifact Registry** | `us-east1-docker.pkg.dev/card-appoval-prediction-mlops/card-appoval-prediction-mlops-recsys` | Docker images |

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
GCP_PROJECT_ID=card-appoval-prediction-mlops
GCP_REGION=us-east1
GCP_ZONE=us-east1-b
GCS_BUCKET_NAME=card-appoval-prediction-data
POSTGRES_APP_PASSWORD=<strong-password>
POSTGRES_MLFLOW_PASSWORD=<strong-password>
GRAFANA_ADMIN_PASSWORD=<strong-password>
```

## Step 2: Development Environment

```bash
# Install MiniConda
https://docs.conda.io/en/latest/miniconda.html#installing

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
terraform plan
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
| `PROJECT_ID` | `card-appoval-prediction-mlops` | GCP Project |
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
```yaml
api:
  tracing:
    enabled: true
    serviceName: "card-approval-api"
    exporterEndpoint: "http://tempo.monitoring:4317"
    samplingRate: "0.1"
```

**MLflow Stack** (`helm-charts/card-approval-training/values.yaml`):
```yaml
mlflow:
  gcs:
    bucket: "card-approval-preidction-data"
    artifactPath: "mlflow-artifacts"
```

---

## Next Steps

1. **[Helm Deployment](01_Helm_Deployment.md)** - Deploy NGINX, MLflow, Monitoring, Tempo
