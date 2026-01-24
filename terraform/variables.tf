variable "project_id" {
  description = "The GCP project ID to host the cluster in"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-east1"
}

variable "zone" {
  description = "GCP zone for zonal resources (GKE cluster)"
  type        = string
  default     = "us-east1-b"
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
  default     = "card-approval-prediction-gke"
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "min_node_count" {
  description = "Minimum number of nodes in the node pool"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes in the node pool"
  type        = number
  default     = 2
}
