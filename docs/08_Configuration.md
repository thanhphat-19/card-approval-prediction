# Configuration Reference

This document lists all configuration variables used across the project.

---

## Jenkins CI/CD (`Jenkinsfile`)

| Variable | Value | Description |
|----------|-------|-------------|
| `PROJECT_ID` | `product-recsys-mlops` | GCP Project ID |
| `ZONE` | `us-east1-b` | GCP Zone |
| `REGION` | `us-east1` | GCP Region |
| `GKE_CLUSTER` | `card-approval-prediction-mlops-gke` | GKE cluster name |
| `GKE_NAMESPACE` | `card-approval` | Kubernetes namespace |
| `REGISTRY` | `us-east1-docker.pkg.dev` | Artifact Registry URL |
| `REPOSITORY` | `product-recsys-mlops/product-recsys-mlops-recsys` | Docker repository |
| `IMAGE_NAME` | `card-approval-api` | Docker image name |
| `MLFLOW_TRACKING_URI` | `http://34.139.72.244/mlflow` | MLflow server URL |
| `MODEL_NAME` | `card_approval_model` | MLflow model name |
| `MODEL_STAGE` | `Production` | Model stage to deploy |
| `F1_THRESHOLD` | `0.90` | Model quality gate threshold |
| `SONAR_HOST_URL` | `http://sonarqube:9000` | SonarQube server URL |

---

## Jenkins Credentials

Configure in **Manage Jenkins → Credentials**:

| Credential ID | Type | Description |
|---------------|------|-------------|
| `gcp-service-account` | Secret file | GCP service account JSON key |
| `sonarqube-token` | Secret text | SonarQube authentication token |
| `github-credentials` | Username/password | GitHub username + PAT |

---

## Helm Values

### Card Approval API (`helm-charts/card-approval/values.yaml`)

```yaml
api:
  image:
    repository: us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api
    tag: latest
  env:
    MLFLOW_TRACKING_URI: "http://card-approval-training-mlflow:5000"
    MODEL_NAME: "card_approval_model"
    MODEL_STAGE: "Production"

postgresql:
  auth:
    database: card_approval_db
    username: app_user
    password: <from-secret>
```

### MLflow Training (`helm-charts/card-approval-training/values.yaml`)

```yaml
mlflow:
  artifactRoot: gs://product-recsys-mlops-recsys-data/mlflow-artifacts

postgresql:
  auth:
    database: mlflow
    username: mlflow
    password: <from-secret>
```

---

## Environment Variables (Runtime)

### API Service

| Variable | Description | Default |
|----------|-------------|---------|
| `MLFLOW_TRACKING_URI` | MLflow server URL | Required |
| `MODEL_NAME` | Registered model name | `card_approval_model` |
| `MODEL_STAGE` | Model stage | `Production` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP key | Optional (uses Workload Identity) |

### Model Evaluation Script

```bash
# Run locally
export MLFLOW_TRACKING_URI=http://34.139.72.244/mlflow
export MODEL_NAME=card_approval_model
export MODEL_STAGE=Production

python scripts/evaluate_model.py --threshold 0.90
```

---

## GCP Resources

| Resource | Name/ID |
|----------|---------|
| Project | `product-recsys-mlops` |
| GKE Cluster | `card-approval-prediction-mlops-gke` |
| GCS Bucket | `product-recsys-mlops-recsys-data` |
| Service Account | `mlflow-gcs@product-recsys-mlops.iam.gserviceaccount.com` |
| Artifact Registry | `us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys` |

---

## Updating Configuration

1. **Jenkins values** → Edit `Jenkinsfile` environment block
2. **Kubernetes values** → Edit Helm `values.yaml` files
3. **Credentials** → Update in Jenkins UI or K8s Secrets
