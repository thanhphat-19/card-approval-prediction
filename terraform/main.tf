# Terraform configuration for prod-recsys-project

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

# ============================================
# GKE Cluster (Standard Mode)
# ============================================
resource "google_container_cluster" "primary" {
  name     = "card-approval-prediction-mlops-gke"
  location = "us-east1-b"

  # Standard mode
  remove_default_node_pool = true
  initial_node_count       = 1

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Deletion protection
  deletion_protection = false
}

# ============================================
# GKE Node Pool (Standard Mode)
# ============================================
resource "google_container_node_pool" "primary_nodes" {
  name       = "primary-node-pool"
  location   = "us-east1-b"
  cluster    = google_container_cluster.primary.name

  # Autoscaling configuration
  initial_node_count = 1

  autoscaling {
    min_node_count = 1
    max_node_count = 2
  }

  node_config {
    # Machine type
    machine_type = "e2-standard-4"
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

    tags = ["gke-node", "card-approval-prediction-mlops-gke"]
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# ============================================
# Cloud Storage Buckets
# ============================================

# Single bucket for all data
resource "google_storage_bucket" "data" {
  name          = "${var.project_id}-recsys-data"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  # Lifecycle rule
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# ============================================
# Artifact Registry (for Docker images)
# ============================================
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "${var.project_id}-recsys"
  format        = "DOCKER"
  description   = "Docker images for recommendation system"
}

# ============================================
# MLflow Service Account & Workload Identity
# ============================================

# GCP Service Account for MLflow
resource "google_service_account" "mlflow" {
  account_id   = "mlflow-gcs"
  display_name = "MLflow GCS Access"
  description  = "Service account for MLflow to access GCS artifacts"
}

# Grant Storage Object Admin on the GCS bucket
resource "google_storage_bucket_iam_member" "mlflow_storage_admin" {
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mlflow.email}"
}

# Workload Identity binding: Link K8s SA to GCP SA
# This allows the Kubernetes service account to impersonate the GCP service account
resource "google_service_account_iam_member" "mlflow_workload_identity" {
  service_account_id = google_service_account.mlflow.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[card-approval-training/mlflow-sa]"
}
