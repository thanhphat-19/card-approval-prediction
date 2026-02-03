# Component 3: Terraform Infrastructure

## Executive Summary

Terraform manages the Google Cloud Platform infrastructure as code, provisioning GKE clusters, Cloud Storage buckets, Artifact Registry for Docker images, and IAM service accounts with Workload Identity. This enables reproducible, version-controlled infrastructure that supports the entire MLOps pipeline.

---

## 1. Concept & Theory

### What is Infrastructure as Code (IaC)?

Infrastructure as Code treats infrastructure provisioning like software development:
- **Version Control**: Track infrastructure changes in Git
- **Code Review**: Review infrastructure changes before applying
- **Reproducibility**: Recreate identical environments
- **Automation**: No manual clicking in cloud consoles

### Why Terraform for ML Projects?

| Challenge | Terraform Solution |
|-----------|-------------------|
| Inconsistent environments | Same code → same infrastructure |
| Configuration drift | Terraform state detects drift |
| Manual provisioning errors | Declarative syntax prevents mistakes |
| Documentation | Infrastructure IS the documentation |

### Core Terraform Concepts

1. **Providers**: Plugins for cloud platforms (GCP, AWS, Azure)
2. **Resources**: Infrastructure components (VMs, clusters, buckets)
3. **State**: Terraform's record of what exists
4. **Variables**: Parameterize configurations
5. **Outputs**: Export resource attributes

### GCP Resources for MLOps

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP MLOps Infrastructure                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    GKE Cluster                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │  FastAPI    │  │   MLflow    │  │  Monitoring │   │   │
│  │  │    API      │  │   Server    │  │    Stack    │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↓                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐   │
│  │  GCS Bucket     │  │ Artifact Registry│  │   IAM      │   │
│  │  (MLflow arts)  │  │ (Docker images) │  │  Accounts  │   │
│  └─────────────────┘  └─────────────────┘  └────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture & Design Decisions

### Resources Created

| Resource | Purpose |
|----------|---------|
| **GKE Cluster** | Run Kubernetes workloads |
| **Node Pool** | Worker nodes with autoscaling |
| **GCS Bucket** | MLflow artifact storage |
| **Artifact Registry** | Docker image storage |
| **Service Account** | MLflow GCS access |
| **IAM Bindings** | Workload Identity permissions |

### Key Design Decisions

#### 1. Standard GKE (Not Autopilot)
```hcl
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone

  # Standard mode - more control over node configuration
  remove_default_node_pool = true
  initial_node_count       = 1
}
```

**Rationale**: Standard mode gives more control over node types, needed for ML workloads with specific resource requirements.

#### 2. Workload Identity for GCS Access
```hcl
# Enable Workload Identity on cluster
workload_identity_config {
  workload_pool = "${var.project_id}.svc.id.goog"
}

# Bind K8s SA to GCP SA
resource "google_service_account_iam_member" "mlflow_workload_identity" {
  service_account_id = google_service_account.mlflow.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[card-approval-training/mlflow-sa]"
}
```

**Benefit**: No service account keys needed; pods authenticate via K8s service accounts.

#### 3. Autoscaling Node Pool
```hcl
autoscaling {
  min_node_count = var.min_node_count  # 1
  max_node_count = var.max_node_count  # 2
}
```

**Cost Optimization**: Scale down during low usage, scale up for training jobs.

#### 4. Lifecycle Rules for GCS
```hcl
lifecycle_rule {
  condition {
    age = 90  # Days
  }
  action {
    type = "Delete"
  }
}
```

**Rationale**: Auto-delete old artifacts to manage costs.

---

## 3. Implementation Guide

### Directory Structure

```
terraform/
├── main.tf              # Main infrastructure definition
├── variables.tf         # Input variables
├── outputs.tf           # Resource outputs
├── terraform.tfvars.example  # Configuration template
└── provider.tf          # GCP provider configuration
```

### Step-by-Step Implementation

#### Step 1: Provider Configuration

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

#### Step 2: GKE Cluster

```hcl
# terraform/main.tf
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone

  # Standard mode
  remove_default_node_pool = true
  initial_node_count       = 1

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Deletion protection (disable for dev)
  deletion_protection = false
}
```

#### Step 3: Node Pool

```hcl
resource "google_container_node_pool" "primary_nodes" {
  name       = "primary-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name

  initial_node_count = var.min_node_count

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  node_config {
    machine_type = var.machine_type  # e2-standard-4
    disk_size_gb = 30
    disk_type    = "pd-standard"

    # Enable Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      environment = "production"
    }

    tags = ["gke-node", var.cluster_name]
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
```

#### Step 4: Cloud Storage Bucket

```hcl
resource "google_storage_bucket" "data" {
  name          = "${var.project_id}-recsys-data"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}
```

#### Step 5: Artifact Registry

```hcl
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "${var.project_id}-recsys"
  format        = "DOCKER"
  description   = "Docker images for recommendation system"
}
```

#### Step 6: Service Account & IAM

```hcl
# GCP Service Account for MLflow
resource "google_service_account" "mlflow" {
  account_id   = "mlflow-gcs"
  display_name = "MLflow GCS Access"
  description  = "Service account for MLflow to access GCS artifacts"
}

# Grant Storage Object Admin
resource "google_storage_bucket_iam_member" "mlflow_storage_admin" {
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mlflow.email}"
}

# Workload Identity binding
resource "google_service_account_iam_member" "mlflow_workload_identity" {
  service_account_id = google_service_account.mlflow.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[card-approval-training/mlflow-sa]"
}
```

#### Step 7: Variables

```hcl
# terraform/variables.tf
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-east1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-east1-b"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "card-approval-prediction-mlops-gke"
}

variable "machine_type" {
  description = "Node machine type"
  type        = string
  default     = "e2-standard-4"
}

variable "min_node_count" {
  description = "Min nodes"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Max nodes"
  type        = number
  default     = 2
}
```

#### Step 8: Outputs

```hcl
# terraform/outputs.tf
output "cluster_name" {
  value       = google_container_cluster.primary.name
  description = "GKE cluster name"
}

output "cluster_endpoint" {
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
  description = "GKE cluster endpoint"
}

output "gcs_bucket_name" {
  value       = google_storage_bucket.data.name
  description = "GCS bucket for MLflow artifacts"
}

output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
  description = "Artifact Registry URL"
}

output "mlflow_service_account_email" {
  value       = google_service_account.mlflow.email
  description = "MLflow service account email"
}
```

#### Step 9: tfvars Configuration

```hcl
# terraform/terraform.tfvars.example
project_id     = "your-project-id"
region         = "us-east1"
zone           = "us-east1-b"
cluster_name   = "card-approval-prediction-mlops-gke"
machine_type   = "e2-standard-4"
min_node_count = 1
max_node_count = 2
```

### Deployment Commands

```bash
# Initialize Terraform
cd terraform/
terraform init

# Preview changes
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output

# Destroy when done
terraform destroy
```

### Connect to GKE

```bash
# After terraform apply
gcloud container clusters get-credentials \
  card-approval-prediction-mlops-gke \
  --zone us-east1-b \
  --project your-project-id

# Verify connection
kubectl get nodes
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Committing terraform.tfvars | Add to .gitignore |
| State file in Git | Use remote backend (GCS) |
| Hardcoded credentials | Use environment variables |
| No state locking | Configure GCS backend with locking |

### Security Considerations

#### 1. Remote State Backend
```hcl
terraform {
  backend "gcs" {
    bucket = "your-project-terraform-state"
    prefix = "card-approval"
  }
}
```

#### 2. IAM Least Privilege
```hcl
# Only grant necessary permissions
role = "roles/storage.objectAdmin"  # Not roles/owner
```

#### 3. Service Account Key Management
```bash
# Use Workload Identity instead of keys
# If keys needed, rotate regularly
gcloud iam service-accounts keys create ...
```

### Cost Optimization

| Resource | Cost Saving |
|----------|-------------|
| **GKE Nodes** | Use preemptible VMs for dev |
| **GCS** | Lifecycle rules delete old artifacts |
| **Node Pool** | Autoscaling down to 1 node |
| **Region** | Choose cheaper regions if latency allows |

```hcl
# Preemptible nodes (75% cheaper)
node_config {
  preemptible  = true  # For dev/test only
  machine_type = "e2-standard-4"
}
```

### Debugging Guide

```bash
# Check Terraform state
terraform show

# View specific resource
terraform state show google_container_cluster.primary

# Refresh state
terraform refresh

# Import existing resource
terraform import google_container_cluster.primary projects/PROJECT/locations/ZONE/clusters/NAME
```

---

## 5. Testing & Validation

### Validation Checklist

```bash
# After terraform apply:

# 1. Check GKE cluster
gcloud container clusters list

# 2. Check GCS bucket
gsutil ls gs://your-project-recsys-data/

# 3. Check Artifact Registry
gcloud artifacts repositories list

# 4. Check Service Account
gcloud iam service-accounts list

# 5. Test Workload Identity
kubectl run test-pod --image=google/cloud-sdk:slim \
  --overrides='{"spec":{"serviceAccountName":"mlflow-sa"}}' \
  --restart=Never -- gcloud auth list
```

### Infrastructure Tests (Terratest)

```go
// test/terraform_test.go
func TestTerraformGKE(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../terraform",
        Vars: map[string]interface{}{
            "project_id": "test-project",
        },
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    clusterName := terraform.Output(t, terraformOptions, "cluster_name")
    assert.Equal(t, "card-approval-prediction-mlops-gke", clusterName)
}
```

---

## 6. Configuration Reference

### Machine Types for ML

| Type | vCPUs | Memory | Use Case |
|------|-------|--------|----------|
| `e2-standard-2` | 2 | 8 GB | Dev/test |
| `e2-standard-4` | 4 | 16 GB | Production API |
| `n1-standard-8` | 8 | 30 GB | Training jobs |
| `n1-highmem-4` | 4 | 26 GB | Memory-intensive |

### IAM Roles Reference

| Role | Purpose |
|------|---------|
| `roles/storage.objectAdmin` | Read/write GCS |
| `roles/storage.objectViewer` | Read-only GCS |
| `roles/artifactregistry.writer` | Push Docker images |
| `roles/iam.workloadIdentityUser` | Workload Identity |

---

## 7. Further Reading

- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Terraform State Management](https://developer.hashicorp.com/terraform/language/state)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator)
