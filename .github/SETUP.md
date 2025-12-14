# GitHub Actions Setup Guide

This document explains how to configure GitHub Actions for automated CI/CD deployment.

## Required GitHub Secrets

Navigate to your repository: **Settings > Secrets and variables > Actions**

### Required Secrets

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `GCP_PROJECT_ID` | Your GCP project ID | GCP Console > Project selector |
| `GCP_SA_KEY` | Service account JSON key | See [Creating Service Account](#creating-service-account) |
| `TF_STATE_BUCKET` | GCS bucket for Terraform state | See [Creating State Bucket](#creating-state-bucket) |
| `DB_PASSWORD` | Database password | Choose a strong password |

### Optional Secrets

| Secret Name | Description |
|-------------|-------------|
| `APP_URL` | Deployed app URL (for load tests) |

## Creating Service Account

1. Go to **GCP Console > IAM & Admin > Service Accounts**

2. Click **Create Service Account**:
   - Name: `github-actions-deployer`
   - ID: `github-actions-deployer`

3. Grant roles:
   ```
   - Artifact Registry Administrator
   - Cloud Functions Developer
   - Cloud SQL Admin
   - Compute Admin
   - Kubernetes Engine Admin
   - Secret Manager Admin
   - Service Account User
   - Storage Admin
   - Service Networking Admin
   ```

4. Click **Done**, then click on the service account

5. Go to **Keys > Add Key > Create new key > JSON**

6. Copy the entire JSON content and add as `GCP_SA_KEY` secret in GitHub

## Creating State Bucket

```bash
# Set your project
export PROJECT_ID=your-project-id

# Create bucket for Terraform state
gsutil mb -p $PROJECT_ID -l us-central1 gs://${PROJECT_ID}-terraform-state

# Enable versioning (recommended)
gsutil versioning set on gs://${PROJECT_ID}-terraform-state

# Add bucket name as TF_STATE_BUCKET secret
echo "Add '${PROJECT_ID}-terraform-state' as TF_STATE_BUCKET in GitHub secrets"
```

## Workflows Overview

### 1. `deploy.yml` - Main CI/CD Pipeline

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch

**Jobs:**

| Job | Trigger | Description |
|-----|---------|-------------|
| `test` | Always | Run pytest with MySQL service container |
| `build` | Push to main | Build & push Docker image to Artifact Registry |
| `deploy-gke` | Push to main | Update GKE deployment with new image |
| `deploy-function` | Push to main | Deploy Cloud Function |
| `deploy-worker` | Push to main | Update worker script on VM |
| `load-test` | Manual only | Run Locust load tests |

### 2. `terraform.yml` - Infrastructure Pipeline

**Triggers:**
- Push to `main` with changes in `infra/`
- Pull requests with changes in `infra/`
- Manual dispatch

**Jobs:**

| Job | Trigger | Description |
|-----|---------|-------------|
| `terraform-plan` | Always | Validate and plan changes |
| `terraform-apply` | Push to main | Apply infrastructure changes |
| `terraform-destroy` | Manual only | Destroy all infrastructure |

## Initial Setup Steps

### Step 1: Create GCP Project & Enable Billing

```bash
gcloud projects create your-project-id
gcloud beta billing projects link your-project-id --billing-account=BILLING_ACCOUNT_ID
```

### Step 2: Enable Required APIs

```bash
gcloud config set project your-project-id

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
```

### Step 3: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer"

# Get the email
SA_EMAIL="github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant roles
for role in \
  roles/artifactregistry.admin \
  roles/cloudfunctions.developer \
  roles/cloudsql.admin \
  roles/compute.admin \
  roles/container.admin \
  roles/secretmanager.admin \
  roles/iam.serviceAccountUser \
  roles/storage.admin \
  roles/servicenetworking.networksAdmin
do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$role"
done

# Create and download key
gcloud iam service-accounts keys create ~/github-actions-key.json \
  --iam-account=$SA_EMAIL

# Display key (copy this to GitHub secrets)
cat ~/github-actions-key.json
```

### Step 4: Create Terraform State Bucket

```bash
gsutil mb -p $PROJECT_ID -l us-central1 gs://${PROJECT_ID}-terraform-state
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### Step 5: Add Secrets to GitHub

1. Go to repository **Settings > Secrets and variables > Actions**
2. Add the following secrets:

```
GCP_PROJECT_ID = your-project-id
GCP_SA_KEY = <paste entire JSON key content>
TF_STATE_BUCKET = your-project-id-terraform-state
DB_PASSWORD = <choose a strong password>
```

### Step 6: Create GitHub Environment (Optional)

For additional protection on production deployments:

1. Go to **Settings > Environments**
2. Create environment: `production`
3. Add protection rules:
   - Required reviewers (optional)
   - Wait timer (optional)

### Step 7: First Deployment

1. Push to `main` branch:
   ```bash
   git add .
   git commit -m "Add CI/CD workflows"
   git push origin main
   ```

2. The `terraform.yml` workflow will:
   - Plan infrastructure changes
   - Apply them (creates GKE, Cloud SQL, etc.)

3. The `deploy.yml` workflow will:
   - Run tests
   - Build and push Docker image
   - Deploy to GKE
   - Deploy Cloud Function
   - Update worker VM

## Monitoring Workflows

- View workflow runs: **Actions** tab in your repository
- View deployment status: Click on individual workflow run
- Download artifacts: Available in workflow run details

## Troubleshooting

### "Permission denied" errors
- Verify service account has all required roles
- Check if APIs are enabled

### "Bucket not found" for Terraform state
- Create the state bucket first
- Verify `TF_STATE_BUCKET` secret is correct

### GKE deployment fails
- Check if cluster exists (Terraform may not have run yet)
- Verify GKE credentials are being fetched correctly

### Tests fail
- Check if MySQL service container started
- Review test output in workflow logs
