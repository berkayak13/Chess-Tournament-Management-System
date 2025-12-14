# Deployment Guide

This guide covers deploying the Chess Tournament Management System to Google Cloud Platform.

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and authenticated
- Terraform >= 1.0 installed
- Docker installed (for building container images)
- `kubectl` installed
- A GCP project with billing enabled

## Quick Start

```bash
# 1. Clone and navigate to the repository
cd Chess-Tournament-Management-System

# 2. Set up GCP project
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# 3. Enable required APIs
gcloud services enable \
  compute.googleapis.com \
  container.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  servicenetworking.googleapis.com

# 4. Deploy infrastructure
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform apply

# 5. Build and push container image
cd ..
export REGION=us-central1
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/chess-tournament/app:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/chess-tournament/app:latest

# 6. Deploy to Kubernetes
gcloud container clusters get-credentials chess-tournament-cluster --region $REGION
kubectl apply -f k8s/
```

## Detailed Steps

### 1. Infrastructure Setup (Terraform)

The `infra/` directory contains Terraform modules for:

| File | Resources |
|------|-----------|
| `networking.tf` | VPC, subnets, firewall rules, Cloud NAT |
| `cloudsql.tf` | Cloud SQL MySQL instance, database, user |
| `gke.tf` | GKE cluster and node pool |
| `vm.tf` | Compute Engine VM for background worker |
| `memorystore.tf` | Redis instance for caching |
| `registry.tf` | Artifact Registry for container images |
| `functions.tf` | Cloud Function for audit logging |

#### Configuration

Create `infra/terraform.tfvars`:

```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"
zone       = "us-central1-a"

# Database
db_password = "strong-password-here"

# Domain (optional, for HTTPS)
domain_name = "chess.yourdomain.com"

# Environment
environment = "production"
```

#### Apply Infrastructure

```bash
cd infra
terraform init
terraform plan
terraform apply
```

This creates:
- VPC with private subnets
- Cloud SQL MySQL instance (private IP)
- GKE cluster with autoscaling node pool
- Memorystore Redis instance
- Compute Engine VM for worker
- Cloud Function for audit logging
- Artifact Registry repository

### 2. Database Migration

After Cloud SQL is created, initialize the database:

```bash
# Get Cloud SQL connection name
INSTANCE_NAME=$(terraform output -raw cloudsql_instance_name)

# Connect via Cloud SQL Proxy
cloud_sql_proxy -instances=${PROJECT_ID}:${REGION}:${INSTANCE_NAME}=tcp:3306 &

# Run schema setup
mysql -h 127.0.0.1 -u chessapp -p < ../code/triggers.sql

# Optionally load sample data
mysql -h 127.0.0.1 -u chessapp -p < ../code/insert_statements.sql
```

### 3. Build Container Image

```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/chess-tournament/app:latest .

# Push to registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/chess-tournament/app:latest
```

### 4. Deploy to Kubernetes

#### Update Kubernetes Secrets

Create `k8s/secrets.yaml` from the example:

```bash
cp k8s/secrets.yaml.example k8s/secrets.yaml
```

Edit with base64-encoded values:
```bash
echo -n 'your-db-password' | base64
```

#### Apply Manifests

```bash
# Get cluster credentials
gcloud container clusters get-credentials chess-tournament-cluster --region $REGION

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply all resources
kubectl apply -f k8s/
```

#### Verify Deployment

```bash
# Check pods
kubectl get pods -n chess-tournament

# Check service
kubectl get svc -n chess-tournament

# Check ingress (may take a few minutes for IP)
kubectl get ingress -n chess-tournament

# View logs
kubectl logs -f deployment/chess-tournament-app -n chess-tournament
```

### 5. Deploy Worker

The worker VM is automatically provisioned by Terraform with a startup script. To manually deploy:

```bash
# SSH to worker VM
gcloud compute ssh chess-tournament-worker --zone $ZONE

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip
pip3 install mysql-connector-python google-cloud-secret-manager

# Deploy worker
sudo cp /path/to/worker/worker.py /opt/chess-worker/
sudo cp /path/to/worker/systemd/worker.service /etc/systemd/system/
sudo systemctl enable chess-worker
sudo systemctl start chess-worker

# Check status
sudo systemctl status chess-worker
journalctl -u chess-worker -f
```

### 6. Deploy Cloud Function

```bash
cd cloud-function-http

gcloud functions deploy audit_log \
  --gen2 \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --region $REGION \
  --set-env-vars AUDIT_BUCKET=chess-tournament-audit-logs \
  --vpc-connector chess-tournament-connector

# Get function URL
gcloud functions describe audit_log --region $REGION --format='value(serviceConfig.uri)'
```

Update the `FUNCTION_URL` in your Kubernetes ConfigMap with this URL.

## Monitoring

### View Logs

```bash
# GKE application logs
kubectl logs -f deployment/chess-tournament-app -n chess-tournament

# Worker logs
gcloud compute ssh chess-tournament-worker --zone $ZONE -- journalctl -u chess-worker -f

# Cloud Function logs
gcloud functions logs read audit_log --region $REGION
```

### Metrics

- **GKE**: View in Cloud Console > Kubernetes Engine > Workloads
- **Cloud SQL**: Cloud Console > SQL > Instance > Monitoring
- **HPA**: `kubectl get hpa -n chess-tournament`

## Scaling

### Manual Scaling

```bash
kubectl scale deployment chess-tournament-app --replicas=5 -n chess-tournament
```

### HPA Configuration

The HPA automatically scales based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)

Min replicas: 2, Max replicas: 10

## Troubleshooting

### Pod not starting

```bash
kubectl describe pod <pod-name> -n chess-tournament
kubectl logs <pod-name> -n chess-tournament
```

### Database connection issues

1. Verify Cloud SQL is running
2. Check VPC connectivity
3. Verify credentials in secrets
4. Check Cloud SQL Proxy sidecar logs

### Redis connection issues

1. Verify Memorystore instance is running
2. Check VPC peering is established
3. Verify `REDIS_URL` in ConfigMap

## Cleanup

To destroy all infrastructure:

```bash
# Delete Kubernetes resources first
kubectl delete -f k8s/

# Destroy Terraform resources
cd infra
terraform destroy
```

## Security Notes

- Database password stored in Secret Manager
- Cloud SQL accessible only via private IP
- GKE nodes in private subnet
- Cloud Function requires VPC connector for DB access
- Consider enabling Cloud Armor for DDoS protection
- Enable SSL/TLS for HTTPS (managed certificate via Ingress)
