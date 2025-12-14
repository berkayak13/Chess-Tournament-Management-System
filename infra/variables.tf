# ============================================================================
# Chess Tournament Management System - Terraform Variables
# ============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Network
variable "network_name" {
  description = "VPC Network name"
  type        = string
  default     = "chess-tournament-vpc"
}

# GKE
variable "gke_cluster_name" {
  description = "GKE Cluster name"
  type        = string
  default     = "chess-tournament-cluster"
}

variable "gke_node_count" {
  description = "Number of nodes in GKE cluster"
  type        = number
  default     = 2
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-small"
}

# Cloud SQL
variable "db_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "chess-tournament-db"
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "chessdb"
}

variable "db_user" {
  description = "Database username"
  type        = string
  default     = "chess_app"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# VM Worker
variable "worker_vm_name" {
  description = "Worker VM instance name"
  type        = string
  default     = "chess-tournament-worker"
}

variable "worker_machine_type" {
  description = "Machine type for worker VM"
  type        = string
  default     = "e2-micro"
}

# Redis / Memorystore
variable "redis_name" {
  description = "Memorystore Redis instance name"
  type        = string
  default     = "chess-tournament-cache"
}

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# Container Registry
variable "app_image_name" {
  description = "Container image name for the Flask app"
  type        = string
  default     = "chess-tournament-app"
}

variable "app_image_tag" {
  description = "Container image tag"
  type        = string
  default     = "latest"
}
