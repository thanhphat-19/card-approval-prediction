# CI/CD Pipeline Guide

Jenkins pipeline for automated testing, building, and deployment with model quality gates.

```
Code Push → Jenkins → Lint → SonarQube → Model Evaluation & Download → Build → Scan → Push → Deploy
```

---

## Step 1: Deploy Jenkins VM

```bash
cd ansible
source ../config.env

# Run Ansible playbooks
ansible-playbook playbooks/01_create_jenkins_vm.yml -i inventory/hosts.ini \
  -e "gcp_project_id=${GCP_PROJECT_ID}" \
  -e "gcp_region=${GCP_REGION}" \
  -e "gcp_zone=${GCP_ZONE}"

ansible-playbook playbooks/02_install_docker.yml -i inventory/hosts.ini \
  -e "gcp_project_id=${GCP_PROJECT_ID}" -e "gcp_zone=${GCP_ZONE}"

ansible-playbook playbooks/03_deploy_jenkins.yml -i inventory/hosts.ini \
  -e "gcp_project_id=${GCP_PROJECT_ID}" -e "gcp_zone=${GCP_ZONE}"

# Get Jenkins IP
gcloud compute instances describe jenkins-server \
  --zone=${GCP_ZONE} --project=${GCP_PROJECT_ID} \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

## Step 2: Initial Jenkins Setup

**Access:** `http://<JENKINS_IP>:8080`

**Get initial password:**
```bash
gcloud compute ssh jenkins-server --zone=${GCP_ZONE} --project=${GCP_PROJECT_ID} \
  --command="sudo docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
```

**Install plugins:** Manage Jenkins → Plugins → Available:
- `SonarQube Scanner`
- `GitHub Branch Source`
- `Docker Pipeline`
- `Google Kubernetes Engine`

---

## Step 3: Configure SonarQube

**Access:** `http://<JENKINS_IP>:9000` (admin / admin)

1. Generate token: My Account → Security → Generate Tokens
2. In Jenkins: Manage Jenkins → System → SonarQube servers:
   - Name: `SonarQube`
   - URL: `http://<JENKINS_IP>:9000`
   - Token: Add credential with generated token

---

## Step 4: Generate Service Account Key

**Critical:** Generate a fresh service account key for Jenkins authentication.

```bash

source config.env
# Generate new key (use standard location)
mkdir -p ~/secrets
gcloud iam service-accounts keys create ~/secrets/gcp-key.json \
  --iam-account=${GSA_EMAIL} \
  --project=${PROJECT_ID}

# Verify the key works
gcloud auth activate-service-account --key-file=~/secrets/gcp-key.json
gcloud auth print-access-token  # Should succeed without errors

# Switch back to your account
gcloud config set account <your-email@gmail.com>
```

**Save this key file** - you'll upload it to Jenkins in Step 6.

---

## Step 5: Grant IAM Permissions

```bash

source config.env
# GCS Storage (for MLflow artifacts)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/storage.objectAdmin"

# Artifact Registry (push images)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# GKE Cluster Viewer (get credentials)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/container.clusterViewer"

# GKE Developer (deploy)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/container.developer"

# Verify permissions
gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${GSA_EMAIL}"
```

---

## Step 6: Configure Jenkins file


Update the config in `Jenkinsfile` to match your environment

```bash
environment {
        // =============================================================
        // GCP Configuration
        // =============================================================
        PROJECT_ID    = 'card-approval-prediction-mlops'
        ZONE          = 'us-east1-b'
        REGION        = 'us-east1'

        // GKE Configuration
        GKE_CLUSTER   = 'card-approval-prediction-mlops-gke'
        GKE_NAMESPACE = 'card-approval'

        // Docker Registry
        REGISTRY      = 'us-east1-docker.pkg.dev'
        REPOSITORY    = 'card-approval-prediction-mlops/card-approval-prediction-mlops-card-approval'
        IMAGE_NAME    = 'card-approval-api'

        // MLflow Configuration
        MLFLOW_TRACKING_URI = 'http://<EXTERNAL_INGRESS_IP>/mlflow'
        MODEL_NAME          = 'card_approval_model'
        MODEL_STAGE         = 'Production'
        F1_THRESHOLD        = '0.90'

        // SonarQube Configuration
        SONAR_HOST_URL = 'http://localhost:9000'
    }

```

## Step 7: Configure Jenkins Credentials

**Manage Jenkins → Credentials → Add:**

| ID | Type | Value | Purpose |
|----|------|-------|---------|
| `gcp-service-account` | Secret file | Upload `~/secrets/gcp-key.json` from Step 4 | GCP authentication |
| `gcp-project-id` | Secret text | Your GCP project ID | GCP project reference |
| `github-credentials` | Username with password | GitHub username + PAT | GitHub Branch Source (clone code) |
| `github-pat` | Secret text | GitHub PAT (same token) | GitHub Server API (PR status) |
| `sonarqube-token` | Secret text | SonarQube auth token | SonarQube analysis |

### GitHub Credentials Setup

**Step 1: Generate GitHub Personal Access Token**
- Go to: https://github.com/settings/tokens
- Generate new token (classic)
- Scopes: `repo`, `admin:repo_hook`
- Copy the token (you'll use it for BOTH credentials below)

**Step 2: Create `github-credentials` (Username with password)**
- **Kind:** Username with password
- **Username:** Your GitHub username
- **Password:** Paste your GitHub PAT
- **ID:** `github-credentials`
- **Purpose:** Used by GitHub Branch Source plugin to clone repository

**Step 3: Create `github-pat` (Secret text)**
- **Kind:** Secret text
- **Secret:** Paste the SAME GitHub PAT
- **ID:** `github-pat`
- **Purpose:** Used by GitHub Server API to report build status on PRs
---

## Step 8: Configure GitHub Server

**Manage Jenkins → System → GitHub:**
- Name: `GitHub`
- API URL: `https://api.github.com`
- Credentials: Select `github-pat`
- ☑️ Manage hooks

Click **Test connection** to verify.

---

## Step 8: Create Pipeline

**New Item → Multibranch Pipeline:**
- Name: `card-approval-prediction`
- Branch Sources → GitHub:
  - Credentials: `github-credentials`
  - URL: `https://github.com/<your-username>/card-approval-prediction`
- Build Configuration: Jenkinsfile

---

## Step 9: Setup GitHub Webhook

**GitHub repo → Settings → Webhooks → Add:**
- Payload URL: `http://<JENKINS_IP>:8080/github-webhook/`
- Content type: `application/json`
- Events: Pull requests, Pushes

---

## Pipeline Flow

| Stage | PR Branch | Main Branch | Description |
|-------|-----------|-------------|-------------|
| Checkout | ✓ | ✓ | Clone repository |
| Linting | ✓ | ✓ | Flake8, Pylint, Black, Isort |
| SonarQube | ✓ | ✓ | Code quality analysis |
| Model Evaluation & Download | ✗ | ✓ | Evaluate & download MLflow model |
| Build Image | ✗ | ✓ | Build Docker image with model |
| Security Scan | ✗ | ✓ | Trivy vulnerability scan |
| Push Image | ✗ | ✓ | Push to Artifact Registry |
| Deploy | ✗ | ✓ | Helm upgrade to GKE |

---

## Verify Pipeline

```bash
# Create test branch
git checkout -b feature/test-cicd
echo "# Test" >> README.md
git add . && git commit -m "test: trigger CI/CD"
git push origin feature/test-cicd

# Create PR → Jenkins runs lint
# Merge PR → Jenkins builds + deploys
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Model Evaluation Stage** | |
| `ERROR: Test features not found` | Test data not in git. Commit `training/data/processed/X_test.csv` and `y_test.csv` |
| `ERROR: No module named 'xgboost'` | Missing ML dependencies in Jenkinsfile pip install (check line 172) |
| Model evaluation fails | Check MLflow tracking URI is correct (line 35 in Jenkinsfile) |
| `No model found in Production stage` | No model registered in MLflow. Run training first |
| **Model Download Stage** | |
| Model download fails | Check MLflow connectivity and GCS permissions |
| `models/model_metadata.json not found` | Download script failed. Check MLflow artifacts |
| **Push Image Stage** | |
| `Invalid JWT Signature` | Service account key is old/corrupted. Regenerate (Step 4) |
| `Permission denied` (Artifact Registry) | Missing `roles/artifactregistry.writer` (Step 5) |
| Image push fails | Check `roles/artifactregistry.writer` granted |
| **Deploy to GKE Stage** | |
| `container.clusters.get permission` | Missing `roles/container.clusterViewer` (Step 5) |
| Deploy fails | Check `roles/container.developer` granted (Step 5) |
| `403 Permission Denied` | Verify all 4 IAM roles from Step 5 are granted |
| **General** | |
| PR status not showing | Verify `github-pat` is Secret text type |
| Lint fails | Run `black app/ training/src scripts && isort app/ training/src scripts` locally |
| Pipeline hangs | Check Jenkins logs and GCP service account permissions |



---

## Summary

Your CI/CD pipeline is now configured with:

✅ **Automated Testing** - Linting and code quality checks on every PR
✅ **Model Quality Gates** - F1 score threshold validation
✅ **Security Scanning** - Trivy vulnerability detection
✅ **Automated Deployment** - Push to GKE on main branch merge
✅ **GitHub Integration** - PR status updates

**Workflow:**
- Push to feature branch → Lint + SonarQube
- Merge to main → Model evaluation → Build → Scan → Push → Deploy

---

## Next Steps

1. **[NGINX Configuration](04_NGINX.md)** - Access deployed services via Ingress
