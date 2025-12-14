# ============================================================================
# Compute Engine VM - Background Worker
# ============================================================================

# Service Account for Worker VM
resource "google_service_account" "worker" {
  account_id   = "worker-vm-${local.resource_suffix}"
  display_name = "Worker VM Service Account"
  project      = var.project_id
}

# IAM roles for Worker service account
resource "google_project_iam_member" "worker_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# Worker VM Instance
resource "google_compute_instance" "worker" {
  name         = var.worker_vm_name
  machine_type = var.worker_machine_type
  zone         = var.zone
  project      = var.project_id

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 20
      type  = "pd-standard"
    }
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.worker_subnet.id

    # No external IP - use Cloud NAT for outbound
  }

  service_account {
    email  = google_service_account.worker.email
    scopes = ["cloud-platform"]
  }

  # Startup script to install Python and worker
  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e

    # Update system
    apt-get update
    apt-get install -y python3 python3-pip python3-venv git

    # Create worker directory
    mkdir -p /opt/chess-worker
    cd /opt/chess-worker

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Install dependencies
    pip install mysql-connector-python google-cloud-secret-manager

    # Download worker script (would come from GCS or git in production)
    cat > worker.py << 'WORKER'
${file("${path.module}/../worker/worker.py")}
WORKER

    # Create systemd service
    cat > /etc/systemd/system/chess-worker.service << 'SERVICE'
[Unit]
Description=Chess Tournament Stats Worker
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chess-worker
ExecStart=/opt/chess-worker/venv/bin/python worker.py
Restart=always
RestartSec=10
Environment=DB_HOST=${google_sql_database_instance.main.private_ip_address}
Environment=DB_USER=${var.db_user}
Environment=DB_NAME=${var.db_name}
Environment=GCP_PROJECT=${var.project_id}

[Install]
WantedBy=multi-user.target
SERVICE

    # Enable and start service
    systemctl daemon-reload
    systemctl enable chess-worker
    systemctl start chess-worker
  EOF

  tags = ["worker", "ssh"]

  labels = local.labels

  # Allow stopping for updates
  allow_stopping_for_update = true

  depends_on = [
    google_sql_database_instance.main,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Outputs
output "worker_vm_name" {
  description = "Worker VM instance name"
  value       = google_compute_instance.worker.name
}

output "worker_vm_internal_ip" {
  description = "Worker VM internal IP"
  value       = google_compute_instance.worker.network_interface[0].network_ip
}
