# Setup Guide

Quick guide to reproduce the Card Approval Prediction project.

## Prerequisites

- GCP Account with billing enabled
- `gcloud` CLI installed and authenticated
- `kubectl` installed
- `helm` v3+ installed
- `terraform` v1.6+ installed
- `ansible` installed (for Jenkins deployment)

---

## Step 1: Clone & Configure

```bash
git clone https://github.com/thanhphat-19/card-approval-prediction.git
cd card-approval-prediction

# Copy Terraform variables
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars: set project_id
```

> 📖 **Configuration Reference**: See [08_Configuration.md](08_Configuration.md) for all configuration values.

## Step 2: Prepare Development Environment

1. Follow steps in [this website](https://docs.conda.io/en/latest/miniconda.html#installing) to install MiniConda.
2. Create and **activate** the virtual environment using conda.
3. Install pre-commit

    ```
    pip install pre-commit
    ```

4. Install Git Hook

    ```
    pre-commit install
    ```


5. Install global dependencies:

    ```
    pip install -r requirements.txt
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
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

docker build -t card-approval-api:latest .
docker tag card-approval-api:latest \
  ${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest
docker push ${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest
```




## Next Steps

1. [Helm Deployment](01_Helm_Deployment.md)
2. [Model Training](02_MLflow_Training.md)
3. [CI/CD Pipeline](04_CICD_Pipeline.md)
4. [Monitoring](05_Monitoring.md)
