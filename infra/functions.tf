# ============================================================================
# Cloud Functions - Serverless Functions
# ============================================================================

# Service Account for Cloud Functions
resource "google_service_account" "functions" {
  account_id   = "cloud-functions-${local.resource_suffix}"
  display_name = "Cloud Functions Service Account"
  project      = var.project_id
}

# IAM roles for Functions service account
resource "google_project_iam_member" "functions_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.functions.email}"
}

# GCS Bucket for function source code
resource "google_storage_bucket" "functions_source" {
  name          = "${var.project_id}-functions-source-${local.resource_suffix}"
  location      = var.region
  project       = var.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  labels = local.labels
}

# GCS Bucket for audit logs (used by the HTTP function)
resource "google_storage_bucket" "audit_logs" {
  name          = "${var.project_id}-audit-logs-${local.resource_suffix}"
  location      = var.region
  project       = var.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90  # Delete logs older than 90 days
    }
  }

  labels = local.labels
}

# Archive the HTTP function source code
data "archive_file" "http_function" {
  type        = "zip"
  source_dir  = "${path.module}/../cloud-function-http"
  output_path = "${path.module}/tmp/http-function.zip"
}

# Upload HTTP function source to GCS
resource "google_storage_bucket_object" "http_function_source" {
  name   = "http-function-${data.archive_file.http_function.output_md5}.zip"
  bucket = google_storage_bucket.functions_source.name
  source = data.archive_file.http_function.output_path
}

# HTTP Cloud Function (Gen 2)
resource "google_cloudfunctions2_function" "audit_logger" {
  name     = "chess-tournament-audit-logger"
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = "python311"
    entry_point = "audit_log"
    source {
      storage_source {
        bucket = google_storage_bucket.functions_source.name
        object = google_storage_bucket_object.http_function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "256M"
    timeout_seconds       = 60
    service_account_email = google_service_account.functions.email

    environment_variables = {
      AUDIT_BUCKET = google_storage_bucket.audit_logs.name
      DB_HOST      = google_sql_database_instance.main.private_ip_address
      DB_NAME      = var.db_name
      DB_USER      = var.db_user
    }

    secret_environment_variables {
      key        = "DB_PASSWORD"
      project_id = var.project_id
      secret     = google_secret_manager_secret.db_password.secret_id
      version    = "latest"
    }

    ingress_settings               = "ALLOW_INTERNAL_AND_GCLB"
    all_traffic_on_latest_revision = true

    vpc_connector                 = google_vpc_access_connector.connector.id
    vpc_connector_egress_settings = "PRIVATE_RANGES_ONLY"
  }

  labels = local.labels

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.db_password
  ]
}

# VPC Access Connector for Cloud Functions to access VPC resources
resource "google_vpc_access_connector" "connector" {
  name          = "chess-vpc-connector"
  region        = var.region
  project       = var.project_id
  network       = google_compute_network.vpc.id
  ip_cidr_range = "10.8.0.0/28"

  depends_on = [google_project_service.apis]
}

# Allow unauthenticated invocations (for internal use with proper auth in code)
resource "google_cloud_run_service_iam_member" "function_invoker" {
  location = var.region
  project  = var.project_id
  service  = google_cloudfunctions2_function.audit_logger.name
  role     = "roles/run.invoker"
  member   = "allUsers"  # Restrict in production
}

# Outputs
output "function_url" {
  description = "HTTP Cloud Function URL"
  value       = google_cloudfunctions2_function.audit_logger.service_config[0].uri
}

output "audit_bucket" {
  description = "Audit logs bucket name"
  value       = google_storage_bucket.audit_logs.name
}
