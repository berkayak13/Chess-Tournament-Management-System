# ============================================================================
# Terraform Outputs
# ============================================================================

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "vpc_network" {
  description = "VPC Network name"
  value       = google_compute_network.vpc.name
}

# Kubernetes connection info
output "kubernetes_connection_info" {
  description = "Kubernetes connection information"
  value = {
    cluster_name     = google_container_cluster.primary.name
    cluster_endpoint = google_container_cluster.primary.endpoint
    connect_command  = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone ${var.zone} --project ${var.project_id}"
  }
  sensitive = true
}

# Database connection info
output "database_connection_info" {
  description = "Database connection information"
  value = {
    instance_name    = google_sql_database_instance.main.name
    connection_name  = google_sql_database_instance.main.connection_name
    private_ip       = google_sql_database_instance.main.private_ip_address
    database_name    = var.db_name
    database_user    = var.db_user
  }
  sensitive = true
}

# Application configuration for Kubernetes
output "app_config" {
  description = "Application configuration for Kubernetes deployment"
  value = {
    image_url    = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/${var.app_image_name}:${var.app_image_tag}"
    db_host      = google_sql_database_instance.main.private_ip_address
    redis_url    = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
    function_url = google_cloudfunctions2_function.audit_logger.service_config[0].uri
  }
  sensitive = true
}

# Docker push commands
output "docker_commands" {
  description = "Commands to build and push Docker image"
  value       = <<-EOT
    # Configure Docker for Artifact Registry
    gcloud auth configure-docker ${var.region}-docker.pkg.dev

    # Build image
    docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/${var.app_image_name}:${var.app_image_tag} .

    # Push image
    docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/${var.app_image_name}:${var.app_image_tag}
  EOT
}
