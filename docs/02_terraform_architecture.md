# Infrastructure Architecture - Solo Developer Setup

## 🏗️ Simple Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    GCP Project                          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │         GKE Autopilot Cluster                     │ │
│  │         (Serverless Kubernetes)                   │ │
│  │                                                    │ │
│  │  Nodes appear automatically when pods run         │ │
│  │                                                    │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │ FastAPI  │  │PostgreSQL│  │  MLflow  │       │ │
│  │  │   Pod    │  │   Pod    │  │   Pod    │       │ │
│  │  └──────────┘  └──────────┘  └──────────┘       │ │
│  │                                                    │ │
│  │  ┌──────────┐                                     │ │
│  │  │  Redis   │                                     │ │
│  │  │   Pod    │                                     │ │
│  │  └──────────┘                                     │ │
│  │                                                    │ │
│  │  💡 Pay only for pods, not nodes!                │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Cloud Storage (GCS)                       │ │
│  │                                                    │ │
│  │  Single Bucket: PROJECT_ID-recsys-data           │ │
│  │                                                    │ │
│  │  ├── data/          (raw data, datasets)         │ │
│  │  ├── models/        (trained ML models)          │ │
│  │  └── mlflow/        (experiment artifacts)       │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │      Artifact Registry (Docker)                   │ │
│  │                                                    │ │
│  │  us-central1-docker.pkg.dev/                     │ │
│  │  PROJECT_ID/PROJECT_ID-recsys/                   │ │
│  │                                                    │ │
│  │  ├── recsys-api:v1.0.0                           │ │
│  │  ├── recsys-api:v1.0.1                           │ │
│  │  └── recsys-api:latest                           │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

```

---

## 📊 Resource Breakdown

### Total Resources: 3

| # | Resource Type | Name | Purpose |
| --- | --- | --- | --- |
| 1 | `google_container_cluster` | GKE Autopilot | Run containerized apps |
| 2 | `google_storage_bucket` | GCS Bucket | Store data/models/artifacts |
| 3 | `google_artifact_registry_repository` | Docker Registry | Store container images |

---

## 🎯 Resource Explanations

### 1. GKE Autopilot Cluster

**What it is:**
A serverless Kubernetes cluster where Google manages all infrastructure.

**Configuration:**

```hcl
resource "google_container_cluster" "primary" {
  name     = "${var.project_id}-gke"
  location = var.region

  # Enable Autopilot mode (no node management, pay per pod)
  enable_autopilot = true

  # Autopilot automatically configures networking
  # No need for custom VPC for solo dev
}

```

**Why you need it:**

- Runs all your containerized applications
- Manages pod scheduling and scaling
- Provides Kubernetes API for deployments
- Handles load balancing automatically

**What runs here:**

```
┌─────────────────────────────────────────┐
│  FastAPI Pod                            │
│  - Your recommendation API              │
│  - Serves predictions                   │
│  - Connects to PostgreSQL & Redis       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  PostgreSQL Pod                         │
│  - Stores user data                     │
│  - Stores product catalog               │
│  - Stores interaction history           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  MLflow Pod                             │
│  - Tracks experiments                   │
│  - Logs metrics and parameters          │
│  - Stores artifacts to GCS              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Redis Pod                              │
│  - Caches recommendations               │
│  - Fast data access                     │
│  - Session storage                      │
└─────────────────────────────────────────┘

```

**Key Features:**

- ✅ **Serverless** - No node management
- ✅ **Auto-scaling** - Scales based on demand
- ✅ **Pay per pod** - Only pay for running containers
- ✅ **Workload Identity** - Secure GCP access built-in
- ✅ **Auto-networking** - No VPC setup needed

**Cost:**

- ~$10/month for 4 small pods
- $0 when no pods are running

**Real-world analogy:**
Like Uber for servers - you only pay when you're using them, and someone else handles all the maintenance.

---

### 2. Cloud Storage Bucket (GCS)

**What it is:**
A single bucket for storing all your data, models, and artifacts.

**Configuration:**

```hcl
resource "google_storage_bucket" "data" {
  name          = "${var.project_id}-recsys-data"
  location      = var.region
  force_destroy = true  # Allow deletion for dev

  uniform_bucket_level_access = true

  # Lifecycle rule to reduce costs
  lifecycle_rule {
    condition {
      age = 90  # Delete files older than 90 days
    }
    action {
      type = "Delete"
    }
  }
}

```

**Why you need it:**

- Persistent storage for data (survives pod restarts)
- Stores training datasets
- Stores trained ML models
- Stores MLflow experiment artifacts
- Unlimited scalability

**Bucket Organization:**

```
gs://PROJECT_ID-recsys-data/
│
├── data/                    # Raw data
│   ├── interactions.csv     # User interactions
│   ├── products.json        # Product catalog
│   ├── users.parquet        # User profiles
│   └── datasets/
│       ├── train.csv
│       └── test.csv
│
├── models/                  # Trained models
│   ├── collaborative_filtering/
│   │   ├── model_v1.pkl
│   │   ├── model_v2.pkl
│   │   └── current.pkl      # Production model
│   └── content_based/
│       └── embeddings.npy
│
└── mlflow/                  # MLflow artifacts
    ├── 0/                   # Experiment ID
    │   └── abc123/          # Run ID
    │       ├── artifacts/
    │       ├── metrics/
    │       └── params/
    └── 1/

```

**Usage in your code:**

```python
from google.cloud import storage

# Upload data
client = storage.Client()
bucket = client.bucket('PROJECT_ID-recsys-data')

# Upload training data
blob = bucket.blob('data/interactions.csv')
blob.upload_from_filename('local_interactions.csv')

# Download model
blob = bucket.blob('models/collaborative_filtering/current.pkl')
blob.download_to_filename('model.pkl')

# MLflow uses this automatically
mlflow.set_tracking_uri("<http://mlflow:5000>")
# Artifacts saved to gs://PROJECT_ID-recsys-data/mlflow/

```

**Key Features:**

- ✅ **Single bucket** - Simpler management
- ✅ **Lifecycle rules** - Auto-delete old files (saves money)
- ✅ **Versioning** - Can be enabled if needed
- ✅ **Workload Identity** - Pods access without keys

**Cost:**

- ~$0.02/GB/month
- ~$0.20/month for 10GB

**Real-world analogy:**
Like Google Drive for your ML project - organized folders for different types of files.

---

### 3. Artifact Registry (Docker)

**What it is:**
A private Docker registry for storing your container images.

**Configuration:**

```hcl
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "${var.project_id}-recsys"
  format        = "DOCKER"
  description   = "Docker images for recommendation system"
}

```

**Why you need it:**

- Stores your custom Docker images
- Private and secure (not public like Docker Hub)
- Fast image pulls (regional, close to cluster)
- Integrated with GKE (automatic authentication)
- Vulnerability scanning included

**What you'll store:**

```
us-central1-docker.pkg.dev/PROJECT_ID/PROJECT_ID-recsys/
│
├── recsys-api:v1.0.0        # Your FastAPI app
├── recsys-api:v1.0.1        # Updated version
├── recsys-api:v1.1.0        # New features
├── recsys-api:latest        # Latest version
│
├── mlflow-custom:v1.0.0     # Custom MLflow image (optional)
└── data-processor:v1.0.0    # Data processing job (optional)

```

**Usage workflow:**

```bash
# 1. Build your Docker image
docker build -t recsys-api:v1.0.0 .

# 2. Tag for Artifact Registry
docker tag recsys-api:v1.0.0 \\
  us-central1-docker.pkg.dev/PROJECT_ID/PROJECT_ID-recsys/recsys-api:v1.0.0

# 3. Push to registry
docker push us-central1-docker.pkg.dev/PROJECT_ID/PROJECT_ID-recsys/recsys-api:v1.0.0

# 4. Deploy to GKE (pulls automatically)
kubectl set image deployment/api \\
  api=us-central1-docker.pkg.dev/PROJECT_ID/PROJECT_ID-recsys/recsys-api:v1.0.0

```

**Key Features:**

- ✅ **Private** - Only you can access
- ✅ **Regional** - Fast pulls (same region as cluster)
- ✅ **Integrated** - GKE pulls automatically
- ✅ **Secure** - Vulnerability scanning
- ✅ **Versioned** - Keep multiple versions

**Cost:**

- ~$0.10/GB/month
- ~$0.50/month for 5GB of images

**Real-world analogy:**
Like a private warehouse for your packaged applications - only your team can access it.

---

## 🔄 How Resources Work Together

### Complete Data Flow

```
1. Developer writes code
   ↓
2. Builds Docker image
   ↓
3. Pushes to Artifact Registry ← (docker_repo)
   ↓
4. Deploys to GKE Autopilot ← (primary cluster)
   ↓
5. FastAPI pod starts automatically
   ↓
6. Connects to PostgreSQL pod ← (same cluster)
   ↓
7. Loads model from GCS ← (data bucket)
   ↓
8. Serves recommendations
   ↓
9. MLflow logs metrics to GCS ← (data bucket)

```

### ML Development Workflow

```
1. Data Scientist runs experiment
   ↓
2. Loads data from GCS ← (data/ folder)
   ↓
3. Trains model in notebook/pod
   ↓
4. MLflow logs to GCS ← (mlflow/ folder)
   ↓
5. Saves model to GCS ← (models/ folder)
   ↓
6. API loads model ← (from models/ folder)
   ↓
7. Serves predictions

```

### CI/CD Pipeline

```
1. Push code to GitHub
   ↓
2. Jenkins/GitHub Actions builds image
   ↓
3. Runs tests
   ↓
4. Pushes to Artifact Registry ← (docker_repo)
   ↓
5. Updates GKE deployment ← (primary cluster)
   ↓
6. Rolling update (zero downtime)

```

---

## 💰 Cost Breakdown by Resource

| Resource | Configuration | Monthly Cost | When Idle |
| --- | --- | --- | --- |
| **GKE Autopilot** | 4 pods (0.5 vCPU, 1GB each) | ~$10 | $0 |
| **GCS Bucket** | 10GB storage | ~$0.20 | ~$0.20 |
| **Artifact Registry** | 5GB images | ~$0.50 | ~$0.50 |
| **Total** |  | **~$10-15** | **~$0.70** |

### Cost Optimization Tips

1. **Stop pods when not in use:**
    
    ```bash
    kubectl scale deployment/api --replicas=0
    kubectl scale deployment/mlflow --replicas=0
    
    ```
    
    Cost: $0 for compute
    
2. **Use lifecycle rules:**
    - Auto-delete old experiment artifacts
    - Keep only recent models
    - Already configured in bucket
3. **Clean up old images:**
    
    ```bash
    gcloud artifacts docker images list \\
      us-central1-docker.pkg.dev/PROJECT_ID/PROJECT_ID-recsys
    
    # Delete old versions
    gcloud artifacts docker images delete IMAGE_NAME:OLD_TAG
    
    ```
    
4. **Choose closest region:**
    - Reduces network egress costs
    - Faster access

---

## 🎯 Why This Architecture?

### ✅ Advantages

**1. Minimal Cost**

- Pay only for running pods (~$10/month)
- No idle node costs
- Single bucket reduces overhead

**2. Simple Management**

- No VPC configuration
- No node pool management
- No service account keys
- Autopilot handles everything

**3. Production-Ready**

- Auto-scaling
- Self-healing
- Load balancing
- Secure by default

**4. Easy Development**

- Local state (no remote backend needed)
- Quick deployments
- Easy cleanup

### ⚠️ Trade-offs

**1. Less Control**

- Can't customize node types
- Can't SSH into nodes
- Limited networking options

**2. Autopilot Limitations**

- Slightly higher per-pod cost than standard GKE
- Some Kubernetes features restricted
- Regional only (not zonal)

**3. Single Bucket**

- Need good folder organization
- Can't have different lifecycle policies per bucket
- All data in one place

---

## 🔒 Security Features

### Built-in Security

1. **Workload Identity**
    - Pods access GCS without keys
    - Automatic credential rotation
    - No secrets to manage
2. **Private Registry**
    - Images not publicly accessible
    - Vulnerability scanning
    - Access control via IAM
3. **Network Security**
    - Autopilot uses secure defaults
    - Encrypted communication
    - Isolated pods

### Access Control

```bash
# Your pods automatically get access to GCS
# No service account keys needed!

# For local development, use your own credentials
gcloud auth application-default login

```

---

## 📈 Scaling Strategy

### Current Setup (Solo Dev)

```
GKE Autopilot: 4 pods
- 1 FastAPI (0.5 vCPU, 1GB RAM)
- 1 PostgreSQL (0.5 vCPU, 1GB RAM)
- 1 MLflow (0.25 vCPU, 512MB RAM)
- 1 Redis (0.25 vCPU, 512MB RAM)

Cost: ~$10/month

```

### When You Need More (Growing)

```
GKE Autopilot: Auto-scales
- 3 FastAPI pods (horizontal scaling)
- 1 PostgreSQL (vertical scaling: 1 vCPU, 2GB)
- 1 MLflow
- 1 Redis

Cost: ~$20-25/month

```

### Production Scale (Team)

```
Consider upgrading to:
- Standard GKE with dedicated nodes
- Separate buckets for data/models/mlflow
- Remote state backend (GCS)
- Multiple environments (dev/staging/prod)

Cost: ~$100-200/month

```

---

## 🔄 Migration Path

### From Solo Dev → Team

When you're ready to scale:

1. **Add remote state backend:**
    
    ```hcl
    backend "gcs" {
      bucket = "prod-recsys-terraform-state"
      prefix = "terraform/state"
    }
    
    ```
    
2. **Split buckets:**
    
    ```hcl
    resource "google_storage_bucket" "data" { ... }
    resource "google_storage_bucket" "models" { ... }
    resource "google_storage_bucket" "mlflow" { ... }
    
    ```
    
3. **Add custom VPC:**
    
    ```hcl
    resource "google_compute_network" "vpc" { ... }
    resource "google_compute_subnetwork" "subnet" { ... }
    
    ```
    
4. **Switch to Standard GKE:**
    
    ```hcl
    resource "google_container_cluster" "primary" {
      enable_autopilot = false  # Change this
      # Add node pool configuration
    }
    
    ```
    

---

## 📚 Related Documentation

- [**README.md**](http://readme.md/) - Deployment guide
- [**COMPARISON.md**](http://comparison.md/) - Comparison with other setups
- [**main.tf**](http://main.tf/) - Actual Terraform code
- [**variables.tf**](http://variables.tf/) - Configuration variables
- [**outputs.tf**](http://outputs.tf/) - Output values

---

## 🎓 Learning Resources

- [GKE Autopilot Documentation](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)

---

**Simple, cost-effective, and production-ready! 🚀**

# Terraform take note

- Terraform là một open-source của HashiCorp,
- dùng để provisioning infrastructure
