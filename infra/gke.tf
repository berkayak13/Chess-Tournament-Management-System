# ============================================================================
# GKE - Kubernetes Cluster
# ============================================================================

# Service Account for GKE nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "gke-nodes-${local.resource_suffix}"
  display_name = "GKE Nodes Service Account"
  project      = var.project_id
}

# IAM roles for GKE node service account
resource "google_project_iam_member" "gke_nodes_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/artifactregistry.reader",
    "roles/secretmanager.secretAccessor",
    "roles/cloudsql.client",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = var.gke_cluster_name
  location = var.zone
  project  = var.project_id

  # Use a separately managed node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.gke_subnet.id

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Enable network policy
  network_policy {
    enabled = true
  }

  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
  }

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  resource_labels = local.labels

  depends_on = [google_project_service.apis]
}

# GKE Node Pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.gke_cluster_name}-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name
  node_count = var.gke_node_count
  project    = var.project_id

  node_config {
    machine_type = var.gke_machine_type
    disk_size_gb = 30
    disk_type    = "pd-standard"

    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = local.labels

    tags = ["gke-node", var.gke_cluster_name]
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Outputs
output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

# kubectl config command
output "gke_connect_command" {
  description = "Command to connect to GKE cluster"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone ${var.zone} --project ${var.project_id}"
}
