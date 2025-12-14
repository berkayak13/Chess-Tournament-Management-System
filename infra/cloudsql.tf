# ============================================================================
# Cloud SQL - MySQL Instance
# ============================================================================

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "${var.db_instance_name}-${local.resource_suffix}"
  database_version = "MYSQL_8_0"
  region           = var.region
  project          = var.project_id

  deletion_protection = false  # Set to true in production

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_size         = 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled            = true
      binary_log_enabled = true
      start_time         = "03:00"
    }

    maintenance_window {
      day          = 7  # Sunday
      hour         = 3
      update_track = "stable"
    }

    database_flags {
      name  = "character_set_server"
      value = "utf8mb4"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    user_labels = local.labels
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Database
resource "google_sql_database" "main" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  charset  = "utf8mb4"
}

# Database User
resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  password = var.db_password
  project  = var.project_id
}

# Store DB password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "chess-tournament-db-password"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

# Output connection details
output "db_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "db_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.main.private_ip_address
}

output "db_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.main.name
}
