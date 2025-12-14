# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup (requires MySQL running on localhost:3306)
python init_db.py    # Creates chessdb and runs code/triggers.sql

# Run application
python app.py        # Runs on http://localhost:5000 with debug=True

# Run with Docker
docker-compose up -d

# Run tests
pytest tests/ -v

# Run load tests
cd locust && locust -f locustfile.py --host=http://localhost:8080
```

## Architecture

Flask + MySQL web application for chess tournament management with role-based access control.

**Stack:** Flask 3.0.2, mysql-connector-python 8.3.0, Flask-Login 0.6.3, Bootstrap 5.3 (CDN)

**Database:** MySQL `chessdb` on 127.0.0.1:3306 (user: root, password: 1234)

## Project Structure

```
.
├── app.py                    # Main Flask application (all routes)
├── config.py                 # Environment-based configuration
├── cache.py                  # Redis/simple caching abstraction
├── init_db.py                # Database initialization script
├── code/
│   ├── triggers.sql          # Schema, triggers, stored procedures
│   ├── schema.sql            # Table definitions (reference)
│   └── insert_statements.sql # Sample data
├── templates/                # Jinja2 templates (by role)
│   ├── base.html
│   ├── admin/stats.html      # System statistics page
│   ├── player/
│   ├── coach/
│   ├── arbiter/
│   └── manager/
├── tests/                    # pytest test suite
│   ├── conftest.py           # Test fixtures
│   ├── test_auth.py
│   ├── test_player_routes.py
│   ├── test_coach_routes.py
│   ├── test_arbiter_routes.py
│   ├── test_manager_routes.py
│   └── test_api.py
├── worker/                   # Background stats worker
│   ├── worker.py
│   ├── requirements.txt
│   └── systemd/worker.service
├── cloud-function-http/      # GCP Cloud Function (audit logging)
│   ├── main.py
│   └── requirements.txt
├── locust/                   # Load testing
│   ├── locustfile.py
│   └── requirements.txt
├── k8s/                      # Kubernetes manifests
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml.example
│   ├── serviceaccount.yaml
│   └── hpa.yaml
├── infra/                    # Terraform modules
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── networking.tf
│   ├── cloudsql.tf
│   ├── gke.tf
│   ├── vm.tf
│   ├── memorystore.tf
│   ├── registry.tf
│   └── functions.tf
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## GCP Deployment Architecture

```
                                 ┌─────────────────┐
                                 │   Cloud DNS     │
                                 └────────┬────────┘
                                          │
                                 ┌────────▼────────┐
                                 │  Load Balancer  │
                                 │    (Ingress)    │
                                 └────────┬────────┘
                                          │
┌─────────────────────────────────────────┼──────────────────────────────────────┐
│  GKE Cluster                            │                                      │
│                           ┌─────────────▼─────────────┐                        │
│                           │   Flask App (2-10 pods)   │                        │
│                           │   with Cloud SQL Proxy    │                        │
│                           └─────────────┬─────────────┘                        │
│                                         │                                      │
└─────────────────────────────────────────┼──────────────────────────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
┌─────────▼─────────┐          ┌─────────▼─────────┐          ┌─────────▼─────────┐
│   Cloud SQL       │          │   Memorystore     │          │  Cloud Functions  │
│   (MySQL)         │          │   (Redis)         │          │  (Audit Logging)  │
└───────────────────┘          └───────────────────┘          └─────────┬─────────┘
          │                                                             │
          │                                                   ┌─────────▼─────────┐
          │                                                   │  Cloud Storage    │
          │                                                   │  (Audit Logs)     │
          │                                                   └───────────────────┘
          │
┌─────────▼─────────┐
│  Compute Engine   │
│  (Stats Worker)   │
└───────────────────┘
```

## Key Files

- `app.py` - Single-file Flask application with all routes
- `config.py` - Configuration classes (Dev, Test, Prod) with env vars
- `cache.py` - Redis caching wrapper with fallback to simple cache
- `code/triggers.sql` - Database schema, triggers, and stored procedures
- `worker/worker.py` - Background worker computing aggregated statistics
- `cloud-function-http/main.py` - HTTP Cloud Function for audit logging

## Database Structure

**Core Tables:** users, players, coaches, arbiters, managers, teams, sponsors, halls, match_tables, matches, match_assignments, player_teams

**System Tables:** system_stats (worker-computed statistics)

**Stored Procedures:**
- `createMatch` - Create match with hall/table availability check
- `assignPlayers` - Assign white/black players to match
- `deleteMatch` - Delete match (cascade to assignments)
- `viewHalls` - List all halls
- `submitRating` - Arbiter submits match rating (1-10)
- `showMatchStats` - Arbiter's rating statistics
- `showCoPlayerStats` - Player's opponent history

**Triggers:** Enforce coach contract non-overlap, arbiter scheduling conflicts, player team membership validation, 2-hour match duration conflicts

## User Roles (users.role ENUM)

- **manager** (`/manager/*`, `/admin/*`) - Create users, manage halls, view system stats
- **player** (`/player/*`) - View own matches, statistics, opponents
- **coach** (`/coach/*`) - Create/delete matches, assign players for own team
- **arbiter** (`/arbiter/*`) - Rate past matches assigned to them

## Route Patterns

Routes are role-protected via `current_user.role` checks. Each role has a dashboard at `/<role>/dashboard`. The index route (`/`) redirects authenticated users to their role's dashboard.

**API endpoint:** `/api/halls/<hall_id>/tables` - Returns JSON list of tables in a hall

**Admin endpoint:** `/admin/stats` - Displays worker-computed system statistics (manager only)

## Environment Variables

```bash
# Database
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=1234
DB_NAME=chessdb

# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=production

# Caching (optional)
REDIS_URL=redis://localhost:6379/0
CACHE_TIMEOUT=300

# Cloud Function integration (optional)
FUNCTION_URL=https://your-function-url.cloudfunctions.net/audit_log

# Worker settings
COMPUTE_INTERVAL=300  # seconds between stat computations
GCP_PROJECT=your-gcp-project  # for Secret Manager access
```

## Terraform Deployment

```bash
cd infra/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply

# Deploy to GKE
gcloud container clusters get-credentials chess-tournament-cluster --region us-central1
kubectl apply -f ../k8s/
```

## CI/CD Workflows

GitHub Actions workflows in `.github/workflows/`:

**`deploy.yml`** - Main CI/CD pipeline (triggers on push to main):
1. **test** - Run pytest with MySQL service container
2. **build** - Build & push Docker image to Artifact Registry
3. **deploy-gke** - Rolling update to GKE
4. **deploy-function** - Deploy Cloud Function
5. **deploy-worker** - Update worker script on VM

**`terraform.yml`** - Infrastructure pipeline (triggers on changes to `infra/`):
1. **terraform-plan** - Validate and plan changes
2. **terraform-apply** - Apply infrastructure (main branch only)
3. **terraform-destroy** - Manual destroy option

See `.github/SETUP.md` for required secrets and setup instructions.

## Important Implementation Details

- Passwords stored in plain text (no hashing)
- Match time slots: 1, 2, or 3 mapped to '01:00:00', '02:00:00', '03:00:00'
- Each match has 2-hour duration for conflict detection
- White player must be from team1, black player from team2
- Ratings can only be submitted after match date has passed
- Rating once submitted cannot be changed (trigger-enforced)
- Caching is optional (falls back to no-op if Redis unavailable)
- Audit logging to Cloud Function is optional (gracefully skipped if unavailable)
