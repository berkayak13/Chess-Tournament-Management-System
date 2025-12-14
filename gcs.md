````md
# Deployment Plan: Flask App + Cloud SQL + GKE + VM Worker + Cloud Functions + Locust (separate)

This document is a practical, end-to-end deployment plan for a Flask application currently bundled with a database, migrated to a cloud deployment that includes:
- Flask app on **GKE**
- Database on **Cloud SQL**
- A **Compute Engine VM** with a real functional role (background worker)
- **Cloud Function(s)** integrated into the system
- **Locust** as a separate performance-testing component (not served by VM)
- Optional **Terraform** to provision infrastructure as code

---

## 0) Goals and target architecture

### Runtime components
- **Client** → public HTTPS endpoint (Ingress / Load Balancer) → **GKE Service** → **Flask Pods**
- Flask Pods read/write to **Cloud SQL**
- **VM Worker** reads raw data from Cloud SQL and writes aggregated outputs back to Cloud SQL
- **Cloud Function (HTTP)** is called by Flask for event-style tasks (logging, side effects, async-ish work)
- Optional **Cloud Function (Event Driven)** triggered by a GCS bucket upload, writing metadata back to Cloud SQL
- **Locust** runs separately (local machine or its own container/pod) and targets the public Ingress URL

### Why this fits the project well
- GKE covers “containerized scalable workloads”
- Cloud SQL is a clean shared DB for app + worker + functions
- VM has a real business/job role (batch stats/report generation), not “load testing”
- Cloud Functions cover serverless integration
- Locust is isolated as a testing tool

---

## 1) Repo structure (recommended)

```text
.
├─ app/                     # Flask app code
│   ├─ app.py
│   ├─ models.py
│   ├─ config.py
│   ├─ requirements.txt
│   └─ ...
├─ Dockerfile               # container for Flask
├─ k8s/                     # Kubernetes manifests
│   ├─ deployment.yaml
│   ├─ service.yaml
│   ├─ ingress.yaml
│   ├─ hpa.yaml             # optional autoscaling
│   └─ configmap-secret-notes.md
├─ worker/                  # VM worker scripts
│   ├─ worker.py
│   ├─ requirements.txt
│   └─ systemd/worker.service
├─ cloud-function-http/
│   ├─ main.py
│   └─ requirements.txt
├─ cloud-function-event/
│   ├─ main.py
│   └─ requirements.txt
├─ locust/                  # load test
│   └─ locustfile.py
├─ infra/                   # Terraform
│   ├─ main.tf
│   ├─ variables.tf
│   ├─ outputs.tf
│   ├─ networking.tf
│   ├─ gke.tf
│   ├─ cloudsql.tf
│   ├─ vm.tf
│   ├─ functions.tf
│   └─ iam.tf
└─ README.md
````

---

## 2) Application refactor (minimal changes required)

### 2.1 Make configuration environment-based

Update Flask config so DB config is not hardcoded.

**Example (config.py):**

* Read `DATABASE_URL` from environment
* Read any secrets from env (API keys, function URL, etc.)
* Keep “local dev” fallback if needed

### 2.2 Ensure DB schema management exists

Pick one:

* Flask-Migrate/Alembic (best)
* “create tables on startup” (works for small projects, but migrations are better)

---

## 3) Database migration: DB-in-app → Cloud SQL

### 3.1 Provision Cloud SQL

* Choose Postgres or MySQL
* Create:

  * Cloud SQL instance
  * database
  * user/password
* Prefer **private IP** inside VPC if possible; otherwise secure public IP access tightly.

### 3.2 Update DB connection string

Set `DATABASE_URL` for:

* GKE pods
* VM worker
* Cloud Function (if writing to DB)

### 3.3 Migrate existing data (optional)

If you already have meaningful data:

* Postgres: `pg_dump` / `pg_restore`
* MySQL: `mysqldump` / import

If not, just run migrations against Cloud SQL.

---

## 4) Containerize Flask app

### 4.1 Dockerfile

Use Gunicorn for production.

Example pattern:

* install deps
* copy code
* run `gunicorn -b 0.0.0.0:8080 app:app`

### 4.2 Build & push to Artifact Registry

* Create Artifact Registry repository (via Terraform or Console)
* `docker build`
* `docker tag`
* `docker push`

---

## 5) Deploy to GKE

### 5.1 Create the cluster

* GKE Standard or Autopilot
* Keep it small for class constraints
* Enable logging/monitoring if available

### 5.2 Kubernetes manifests

You will apply:

* `Deployment` (Flask)
* `Service` (ClusterIP)
* `Ingress` (public)
* optional `HPA` (autoscaling)

**Key points**

* Set `DATABASE_URL` via Kubernetes Secret
* Keep non-secret config in ConfigMap
* Add readiness/liveness probes if possible

### 5.3 Connect GKE to Cloud SQL

Common options:

* Cloud SQL Auth Proxy / sidecar
* Private IP connectivity in VPC
* Workload Identity or node service account permissions

Pick the method that is simplest for your setup and matches course expectations.

---

## 6) VM Worker (functional VM role)

### 6.1 What the VM does

A background worker that:

* reads raw transactional tables (e.g., user actions, events, requests)
* computes aggregates (e.g., daily counts, rolling averages, usage metrics)
* writes results into `system_stats` / `reports` tables

### 6.2 Where it shows in the Flask app

Add an admin endpoint/page:

* `/admin/stats`
* `/reports/latest`
  that reads the aggregated tables and renders a table or chart.

### 6.3 How it runs on the VM

Two clean patterns:

* **systemd service** (always on)
* **cron job** (every 5 minutes / hourly)

### 6.4 Provisioning the VM

* Provision VM (Terraform recommended)
* Startup script can:

  * install Python
  * pull `worker.py` (or bake it in via image or git)
  * set env vars (DATABASE_URL)
  * enable systemd service

---

## 7) Cloud Functions (serverless integration)

### 7.1 HTTP Function (recommended)

Flask calls it on specific events:

* on user signup
* on new record creation
* on “export report” click

Possible actions:

* write an audit log row to Cloud SQL
* store a JSON log in GCS
* trigger an async workflow-like step

**How Flask uses it**

* store `FUNCTION_URL` in env
* `requests.post(FUNCTION_URL, json=payload)`

### 7.2 Event-driven Function (optional)

Use a GCS bucket:

* Flask uploads a file → triggers function → function stores metadata to DB

This is great if you want a clean “event-driven” story in the report.

---

## 8) Locust (separate from VM)

Locust is a testing component only:

* Run Locust locally or as a separate container/pod
* Target the public Ingress URL of your Flask service
* Collect:

  * latency, throughput, failures
  * optionally correlate with GKE metrics (CPU/memory, HPA scaling)

---

## 9) Terraform plan (bonus infrastructure-as-code)

### 9.1 What Terraform provisions

* Enable APIs (container, compute, sqladmin, artifactregistry, cloudfunctions, storage, etc.)
* VPC + subnets + firewall rules
* GKE cluster (+ node pool)
* Cloud SQL instance + db + user
* Artifact Registry repo
* Compute Engine VM (+ startup script)
* Cloud Functions (+ triggers) (optional but strong bonus)
* GCS bucket (if used)
* Service accounts + IAM bindings

### 9.2 Suggested workflow

1. `terraform init`
2. `terraform plan`
3. `terraform apply`
4. Deploy app to GKE:

   * Either `kubectl apply -f k8s/`
   * Or Terraform `kubernetes_*` resources later if you want full IaC

---

## 10) Security and configuration checklist

* Use Kubernetes **Secrets** for:

  * DB credentials
  * Function URL tokens (if any)
* Limit IAM roles:

  * GKE workload identity / node SA should have minimal permissions
  * VM SA should only access what it needs (Cloud SQL, optionally GCS)
  * Function SA should only access what it needs
* Use HTTPS Ingress
* Add basic rate-limiting or auth for admin endpoints

---

## 11) Observability (recommended)

* GKE logging/monitoring enabled
* Log requests in Flask (structured logs)
* VM logs (systemd journal) or write logs to Cloud Logging
* Cloud Function logs in Cloud Logging

In the report, show:

* baseline vs load test (Locust)
* how scaling behaves (if HPA enabled)

---

# Adding a cache: does it work here?

Yes — adding caching can be very useful and fits this architecture nicely, especially because:

* GKE pods are stateless and can scale horizontally
* DB can become the bottleneck under load
* Some endpoints likely return repeated data (stats pages, lists, home pages)

## Recommended caching options

### Option A: Redis / Memorystore (best for server-side caching)

**What it gives you**

* Shared cache across all Flask pods
* Fast responses for repeated queries
* Avoids hitting Cloud SQL for every request

**Common use cases**

* Cache expensive DB query results for N seconds
* Cache “latest stats/report” page results
* Cache session data (if you use server-side sessions)

**How**

* Use a Flask caching library (like Flask-Caching) with Redis backend
* Provision Redis as:

  * GCP Memorystore (managed) OR
  * a Redis pod in GKE (acceptable but less “managed”)

### Option B: In-memory cache per pod (fast but limited)

**Pros**

* easiest, no extra infra

**Cons**

* each pod has its own cache (inconsistent)
* cache resets on pod restart/scale events

This is okay for small demos but weaker as a “real” architecture.

### Option C: HTTP caching/CDN for static responses

If you have static assets or public endpoints:

* set Cache-Control headers
* optionally use Cloud CDN in front of the load balancer

## What I would do for your project

* If you want a clean “systems” story: **Redis/Memorystore**
* If you want minimal complexity: cache just the **stats endpoint** for 15–60 seconds

## What to be careful about

* Cache invalidation: don’t cache endpoints that must be strongly consistent (unless short TTL is OK)
* Don’t cache anything user-private without keying by user/session
* Keep TTL small for things that change frequently (e.g., 30s)

---

## 12) Minimal “definition of done”

* Flask runs on GKE, reachable via Ingress
* Cloud SQL is the only DB (no embedded DB in container)
* VM worker writes aggregates that are visible from Flask UI
* Cloud Function is integrated (Flask calls it OR event-driven via GCS)
* Locust tests the public endpoint, separate from VM
* Terraform provisions most or all infra (bonus)
* (Optional) caching implemented for at least one endpoint

```

If you tell me what your DB is (SQLite? Postgres? MySQL?) and whether you’re already using SQLAlchemy, I can also add a “copy-paste ready” section in that markdown with:
- exact env vars you’ll need,
- example `deployment.yaml` env/secret wiring,
- and a simple Redis caching snippet for one route.
```
