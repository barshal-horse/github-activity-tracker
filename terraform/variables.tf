variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket_name" {
  description = "Name prefix for the GCS data lake bucket"
  type        = string
  default     = "gh-archive-data-lake"
}

variable "bq_dataset" {
  description = "BigQuery dataset name"
  type        = string
  default     = "github_analytics"
}
