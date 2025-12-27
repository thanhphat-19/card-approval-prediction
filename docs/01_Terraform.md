# **Step 1: Set Active Project**

```python
gcloud config set project <project_name>
```

**What this does:**

- Sets **`<proJec-name>`** as your **default project** for all **`gcloud`** commands
- All future commands will run against this project unless you specify otherwise

**Why needed:**

- You might have multiple GCP projects
- This ensures Terraform and gcloud commands target the correct projec

**Verify it worked:**

```python
gcloud config get-value project
# Should output: <project_name>
```

# **Step 2: Enable Required APIs**

```bash
gcloud services enable container.googleapis.com
gcloud services enable storage.googleapis.com

```

**What this does:**

- **`container.googleapis.com`** - Enables Google Kubernetes Engine (GKE) API
- **`storage.googleapis.com`** - Enables Cloud Storage (GCS) API
- **`artifactregistry.googleapis.com`** - Enables Artifact Registry API

**Why needed:**

- GCP APIs are **disabled by default** for security and cost reasons
- Terraform cannot create resources if the APIs are not enabled
- Each API must be explicitly enabled before use

**What happens:**

```bash
Operation "operations/..." finished successfully.
```

**Behind the scenes:**

- GCP activates these services in your project
- May take 1-2 minutes to propagate
- You'll be billed for usage of these services

**Verify APIs are enabled:**

```bash
gcloud services list --enabled | grep -E "container|storage|artifactregistry"
```

# **Step 3: Initialize Terraform**

```bash
cd terraform
terraform init
```

**What this does:**

1. **Downloads provider plugins** - Downloads the Google Cloud provider (~100MB)
2. **Initializes backend** - Sets up where Terraform state will be stored (local file)
3. **Creates `.terraform/` directory** - Stores provider plugins and modules
4. **Creates `.terraform.lock.hcl`** - Locks provider versions for consistency

**Output you'll see:**

```bash
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
- Installing hashicorp/google v5.x.x...
- Installed hashicorp/google v5.x.x

Terraform has been successfully initialized!
```

**Files created:**

```bash
terraform/
├── .terraform/           # Provider plugins (gitignored)
├── .terraform.lock.hcl   # Provider version lock
├── main.tf
├── variables.tf
├── outputs.tf
└── terraform.tfvars
```

**Why needed:**

- Must be run before any other Terraform command
- Downloads necessary tools to interact with GCP
- Only needs to be run once (or when providers change)

# **Step 4: Preview Changes (terraform plan)**

```bash
terraform plan
```

**What this does:**

1. **Reads your configuration** - Parses main.tf, variables.tf, **`terraform.tfvars`**
2. **Authenticates to GCP** - Uses your **`gcloud`** credentials
3. **Queries current state** - Checks what resources already exist
4. **Calculates changes** - Determines what needs to be created/modified/deleted
5. **Shows you a preview** - Displays what will happen (doesn't make changes yet)

**Output you'll see:**

```bash
Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # google_artifact_registry_repository.docker_repo will be created
  + resource "google_artifact_registry_repository" "docker_repo" {
      + create_time   = (known after apply)
      + description   = "Docker images for recommendation system"
      + format        = "DOCKER"
      + location      = "us-east1"
      + name          = (known after apply)
      + project       = "product-recsys-mlops"
      + repository_id = "product-recsys-mlops-recsys"
    }

  # google_container_cluster.primary will be created
  + resource "google_container_cluster" "primary" {
      + cluster_ipv4_cidr       = (known after apply)
      + enable_autopilot        = true
      + endpoint                = (known after apply)
      + location                = "us-east1"
      + name                    = "product-recsys-mlops-gke"
      + project                 = "product-recsys-mlops"
      + self_link               = (known after apply)
      ...
    }

  # google_storage_bucket.data will be created
  + resource "google_storage_bucket" "data" {
      + force_destroy         = true
      + location              = "US-EAST1"
      + name                  = "product-recsys-mlops-recsys-data"
      + project               = "product-recsys-mlops"
      + self_link             = (known after apply)
      + uniform_bucket_level_access = true
      ...
    }

Plan: 3 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + artifact_registry_url = "us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys"
  + configure_kubectl     = "gcloud container clusters get-credentials product-recsys-mlops-gke --region us-east1 --project product-recsys-mlops"
  + gcs_bucket            = "product-recsys-mlops-recsys-data"
  + gcs_bucket_url        = "gs://product-recsys-mlops-recsys-data"
  + project_id            = "product-recsys-mlops"
  + region                = "us-east1"
```

**What the symbols mean:**

- **`+`** = Will be **created**
- **`~`** = Will be **modified**
- = Will be **destroyed**
- **`/+`** = Will be **replaced** (destroyed then created)

**Why needed:**

- **Safety check** - Review changes before applying
- **Catch errors** - Spot mistakes in configuration
- **No cost** - Doesn't create anything, just shows plan
- **Best practice** - Always run **`plan`** before **`apply`**

# **Step 5: Create Infrastructure (terraform apply)**

```bash
terraform apply
```

**What this does:**

1. **Runs `terraform plan` again** - Shows you the changes
2. **Asks for confirmation** - You must type **`yes`** to proceed
3. **Creates resources in order** - Respects dependencies
4. **Saves state** - Records what was created in **`terraform.tfstate`**
5. **Shows outputs** - Displays important information

**Interactive prompt:**

```bash
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes    ← Type 'yes' and press Enter
```

**What happens (in order):**

## **5.1 Create GCS Bucket (30 seconds)**

```bash
google_storage_bucket.data: Creating...
google_storage_bucket.data: Creation complete after 2s [id=product-recsys-mlops-recsys-data]
```

- Creates bucket in **`us-east1`**
- Sets lifecycle rule (delete files after 90 days)
- Enables uniform bucket-level access

## **5.2 Create Artifact Registry (30 seconds)**

```bash
google_artifact_registry_repository.docker_repo: Creating...
google_artifact_registry_repository.docker_repo: Creation complete after 3s
```

- Creates Docker registry in **`us-east1`**
- Ready to receive Docker images

## **5.3 Create GKE Autopilot Cluster (10-15 minutes) ⏰**

```bash
google_container_cluster.primary: Creating...
google_container_cluster.primary: Still creating... [10s elapsed]
google_container_cluster.primary: Still creating... [20s elapsed]
...
google_container_cluster.primary: Still creating... [10m0s elapsed]
google_container_cluster.primary: Creation complete after 12m34s
```

- Creates Kubernetes control plane
- Configures Autopilot settings
- Sets up networking
- **This is the longest step!**

## **5.4 Save State**

```bash
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

artifact_registry_url = "us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys"
configure_kubectl = "gcloud container clusters get-credentials product-recsys-mlops-gke --region us-east1 --project product-recsys-mlops"
docker_push_example = "docker push us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/recsys-api:latest"
gcs_bucket = "product-recsys-mlops-recsys-data"
gcs_bucket_url = "gs://product-recsys-mlops-recsys-data"
project_id = "product-recsys-mlops"
region = "us-east1"
```

**Files created:**

```bash
terraform/
├── terraform.tfstate      # Current state (what exists in GCP)
├── terraform.tfstate.backup  # Previous state (backup)
```

**Why needed:**

- Actually creates the infrastructure
- Provisions real GCP resources
- Starts billing (resources now cost money)

# **Step 6: Configure kubectl**

```bash
terraform output -raw configure_kubectl | bash
# Fetching cluster endpoint and auth data.
# kubeconfig entry generated for product-recsys-mlops-gke.
```

**What this does:**

1. **Gets the command from Terraform output** - Extracts the kubectl config command
2. **Runs it with bash** - Executes the command
3. **Downloads cluster credentials** - Gets authentication info
4. **Updates `~/.kube/config`** - Saves cluster connection details

**Equivalent to running:**

```bash
gcloud container clusters get-credentials product-recsys-mlops-gke \
  --region us-east1 \
  --project product-recsys-mlops
```

**Output you'll see:**

```bash
Fetching cluster endpoint and auth data.
kubeconfig entry generated for product-recsys-mlops-gke.
```

**What it configures:**

```bash
# ~/.kube/config
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: <base64-cert>
    server: https://34.xxx.xxx.xxx  # Cluster endpoint
  name: gke_product-recsys-mlops_us-east1_product-recsys-mlops-gke
contexts:
- context:
    cluster: gke_product-recsys-mlops_us-east1_product-recsys-mlops-gke
    user: gke_product-recsys-mlops_us-east1_product-recsys-mlops-gke
  name: gke_product-recsys-mlops_us-east1_product-recsys-mlops-gke
current-context: gke_product-recsys-mlops_us-east1_product-recsys-mlops-gke
```

**Why needed:**

- Allows **`kubectl`** commands to connect to your cluster
- Required before you can deploy applications
- Sets this cluster as your default

# **Step 7: Verify Cluster**

```bash
kubectl get nodes
```

**What this does:**

- Connects to your GKE cluster
- Lists all nodes (worker machines)

**Output you'll see:**

```bash
No resources found
```

**Wait, no nodes?** This is **NORMAL** for Autopilot!

**Why:**

- Autopilot creates nodes **only when you deploy pods**
- No pods = no nodes = no cost! 💰
- Nodes appear automatically when needed

```bash
kubectl run test --image=nginx
kubectl get nodes
# Now you'll see nodes!
```

## **Step 8: Check Outputs**

```bash
terraform output
```

**What this does:**

- Shows all output values from your Terraform configuration
- Provides important information you'll need

**Output you'll see:**

```bash
artifact_registry_url = "us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys"
configure_kubectl = "gcloud container clusters get-credentials product-recsys-mlops-gke --region us-east1 --project product-recsys-mlops"
docker_push_example = "docker push us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/recsys-api:latest"
gcs_bucket = "product-recsys-mlops-recsys-data"
gcs_bucket_url = "gs://product-recsys-mlops-recsys-data"
project_id = "product-recsys-mlops"
region = "us-east1"
```

**How to use these:**

```bash
# Get specific output
terraform output gcs_bucket
# Output: "product-recsys-mlops-recsys-data"

# Get raw value (no quotes)
terraform output -raw gcs_bucket
# Output: product-recsys-mlops-recsys-data

# Use in commands
gsutil ls gs://$(terraform output -raw gcs_bucket)
```

**Summary Timeline**

```bash
Step 1: Set project          → 1 second
Step 2: Enable APIs          → 30 seconds
Step 3: terraform init       → 30 seconds
Step 4: terraform plan       → 10 seconds
Step 5: terraform apply      → 10-15 minutes ⏰
Step 6: configure kubectl    → 5 seconds
Step 7: verify cluster       → 2 seconds
Step 8: check outputs        → 1 second

Total: ~15 minutes
```
