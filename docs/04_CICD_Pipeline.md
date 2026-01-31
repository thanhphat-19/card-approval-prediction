# CI/CD Pipeline Guide

Jenkins pipeline for automated testing, building, and deployment with model quality gates.

```
Code Push → Jenkins → Lint → SonarQube → Model Evaluation → Build → Scan → Push → Deploy
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
export PROJECT_ID=product-recsys-mlops
export GSA_NAME=mlflow-gcs
export SA_EMAIL=${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

# Generate new key (use standard location)
mkdir -p ~/secrets
gcloud iam service-accounts keys create ~/secrets/gcp-key.json \
  --iam-account=${SA_EMAIL} \
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
export SA_EMAIL=mlflow-gcs@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# GCS Storage (for MLflow artifacts)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

# Artifact Registry (push images)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# GKE Cluster Viewer (get credentials)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/container.clusterViewer"

# GKE Developer (deploy)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/container.developer"

# Verify permissions
gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${SA_EMAIL}"
```

---

## Step 6: Configure Jenkins Credentials

**Manage Jenkins → Credentials → Add:**

| ID | Type | Value |
|----|------|-------|
| `gcp-service-account` | Secret file | Upload `~/secrets/gcp-key.json` from Step 4 |
| `gcp-project-id` | Secret text | Your GCP project ID |
| `github-credentials` | Username/password | GitHub username + PAT |
| `github-pat` | Secret text | GitHub PAT (same token) |
| `sonarqube-token` | Secret text | SonarQube auth token |

**Generate GitHub PAT:** https://github.com/settings/tokens
- Scopes: `repo`, `admin:repo_hook`

**⚠️ Important:** Use the `/home/thanhphat/secrets/gcp-key.json` file generated in Step 4, not an old key.

---

## Step 7: Prepare Test Data for Model Evaluation

**Critical:** The Model Evaluation stage requires test data in git repository.

```bash
# Temporarily disable .gitignore for test data
# Comment out this line in .gitignore:
# training/data/processed/*.csv

# Add test data to git
git add training/data/processed/X_test.csv training/data/processed/y_test.csv
git commit -m "chore: add test data for CI/CD model evaluation"
git push origin main

# Re-enable .gitignore after push (optional, for security)
# Uncomment the line in .gitignore
```

**Why?** The `evaluate_model.py` script needs `X_test.csv` and `y_test.csv` to validate model quality during CI/CD. Without these files, the pipeline will fail with `ERROR: Test features not found`.

---

## Step 8: Configure GitHub Server

**Manage Jenkins → System → GitHub:**
- Name: `GitHub`
- API URL: `https://api.github.com`
- Credentials: Select `github-pat`
- ☑️ Manage hooks

Click **Test connection** to verify.

---

## Step 9: Create Pipeline

**New Item → Multibranch Pipeline:**
- Name: `card-approval-prediction`
- Branch Sources → GitHub:
  - Credentials: `github-credentials`
  - URL: `https://github.com/<your-username>/card-approval-prediction`
- Build Configuration: Jenkinsfile

---

## Step 10: Setup GitHub Webhook

**GitHub repo → Settings → Webhooks → Add:**
- Payload URL: `http://<JENKINS_IP>:8080/github-webhook/`
- Content type: `application/json`
- Events: Pull requests, Pushes

---

## Pipeline Flow

| Stage | PR Branch | Main Branch | Description |
|-------|-----------|-------------|-------------|
| Checkout |   |   | Clone repository |
| Linting |   |   | Flake8, Pylint, Black, Isort |
| SonarQube |   |   | Code quality analysis |
| Model Evaluation |  |   | Evaluate MLflow model (F1 ≥ 0.90) |
| Build Image |  |   | Build Docker image |
| Security Scan |  |   | Trivy vulnerability scan |
| Push Image |  |   | Push to Artifact Registry |
| Deploy |  |   | Helm upgrade to GKE |

### Model Quality Gate

The pipeline includes a **Model Evaluation** stage that:
1. Loads the latest Production model from MLflow
2. Evaluates against test data (`data/processed/`)
3. Checks if F1 score meets threshold (default: 0.90)
4. **Fails the build** if model doesn't meet quality requirements

```bash
# Run evaluation locally
export MLFLOW_TRACKING_URI=http://<MLFLOW_IP>/mlflow
python scripts/evaluate_model.py --threshold 0.90
```

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
| `ERROR: Test features not found` | Test data not in git. Follow Step 7 to add test files |
| `ERROR: No module named 'xgboost'` | Missing ML dependencies in Jenkinsfile pip install |
| Model evaluation fails | Check MLflow tracking URI is correct |
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
| Lint fails | Run `black app/ && isort app/` locally |
| Pipeline hangs | Check Jenkins logs and GCP service account permissions |

### Common Service Account Key Issues

If you see `Invalid JWT Signature` error:

```bash
# 1. Regenerate service account key (use standard location)
mkdir -p ~/secrets
gcloud iam service-accounts keys create ~/secrets/gcp-key.json \
  --iam-account=mlflow-gcs@product-recsys-mlops.iam.gserviceaccount.com \
  --project=product-recsys-mlops

# 2. Verify it works
gcloud auth activate-service-account --key-file=~/secrets/gcp-key.json
gcloud auth print-access-token

# 3. Update Jenkins credential (Manage Jenkins → Credentials → gcp-service-account)
```
