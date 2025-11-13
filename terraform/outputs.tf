output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

# GKE Outputs
output "gke_cluster_name" {
  description = "GKE Autopilot cluster name"
  value       = google_container_cluster.primary.name
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}

# GCS Outputs
output "gcs_bucket" {
  description = "GCS bucket for all data (data/models/mlflow)"
  value       = google_storage_bucket.data.name
}

output "gcs_bucket_url" {
  description = "GCS bucket URL"
  value       = "gs://${google_storage_bucket.data.name}"
}

# Artifact Registry Outputs
output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "docker_push_example" {
  description = "Example docker push command"
  value       = "docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/recsys-api:latest"
}
