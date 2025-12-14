# ============================================================================
# Artifact Registry - Container Registry
# ============================================================================

# Artifact Registry Repository
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "chess-tournament"
  description   = "Chess Tournament Management System container images"
  format        = "DOCKER"
  project       = var.project_id

  labels = local.labels

  depends_on = [google_project_service.apis]
}

# Outputs
output "registry_url" {
  description = "Artifact Registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "app_image_url" {
  description = "Full image URL for the Flask app"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/${var.app_image_name}:${var.app_image_tag}"
}
