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
