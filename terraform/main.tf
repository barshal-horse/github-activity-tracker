terraform {
  required_version = ">= 1.0"
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

# ============================================================
# Google Cloud Storage — Data Lake
# ============================================================
resource "google_storage_bucket" "data_lake" {
  name          = "${var.gcs_bucket_name}-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90 # Auto-delete after 90 days to save costs
    }
    action {
      type = "Delete"
    }
  }
}

# ============================================================
# BigQuery — Data Warehouse
# ============================================================
resource "google_bigquery_dataset" "github_analytics" {
  dataset_id    = var.bq_dataset
  friendly_name = "GitHub Analytics"
  description   = "Data warehouse for GitHub open source activity tracker"
  location      = var.region

  delete_contents_on_destroy = true
}

# External table pointing to processed Parquet in GCS
resource "google_bigquery_table" "external_events" {
  dataset_id = google_bigquery_dataset.github_analytics.dataset_id
  table_id   = "external_github_events"

  deletion_protection = false

  external_data_configuration {
    autodetect    = true
    source_format = "PARQUET"
    source_uris   = ["gs://${google_storage_bucket.data_lake.name}/processed/events/*.parquet"]
  }

  depends_on = [google_bigquery_dataset.github_analytics]
}
