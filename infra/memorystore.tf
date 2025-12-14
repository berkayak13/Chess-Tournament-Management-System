# ============================================================================
# Memorystore - Redis Cache
# ============================================================================

# Redis Instance
resource "google_redis_instance" "cache" {
  name           = var.redis_name
  tier           = "BASIC"
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region
  project        = var.project_id

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"

  labels = local.labels

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Outputs
output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.cache.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.cache.port
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
}
