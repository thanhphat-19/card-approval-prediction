# Setup & Configuration Guide

Complete guide to setup and configure the Card Approval Prediction MLOps project.

---

## Prerequisites

**Required Tools:**
- GCP Account with billing enabled
- `gcloud` CLI installed and authenticated
- `kubectl` installed
- `helm` v3+ installed
- `terraform` v1.6+ installed
- `ansible` installed (for Jenkins deployment)
- `docker` installed

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

## Step 5: Build & Push Docker Image

```bash
source config.env

# Configure Docker for Artifact Registry
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

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

1. **[Helm Deployment](01_Helm_Deployment.md)** - Deploy all services to Kubernetes
2. **[Model Training](02_MLflow_Training.md)** - Train and register models
3. **[CI/CD Pipeline](03_CICD_Pipeline.md)** - Setup Jenkins automation
4. **[Monitoring](05_Monitoring.md)** - Configure Prometheus & Grafana
