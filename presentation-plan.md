# Chess Tournament Management System - Cloud Computing Presentation Plan

## PowerPoint Presentation Structure

---

### Slide 1: Title Slide
- **Chess Tournament Management System**
- Cloud Computing Course Project
- Your Name, Date

---

### Slide 2: Project Overview
- What the application does (tournament management, player ratings, match tracking)
- Why cloud computing? (scalability, reliability, cost efficiency)
- Technology stack summary: Python Flask, MySQL, Redis, GCP

---

### Slide 3: Architecture Diagram (Critical slide)
Include a visual diagram showing:
- Users → Load Balancer → GKE (Flask App) → Cloud SQL / Redis
- Cloud Functions (Audit Logger)
- Background Worker VM
- All within a VPC

**Explanation:** How components communicate via private networking

---

### Slide 4: Cloud Provider - Google Cloud Platform
Services used:

| Service | Purpose |
|---------|---------|
| GKE | Container orchestration |
| Cloud SQL | Managed MySQL database |
| Memorystore | Redis caching |
| Cloud Functions | Serverless audit logging |
| Compute Engine | Background worker |
| Artifact Registry | Docker image storage |
| Secret Manager | Credentials management |

---

### Slide 5: Containerization with Docker
- Multi-stage Dockerfile (optimized image ~200MB)
- Base image: Python 3.11-slim
- Production server: Gunicorn
- Docker Compose for local development
- **Key concept:** Portability - same container runs locally and in cloud

---

### Slide 6: Kubernetes (GKE) - Container Orchestration
Explain these K8s concepts with your examples:
- **Pods:** 2 Flask app replicas
- **Deployment:** Manages pod lifecycle
- **Service:** Internal load balancing (ClusterIP)
- **Ingress:** External HTTP(S) load balancer
- **ConfigMaps & Secrets:** Configuration management

---

### Slide 7: Horizontal Pod Autoscaler (HPA)
- Min replicas: 2, Max: 10
- CPU target: 70%, Memory: 80%
- **Explain:** How it automatically scales based on load
- Scale-up: Quick (15s), Scale-down: Slow (300s stabilization)
- **Cloud computing concept:** Elasticity

---

### Slide 8: Serverless Computing - Cloud Functions
- Function: `chess-tournament-audit-logger`
- Trigger: HTTP
- Runtime: Python 3.11
- **Key benefits:**
  - Pay only when function runs
  - Scales to zero (cost saving)
  - Auto-scales up to 10 instances
- Stores audit logs in Cloud Storage

---

### Slide 9: Database Services - Cloud SQL
- Managed MySQL 8.0 instance
- **Features:**
  - Automatic backups (daily at 03:00 UTC)
  - Point-in-time recovery (binary logging)
  - Private IP only (security)
  - Auto-resize storage
- **Cloud concept:** Database as a Service (DBaaS)

---

### Slide 10: Caching with Redis (Memorystore)
- In-memory data store
- Use cases in your app:
  - Statistics caching (30s TTL)
  - Hall data (5 min TTL)
  - Dashboard data (15s TTL)
- **Cloud concept:** Reduces database load, improves latency

---

### Slide 11: Networking & Security
- **VPC (Virtual Private Cloud):** Isolated network
- **Subnets:**
  - GKE: 10.0.0.0/20
  - Worker: 10.3.0.0/24
  - VPC Connector: 10.8.0.0/28
- **Private IP:** No public database access
- **Cloud NAT:** Outbound internet for private instances
- **Firewall rules:** Allow internal, SSH controlled

---

### Slide 12: Workload Identity & IAM
- **Problem:** How do pods access GCP services securely?
- **Solution:** Workload Identity
  - Kubernetes ServiceAccount → GCP Service Account
  - No credentials in code or config
- **Least privilege principle:** Each component has minimal required permissions

---

### Slide 13: Secrets Management
- Google Secret Manager for sensitive data
- Kubernetes Secrets for pod environment
- GitHub Secrets for CI/CD
- **Never in code:** DB passwords, API keys stored securely

---

### Slide 14: Infrastructure as Code (Terraform)
- 10+ Terraform files managing entire infrastructure
- **Benefits:**
  - Reproducible deployments
  - Version controlled infrastructure
  - Easy to destroy/recreate
- **Files:** networking.tf, gke.tf, cloudsql.tf, etc.

---

### Slide 15: CI/CD Pipeline - GitHub Actions
Show your pipeline stages:
1. **Test:** Run pytest, lint code
2. **Build:** Docker image → Artifact Registry
3. **Deploy to GKE:** kubectl apply
4. **Deploy Cloud Function:** gcloud functions deploy
5. **Update Worker VM:** gcloud scp + restart service
6. **Load Test:** Locust (optional)

---

### Slide 16: Deployment Flow Diagram
Visual showing:
```
git push → GitHub Actions → Build Docker Image →
Push to Artifact Registry → Deploy to GKE →
Update Cloud Function → Update Worker VM
```

---

### Slide 17: Background Worker Pattern
- Compute Engine VM (e2-micro)
- Runs continuously (systemd service)
- Computes aggregated statistics every 5 minutes
- **Why separate?** Offload heavy computation from web tier

---

### Slide 18: Load Testing with Locust
- Simulates different user roles (Player, Coach, Arbiter, Manager)
- Tests scalability and performance
- Generates HTML reports
- **Cloud relevance:** Validates auto-scaling works

---

### Slide 19: Cloud Computing Concepts Applied

| Concept | Implementation |
|---------|---------------|
| **IaaS** | Compute Engine VM |
| **PaaS** | Cloud SQL, GKE, Memorystore |
| **FaaS/Serverless** | Cloud Functions |
| **Elasticity** | HPA auto-scaling |
| **High Availability** | 2+ replicas, regional resources |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions |

---

### Slide 20: Cost Optimization Strategies
- **Right-sizing:** e2-micro for worker, db-f1-micro for dev
- **Serverless:** Functions scale to zero
- **Private IP:** No egress charges for internal traffic
- **Preemptible nodes:** Could be used for non-critical workloads
- **Caching:** Reduces database queries

---

### Slide 21: Challenges & Lessons Learned
- VPC Connector setup for Cloud Functions
- Workload Identity configuration
- Database migrations in cloud environment
- CI/CD debugging and optimization

---

### Slide 22: Demo / Screenshots
- Show application running
- Kubernetes dashboard
- Cloud Console views
- CI/CD pipeline execution

---

### Slide 23: Future Improvements
- Add Cloud Monitoring & Alerting
- Implement Cloud CDN for static assets
- Add Cloud Armor for DDoS protection
- Multi-region deployment

---

### Slide 24: Conclusion
- Successfully deployed full-stack app on GCP
- Leveraged multiple cloud services
- Implemented DevOps best practices
- Achieved scalable, secure architecture

---

### Slide 25: Q&A
- Questions?

---

## Key Talking Points to Emphasize

1. **Why GKE over Cloud Run?** - More control, persistent connections, complex networking
2. **Why separate Worker VM?** - Long-running batch jobs don't fit serverless model
3. **Why Cloud Functions for audit?** - Event-driven, async, scales independently
4. **Private networking importance** - Security best practice, no public DB access
5. **IaC benefits** - Show how Terraform makes infrastructure reproducible

---

## Detailed Technical Information by Topic

### 1. Cloud Infrastructure & Services (GCP)

**Primary Cloud Provider:** Google Cloud Platform (GCP)

**Key Services Used:**
- **Google Kubernetes Engine (GKE)** - Orchestration and compute
- **Cloud SQL** - Managed MySQL database
- **Memorystore (Redis)** - In-memory caching
- **Cloud Functions (Gen 2)** - Serverless functions
- **Compute Engine** - Background worker VM
- **Artifact Registry** - Container image registry
- **Cloud Storage (GCS)** - Audit logs and function source storage
- **Secret Manager** - Secrets management
- **Cloud NAT** - Network address translation
- **VPC & VPC Peering** - Private networking

---

### 2. Containerization Details

**Docker Configuration:**
- **File:** `/Dockerfile`
- **Multi-stage build** for optimized production images
- **Base image:** Python 3.11-slim
- **Production server:** Gunicorn (2 workers, 4 threads each)
- **Port:** 8080
- **Health checks:** HTTP endpoint checks every 30s
- **Environment:** FLASK_ENV=production, PYTHONUNBUFFERED=1

**Docker Compose (Local Development):**
- **File:** `/docker-compose.yml`
- **Services:**
  - Flask app (port 5000→8080)
  - MySQL 8.0 database (port 3307)
  - Redis 7 cache (port 6379)
  - Adminer database management UI (optional dev tool)
- **Networks:** Custom bridge network (chess-network)
- **Volumes:** Persistent MySQL and Redis data volumes

---

### 3. CI/CD Pipelines

**GitHub Actions Workflows:**

**A. Deploy Pipeline** (`.github/workflows/deploy.yml`)
- **Job 1: Test**
  - Runs pytest on all test suites
  - Spins up MySQL service for integration tests
  - Database initialization with schema and triggers
  - Optional flake8 linting
  - Optional test failures allow continuation

- **Job 2: Build & Push Docker Image**
  - Authenticate to GCP via service account
  - Configure Docker for Artifact Registry
  - Multi-tag Docker images (SHA + latest)
  - Push to `${REGION}-docker.pkg.dev/${PROJECT_ID}/chess-tournament/chess-tournament-app`

- **Job 3: Deploy to GKE**
  - Update deployment image reference
  - Uses short SHA (7 chars) for image tagging
  - Rollout status verification (300s timeout)
  - Service and pod verification

- **Job 4: Deploy Cloud Function**
  - Deploys `chess-tournament-audit-logger` (Gen 2)
  - Python 3.11 runtime
  - HTTP trigger
  - 256MB memory, 60s timeout
  - Reads environment variables from secrets

- **Job 5: Update Worker VM**
  - Copy worker script to VM via gcloud scp
  - Restart chess-worker systemd service

- **Job 6: Load Testing** (Manual trigger)
  - Locust load testing framework
  - Generates HTML report artifacts

**B. Terraform Pipeline** (`.github/workflows/terraform.yml`)
- **Job 1: Terraform Plan**
  - Format validation
  - State initialization from GCS bucket
  - Plan generation and artifact upload
  - Posts plan to PR comments

- **Job 2: Terraform Apply**
  - Auto-approval on main branch
  - Requires production environment approval
  - Outputs Terraform values to GitHub step summary

- **Job 3: Terraform Destroy**
  - Manual workflow dispatch only
  - Requires production environment approval

---

### 4. Database Services

**Cloud SQL Configuration:**

**Terraform File:** `/infra/cloudsql.tf`

**Instance Details:**
- **Version:** MySQL 8.0
- **Machine tier:** `db-f1-micro` (configurable)
- **Storage:** 10GB SSD with auto-resize enabled
- **Availability:** Regional (PROD) / Zonal (DEV)
- **Network:** Private IP only (no public IP)
- **Connection:** Via VPC peering

**Backup & Maintenance:**
- Binary logging enabled for point-in-time recovery
- Daily backups at 03:00 UTC
- Sunday maintenance window at 03:00 UTC
- Stable update track

**Database Configuration:**
- **Database:** `chessdb`
- **User:** `chess_app` (application user)
- **Charset:** UTF8MB4 (Unicode support)
- **Max connections:** 100

**Secret Management:**
- Database password stored in Google Secret Manager
- `chess-tournament-db-password` secret ID
- Auto-replication across regions

---

### 5. Kubernetes (Container Orchestration)

**Files:** `/k8s/` directory

**A. Namespace** (`namespace.yaml`)
- Dedicated `chess-tournament` namespace
- Labels for organization

**B. Deployment** (`deployment.yaml`)
- **Container:** Flask app (image: Artifact Registry)
- **Replicas:** 2 (baseline)
- **Ports:** 8080 (HTTP)
- **Service Account:** chess-tournament-app (Workload Identity)

**Environment Configuration:**
- **ConfigMap:** `chess-tournament-config`
  - `db_host` - Cloud SQL private IP
  - `db_name` - chessdb
  - `redis_url` - Memorystore Redis endpoint
  - `function_url` - Cloud Function HTTP endpoint

- **Secrets:** `chess-tournament-secrets`
  - `db_user` - database user
  - `db_password` - database password
  - `secret_key` - Flask secret key

**Resource Limits:**
- **Requests:** 256Mi memory, 100m CPU
- **Limits:** 512Mi memory, 500m CPU

**Health Checks:**
- **Liveness:** HTTP GET `/`, 30s delay, 10s interval, 5s timeout
- **Readiness:** HTTP GET `/`, 5s delay, 5s interval, 3s timeout

**C. Service** (`service.yaml`)
- **Type:** ClusterIP (internal)
- **Port mapping:** 80 → 8080
- **Selector:** app=chess-tournament, component=web

**D. Ingress** (`ingress.yaml`)
- **Class:** GCE (Google Cloud Load Balancer)
- **Static IP:** chess-tournament-ip
- **HTTPS:** Managed certificate (optional)
- **Paths:** /* (all traffic)
- **Backend:** chess-tournament-service

**E. Horizontal Pod Autoscaler (HPA)** (`hpa.yaml`)
- **Min replicas:** 2
- **Max replicas:** 10
- **CPU target:** 70% utilization
- **Memory target:** 80% utilization
- **Scale-up:** 100% per 15s, max 4 pods per 15s
- **Scale-down:** 10% per 60s, 300s stabilization window

**F. Service Account** (`serviceaccount.yaml`)
- **Name:** chess-tournament-app
- **Workload Identity:** Linked to GKE node service account
- **Annotation:** `iam.gke.io/gcp-service-account`

**G. ConfigMap** (`configmap.yaml`)
- Non-sensitive configuration data
- Cloud resource endpoints (private IPs and URLs)

---

### 6. Serverless Functions

**Cloud Functions (Gen 2):**

**Function Name:** `chess-tournament-audit-logger`

**Code Location:** `/cloud-function-http/main.py`

**Configuration:**
- **Runtime:** Python 3.11
- **Trigger:** HTTP (synchronous)
- **Memory:** 256MB
- **Timeout:** 60 seconds
- **Max instances:** 10
- **Min instances:** 0 (scales to zero)

**VPC Integration:**
- **VPC Connector:** `chess-vpc-connector` (10.8.0.0/28)
- **Egress:** PRIVATE_RANGES_ONLY
- **Access:** ALLOW_INTERNAL_AND_GCLB

**Functionality:**
- Receives audit events from Flask application
- **Events tracked:**
  - User login/logout
  - Match creation
  - Match rating submission
  - User creation

**Storage Options:**
- **Primary:** Google Cloud Storage (audit logs bucket)
  - Path structure: `year/month/day/timestamp_event_type.json`
  - Lifecycle: Delete logs older than 90 days
- **Secondary:** Cloud SQL database (optional)
  - Creates `audit_logs` table if not exists
  - Stores event details with indexes on event_type, username, created_at

**Service Account:** `cloud-functions-${resource_suffix}`
**IAM Roles:**
- logging.logWriter
- cloudsql.client
- storage.objectAdmin
- secretmanager.secretAccessor

**Environment Variables:**
- `AUDIT_BUCKET` - GCS bucket name
- `DB_HOST` - Cloud SQL private IP
- `DB_NAME` - chessdb
- `DB_USER` - application user
- `DB_PASSWORD` - from Secret Manager

---

### 7. Background Worker (Microservice)

**Worker VM:**

**Infrastructure:** Compute Engine VM instance

**Configuration:**
- **Name:** chess-tournament-worker
- **Machine type:** e2-micro
- **Image:** Debian 11
- **Disk:** 20GB SSD
- **Network:** Private subnet (no external IP)
- **Service Account:** worker-vm-${resource_suffix}

**IAM Roles:**
- logging.logWriter
- monitoring.metricWriter
- cloudsql.client
- secretmanager.secretAccessor

**Startup Script Automation:**
- Installs Python 3, pip, venv
- Creates `/opt/chess-worker` directory
- Deploys worker.py script
- Creates systemd service: chess-worker.service
- Auto-starts on boot with restart on failure

**Worker Functionality** (`worker/worker.py`):
- Runs continuously with 5-minute intervals (configurable)
- Reads raw tournament data from Cloud SQL
- Computes aggregated statistics:
  - Player ratings and performance metrics
  - Tournament win/loss statistics
  - System-wide statistics
- Writes aggregated results back to `system_stats` table

**Configuration:**
- Database connection via private IP
- Credentials from environment variables
- Logging to stdout (captured by systemd journal)

---

### 8. API Architecture

**Application Framework:** Flask (Python)

**API Structure:**

**A. Web Routes:**
- Authentication endpoints (login, logout)
- Player dashboard and operations
- Coach operations (match management, halls)
- Arbiter operations (rating matches)
- Manager operations (user management, statistics)
- Admin endpoints (system configuration)

**B. Cloud Function Integration:**
- HTTP POST requests to audit logging endpoint
- Non-blocking with 1-second timeout
- Graceful failure handling

**C. Database Integration:**
- MySQL.connector for direct database access
- Connection pooling via app.get_db_connection()
- Prepared statements for SQL injection prevention

**D. Caching Layer:**
- **Redis (Memorystore)** - Production
- **In-memory cache (Simple)** - Development fallback
- Cache timeouts by data type:
  - Statistics: 30 seconds
  - Halls: 5 minutes
  - API tables: 5 minutes
  - Admin stats: 1 minute
  - Dashboard: 15 seconds

---

### 9. Authentication & Authorization

**Flask-Login Integration:**
- User authentication via username/password
- Session-based authentication
- Role-based access control (RBAC)

**User Roles:**
- Player
- Coach
- Arbiter
- Manager
- Admin

**Configuration:**
- Login manager with redirect to login page
- User loader from MySQL database
- Password hashing via Werkzeug
- CSRF protection (enabled in production)
- WTF-CSRF for form protection

**GCP IAM Integration (Kubernetes):**
- **Workload Identity** for pod-to-GCP service account binding
- Service account annotations in Kubernetes
- Automatic credential provisioning

---

### 10. Environment Configuration & Secrets Management

**Configuration Hierarchy:**

**A. Configuration Classes** (`config.py`):
```
- DevelopmentConfig (DEBUG=True, local database)
- TestingConfig (test database, CSRF disabled)
- ProductionConfig (GCP deployment)
```

**B. Environment Variables:**
```
FLASK_ENV=production|development|testing
SECRET_KEY=<secret>
DB_HOST=<private-ip>
DB_PORT=3306
DB_USER=chess_app
DB_PASSWORD=<secret>
DB_NAME=chessdb
REDIS_URL=redis://<host>:<port>/0
FUNCTION_URL=https://chess-tournament-audit-logger-*.a.run.app
CACHE_TIMEOUT=300
COMPUTE_INTERVAL=300
```

**C. Secrets Management:**
- **Google Secret Manager** for sensitive data
  - Database password: `chess-tournament-db-password`
  - Secret rotation and versioning supported
  - Automatic replication

- **Kubernetes Secrets:**
  - Database credentials
  - Flask SECRET_KEY
  - Base64 encoded values

- **CI/CD Secrets (GitHub Actions):**
  - GCP_SA_KEY - Service account credentials
  - GCP_PROJECT_ID
  - DB_PASSWORD
  - TF_STATE_BUCKET
  - APP_URL - For load testing
  - AUDIT_BUCKET

**D. Local Development:**
- `.env` file support via python-dotenv
- Development fallbacks in config.py
- Docker-compose environment variables

---

### 11. Networking & Security

**VPC Architecture:**

**A. Networks:**
- **VPC:** chess-tournament-vpc
- **Subnets:**
  - GKE subnet: 10.0.0.0/20
    - Pod range: 10.1.0.0/16
    - Service range: 10.2.0.0/20
  - Worker subnet: 10.3.0.0/24
  - VPC Connector: 10.8.0.0/28

**B. Firewall Rules:**
- Allow internal traffic (TCP/UDP 0-65535, ICMP)
- Allow SSH (TCP 22) from 0.0.0.0/0 (restrict in prod)
- Cloud NAT for private instance outbound access

**C. Private IP Configuration:**
- Cloud SQL accessible only via private IP
- GKE nodes in private subnet
- Cloud Function VPC connector for DB access
- Private service connection for Cloud SQL peering

**D. Security Features:**
- Workload Identity (pod→GCP service account)
- Network Policy enabled in GKE
- Service accounts with least privilege IAM roles
- Resource quotas and limits
- Health checks and auto-healing

---

### 12. Infrastructure as Code (Terraform)

**Location:** `/infra/` directory

**Files:**
- `main.tf` - Provider configuration, API enablement
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `networking.tf` - VPC, subnets, firewalls, Cloud NAT
- `gke.tf` - GKE cluster, node pools, service accounts
- `cloudsql.tf` - Cloud SQL instance, database, user, secrets
- `memorystore.tf` - Redis instance
- `vm.tf` - Compute Engine worker VM
- `functions.tf` - Cloud Functions, GCS buckets, VPC connector
- `registry.tf` - Artifact Registry

**Backend Configuration:**
- Local backend (default)
- Supports GCS backend for remote state: `backend "gcs" { bucket = "your-bucket" }`

**Resource Naming:**
- Deterministic with random suffix for uniqueness
- Labels for tracking (app, environment, managed_by)

---

### 13. Load Testing

**Locust Framework:**

**File:** `/locust/locustfile.py`

**Test Scenarios:**
- Player browsing (weight: 5 - most common)
- Coach operations (match, hall management)
- Arbiter operations (rating matches)
- Manager operations (user management, stats)
- API endpoint testing

**Configuration:**
- Wait time: 1-5 seconds between requests
- Simulates realistic user behavior
- Custom login/logout functionality
- Role-based user personas

**Execution:**
- Manual workflow dispatch in GitHub Actions
- Configurable number of users and spawn rate
- 60-second test runs
- HTML report generation

---

### 14. Deployment Workflow

**Complete Deployment Flow:**

1. **Infrastructure Setup (Terraform)**
   - Create GCP project and enable APIs
   - Run terraform init, plan, apply
   - Provisions: VPC, GKE, Cloud SQL, Memorystore, Worker VM, Cloud Functions

2. **Database Initialization**
   - Cloud SQL Proxy connection
   - Load schema.sql and triggers.sql
   - Optional sample data loading

3. **Container Image Build**
   - Docker build with Dockerfile
   - Push to Artifact Registry
   - Automatic tagging (SHA + latest)

4. **Kubernetes Deployment**
   - Get GKE credentials
   - Apply namespace, RBAC, ConfigMap, Secrets
   - Deploy application pods
   - HPA monitors and scales

5. **Cloud Function Deployment**
   - Upload source to GCS
   - Deploy Gen 2 Cloud Function
   - Configure VPC connector

6. **Worker Deployment**
   - VM startup script executes automatically
   - Systemd service manages worker lifecycle
   - CI/CD can update script via gcloud scp

---

### 15. Monitoring & Observability

**Built-in Monitoring:**
- Kubernetes: kubectl get pods/services/ingress
- GKE: Cloud Console > Kubernetes Engine > Workloads
- Cloud SQL: Cloud Console > SQL > Instance > Monitoring
- HPA metrics: kubectl get hpa
- Logs: kubectl logs, gcloud functions logs read

**Application Logging:**
- Gunicorn access logs
- Flask application logs
- Python logging to stdout
- systemd journal for VM services

---

## Summary Table

| Aspect | Technology | Purpose |
|--------|-----------|---------|
| **Cloud Provider** | Google Cloud Platform | All infrastructure |
| **Compute** | GKE | App container orchestration |
| **Compute** | Compute Engine VM | Background worker |
| **Serverless** | Cloud Functions (Gen 2) | Audit logging |
| **Database** | Cloud SQL (MySQL 8.0) | Persistent data |
| **Cache** | Memorystore (Redis) | Query caching |
| **Container Registry** | Artifact Registry | Docker image storage |
| **Secrets** | Secret Manager | Credentials management |
| **Networking** | VPC + VPC Peering | Private networking |
| **Load Balancing** | GCE Ingress | Public HTTP(S) endpoint |
| **IaC** | Terraform | Infrastructure provisioning |
| **CI/CD** | GitHub Actions | Build, test, deploy pipelines |
| **Testing** | Locust | Load testing |
| **Containerization** | Docker | Application packaging |

---

## Key Architectural Patterns

1. **Microservices-lite:** Flask app (GKE) + Worker (VM) + Functions (Serverless)
2. **Private-by-default:** All database and function access via private IPs/VPC
3. **Scalable:** HPA for app pods, auto-healing for nodes
4. **Event-driven:** Cloud Functions for side effects (audit logging)
5. **Infrastructure-as-Code:** Terraform for reproducible deployments
6. **Secrets management:** Google Secret Manager + K8s Secrets
7. **Caching strategy:** Redis for frequently accessed data
8. **Audit & Compliance:** Cloud Storage + Cloud SQL audit logs
