# CI/CD Pipeline Guide

Jenkins pipeline for automated testing, building, and deployment.

```
Code Push → Jenkins → Lint → Build → Scan → Push → Deploy
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

## Step 4: Grant IAM Permissions

```bash
export SA_EMAIL=mlflow-gcs@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Artifact Registry (push images)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# GKE (deploy)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/container.clusterViewer"
```

---

## Step 5: Configure Jenkins Credentials

**Manage Jenkins → Credentials → Add:**

| ID | Type | Value |
|----|------|-------|
| `gcp-service-account` | Secret file | Upload `~/secrets/gcp-key.json` |
| `gcp-project-id` | Secret text | Your GCP project ID |
| `github-credentials` | Username/password | GitHub username + PAT |
| `github-pat` | Secret text | GitHub PAT (same token) |
| `sonarqube-token` | Secret text | SonarQube token |

**Generate GitHub PAT:** https://github.com/settings/tokens
- Scopes: `repo`, `admin:repo_hook`

---

## Step 6: Configure GitHub Server

**Manage Jenkins → System → GitHub:**
- Name: `GitHub`
- API URL: `https://api.github.com`
- Credentials: Select `github-pat`
- ☑️ Manage hooks

Click **Test connection** to verify.

---

## Step 7: Create Pipeline

**New Item → Multibranch Pipeline:**
- Name: `card-approval-prediction`
- Branch Sources → GitHub:
  - Credentials: `github-credentials`
  - URL: `https://github.com/<your-username>/card-approval-prediction`
- Build Configuration: Jenkinsfile

---

## Step 8: Setup GitHub Webhook

**GitHub repo → Settings → Webhooks → Add:**
- Payload URL: `http://<JENKINS_IP>:8080/github-webhook/`
- Content type: `application/json`
- Events: Pull requests, Pushes

---

## Pipeline Flow

| Stage | PR Branch | Main Branch |
|-------|-----------|-------------|
| Checkout | ✅ | ✅ |
| Linting | ✅ | ✅ |
| Build Image | ❌ | ✅ |
| Security Scan | ❌ | ✅ |
| Push Image | ❌ | ✅ |
| Deploy | ❌ | ✅ |

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
| Image push fails | Check `roles/artifactregistry.writer` granted |
| Deploy fails | Check `roles/container.developer` granted |
| PR status not showing | Verify `github-pat` is Secret text type |
| Lint fails | Run `black app/ && isort app/` locally |
