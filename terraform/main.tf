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
# GKE Cluster (Autopilot - Minimal Cost)
# ============================================
resource "google_container_cluster" "primary" {
  name     = "${var.project_id}-gke"
  location = var.region

  # Enable Autopilot mode (no node management, pay per pod)
  enable_autopilot = true

}

# ============================================
# Cloud Storage Buckets
# ============================================

# Single bucket for all data
resource "google_storage_bucket" "data" {
  name          = "${var.project_id}-recsys-data"
  location      = var.region
  force_destroy = true  # Allow deletion for dev

  uniform_bucket_level_access = true

  # Lifecycle rule to reduce costs
  lifecycle_rule {
    condition {
      age = 90  # Delete files older than 90 days
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
  member             = "serviceAccount:${var.project_id}.svc.id.goog[recsys-training/mlflow-sa]"
}
