# Card Approval Prediction - CI/CD Pipeline

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Pipeline Stages](#pipeline-stages)
- [Setup Instructions](#setup-instructions)
- [Jenkins Configuration](#jenkins-configuration)
- [SonarQube Setup](#sonarqube-setup)
- [GitHub Integration](#github-integration)
- [Pipeline Operations](#pipeline-operations)
- [Monitoring & Alerts](#monitoring--alerts)
- [Troubleshooting](#troubleshooting)

## 🚀 Overview

This project implements a complete CI/CD pipeline for the Card Approval Prediction API with automated testing, code quality analysis, container building, and Kubernetes deployment.

### Components

- **Jenkins** - CI/CD orchestration
- **SonarQube** - Code quality & security analysis
- **Ansible** - Infrastructure automation
- **Docker** - Container building
- **Helm** - Kubernetes deployment
- **GitHub** - Source control & webhooks
- **Prometheus/Grafana** - Monitoring

### Pipeline Flow

```
1. Code Push to GitHub
   ↓
2. Webhook Triggers Jenkins
   ↓
3. Checkout Code
   ↓
4. Parallel: Unit Tests + Linting
   ↓
5. SonarQube Analysis
   ↓
6. Quality Gate Check
   ↓
7. Build Docker Image
   ↓
8. Security Scan (Trivy)
   ↓
9. Push to Google Container Registry
   ↓
10. Deploy to GKE using Helm
   ↓
11. Smoke Tests
   ↓
12. Monitoring Active
```

## 🏗️ Architecture

```
┌─────────────┐
│   GitHub    │ ──webhook──> ┌──────────┐
└─────────────┘              │ Jenkins  │
                             │ (GCE VM) │
                             └────┬─────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
              ┌──────────┐  ┌──────────┐  ┌─────────┐
              │SonarQube │  │  Docker  │  │   GKE   │
              └──────────┘  │ Registry │  │Cluster  │
                            └──────────┘  └─────────┘
                                               │
                                          ┌────┴────┐
                                          ↓         ↓
                                    ┌──────────┐ ┌──────────┐
                                    │Prometheus│ │ Grafana  │
                                    └──────────┘ └──────────┘
```

## 📝 Pipeline Stages

### Stage 1: Checkout
- Pulls latest code from GitHub
- Sets environment variables (GIT_COMMIT, GIT_BRANCH)

### Stage 2: Code Quality Analysis (Parallel)

**Unit Tests:**
```groovy
stage('Unit Tests') {
    agent {
        docker {
            image 'python:3.10-slim'
        }
    }
    steps {
        sh '''
            pip install -r requirements.txt
            pip install pytest pytest-cov
            pytest tests/ --cov=app --cov-report=xml
        '''
    }
}
```

**Linting:**
```groovy
stage('Linting') {
    steps {
        sh '''
            flake8 app cap_model/src
            pylint app cap_model/src
            black --check app cap_model/src
        '''
    }
}
```

### Stage 3: SonarQube Analysis
- Static code analysis
- Code coverage check
- Security vulnerability scan
- Technical debt calculation

### Stage 4: Quality Gate
- Enforces quality standards
- Aborts pipeline if quality gate fails
- Runs only on main/develop branches

### Stage 5: Build Docker Image
```bash
docker build -t ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} .
docker tag ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} \
           ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest
```

### Stage 6: Security Scan
```bash
docker run aquasec/trivy image \
  --severity HIGH,CRITICAL \
  ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
```

### Stage 7: Push to Registry
- Authenticates with Google Container Registry
- Pushes both versioned and latest tags

### Stage 8: Deploy to GKE
```bash
helm upgrade --install card-approval ./helm-charts/card-approval \
  --namespace card-approval \
  --set api.image.tag=${IMAGE_TAG} \
  --atomic \
  --timeout 10m
```

### Stage 9: Smoke Tests
- Health check validation
- Prediction endpoint test
- Verifies deployment success

## 🛠️ Setup Instructions

### Step 1: Deploy Jenkins Infrastructure

```bash
# Navigate to ansible directory
cd ansible

# Install Ansible dependencies
pip install -r requirements.txt

# Deploy Jenkins on GCE
./deploy_jenkins.sh
```

This will:
1. Create GCE instance for Jenkins
2. Install Docker and dependencies
3. Deploy Jenkins container
4. Deploy SonarQube container

**Output will show:**
```
Jenkins URL: http://<EXTERNAL_IP>:8080
SonarQube URL: http://<EXTERNAL_IP>:9000
Initial Admin Password: <password>
```

### Step 2: Access Jenkins

```bash
# Get external IP
JENKINS_IP=$(gcloud compute instances describe jenkins-server \
  --zone=us-east1-b \
  --format='value(networkInterfaces[0].accessConfigs[0].natIP)')

echo "Jenkins: http://${JENKINS_IP}:8080"
```

Open in browser and complete setup wizard.

### Step 3: Verify Services

```bash
# SSH to Jenkins server
gcloud compute ssh jenkins-server --zone=us-east1-b

# Check containers
docker ps

# Should show:
# - jenkins
# - sonarqube
```

## ⚙️ Jenkins Configuration

### Initial Setup

1. **Unlock Jenkins**
   - Use initial admin password from Ansible output
   - Or get it: `gcloud compute ssh jenkins-server --zone=us-east1-b --command='sudo docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword'`

2. **Install Plugins**

   **Required:**
   - Git
   - GitHub Integration
   - Docker Pipeline
   - Kubernetes CLI
   - Google Container Registry Auth
   - SonarQube Scanner
   - Blue Ocean (optional, for better UI)

   **Installation:**
   - Manage Jenkins → Manage Plugins → Available
   - Search and install each plugin
   - Restart Jenkins

3. **Create Admin User**
   - Username: admin
   - Password: (set strong password)
   - Email: your-email@example.com

### Configure Credentials

Go to: **Manage Jenkins → Manage Credentials → Global → Add Credentials**

#### 1. GCP Service Account

```bash
# Create service account key
gcloud iam service-accounts keys create gcp-sa-key.json \
  --iam-account=jenkins@product-recsys-mlops.iam.gserviceaccount.com

# Upload in Jenkins:
# - Kind: Secret file
# - ID: gcp-service-account
# - File: Upload gcp-sa-key.json
```

#### 2. GitHub Personal Access Token

```bash
# Create token at: https://github.com/settings/tokens
# Scopes: repo, admin:repo_hook

# Add in Jenkins:
# - Kind: Username with password
# - ID: github-credentials
# - Username: your-github-username
# - Password: your-github-token
```

#### 3. SonarQube Token

```bash
# Generate in SonarQube:
# User → My Account → Security → Generate Token

# Add in Jenkins:
# - Kind: Secret text
# - ID: sonarqube-token
# - Secret: your-sonarqube-token
```

### Configure SonarQube Server

**Manage Jenkins → Configure System → SonarQube servers**

```
Name: SonarQube
Server URL: http://localhost:9000
Server authentication token: sonarqube-token (select credential)
```

### Configure Global Tool Configuration

**Manage Jenkins → Global Tool Configuration**

**SonarQube Scanner:**
- Name: SonarScanner
- Install automatically: ✓
- Version: Latest

**Docker:**
- Name: docker
- Install automatically: ✓

### Create Multibranch Pipeline

1. **New Item** → Enter name: `card-approval-pipeline`
2. Select: **Multibranch Pipeline**
3. Configure:

   **Branch Sources:**
   ```
   Add source: GitHub
   Credentials: github-credentials
   Repository URL: https://github.com/yourusername/card-approval-prediction
   ```

   **Build Configuration:**
   ```
   Mode: by Jenkinsfile
   Script Path: Jenkinsfile
   ```

   **Scan Multibranch Pipeline Triggers:**
   ```
   ✓ Periodically if not otherwise run
   Interval: 1 minute
   ```

4. **Save** → **Scan Repository Now**

## 🔍 SonarQube Setup

### Initial Configuration

1. **Access SonarQube**
   ```
   URL: http://<JENKINS_IP>:9000
   Default credentials: admin/admin
   ```

2. **Change Password**
   - First login will prompt password change
   - Use strong password

3. **Create Project**
   - Projects → Create Project
   - Project key: `card-approval-prediction`
   - Display name: `Card Approval Prediction API`

4. **Generate Token**
   - User → My Account → Security
   - Generate Token: `jenkins-integration`
   - Copy token (use in Jenkins credentials)

### Quality Gate Configuration

**Quality Gates → Create**

Name: `Card Approval Standards`

**Conditions:**
```
On Overall Code:
- Coverage < 80% → ERROR
- Duplicated Lines > 3% → ERROR

On New Code:
- Coverage < 80% → ERROR
- Maintainability Rating > A → ERROR
- Reliability Rating > A → ERROR
- Security Rating > A → ERROR
```

**Set as Default** for your project.

### Quality Profiles

**Quality Profiles → Python**

Use or customize:
- Sonar way (default)
- Enable security rules
- Enable code smell detection

## 🔗 GitHub Integration

### Setup Webhook

1. **In GitHub Repository:**
   - Settings → Webhooks → Add webhook

2. **Configure:**
   ```
   Payload URL: http://<JENKINS_IP>:8080/github-webhook/
   Content type: application/json
   Secret: (optional, set webhook secret)

   Events:
   ✓ Push events
   ✓ Pull request events
   ```

3. **Save**

### Or Use Script

```bash
# Update script with your details
nano scripts/setup-github-webhook.sh

# Set:
# - GITHUB_REPO_OWNER
# - GITHUB_TOKEN
# - WEBHOOK_SECRET

# Run
./scripts/setup-github-webhook.sh
```

### Verify Webhook

1. Make a commit and push
2. Check GitHub: Settings → Webhooks → Recent Deliveries
3. Should show 200 response
4. Jenkins should trigger build automatically

## 🎮 Pipeline Operations

### Trigger Build

**Automatic (Webhook):**
```bash
git add .
git commit -m "Update feature"
git push origin main
```

**Manual:**
- Jenkins → card-approval-pipeline → main → Build Now

### Monitor Build

**Jenkins UI:**
- Pipeline view shows all stages
- Click stage for logs
- Blue Ocean provides better visualization

**CLI:**
```bash
# Watch build status
watch -n 2 'curl -s http://<JENKINS_IP>:8080/job/card-approval-pipeline/job/main/lastBuild/api/json | jq ".result"'
```

### View Logs

```bash
# SSH to Jenkins server
gcloud compute ssh jenkins-server --zone=us-east1-b

# View Jenkins logs
docker logs -f jenkins

# View specific build log (from Jenkins UI)
```

### Rollback Failed Deployment

If deployment fails, Helm automatically rolls back due to `--atomic` flag.

**Manual rollback:**
```bash
# Get release history
helm history card-approval -n card-approval

# Rollback to previous
helm rollback card-approval -n card-approval

# Rollback to specific revision
helm rollback card-approval 3 -n card-approval
```

### Promote to Production

**Strategy 1: Separate Pipeline**
```groovy
// In Jenkinsfile
when {
    branch 'production'
}
```

**Strategy 2: Manual Approval**
```groovy
stage('Deploy to Production') {
    input {
        message "Deploy to production?"
        ok "Deploy"
    }
    steps {
        // Deploy steps
    }
}
```

**Strategy 3: Tag-based Release**
```bash
git tag v1.0.0
git push origin v1.0.0

# Jenkins triggers on tag
```

## 📊 Monitoring & Alerts

### Application Metrics

**Prometheus Metrics Available:**
```
# Request metrics
fastapi_requests_total
fastapi_request_duration_seconds

# Resource metrics
process_cpu_seconds_total
process_resident_memory_bytes

# Custom metrics
predictions_total
prediction_duration_seconds
model_version_info
```

**Access Metrics:**
```bash
kubectl port-forward -n card-approval svc/card-approval-api 8000:80
curl http://localhost:8000/metrics
```

### Grafana Dashboards

**Setup:**
```bash
# Install kube-prometheus-stack
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Access Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Login: admin/prom-operator
```

**Create Custom Dashboard:**
1. Grafana → Dashboards → New Dashboard
2. Add Panel → Prometheus query:
   ```promql
   rate(fastapi_requests_total[5m])
   ```
3. Save dashboard

### Jenkins Monitoring

**Install Plugins:**
- Prometheus Metrics Plugin
- Monitoring Plugin

**Expose Metrics:**
- Manage Jenkins → Configure System → Prometheus
- Enable: ✓

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'jenkins'
    static_configs:
      - targets: ['<JENKINS_IP>:8080']
    metrics_path: '/prometheus'
```

### Alerting Rules

**Create AlertManager config:**
```yaml
# prometheus-alerts.yaml
groups:
  - name: cicd-alerts
    rules:
      - alert: PipelineFailureRate
        expr: rate(jenkins_job_failure_total[5m]) > 0.2
        for: 5m
        annotations:
          summary: "High pipeline failure rate"

      - alert: DeploymentFailed
        expr: up{job="card-approval-api"} == 0
        for: 5m
        annotations:
          summary: "Card Approval API is down"
```

## 🔧 Troubleshooting

### Jenkins Issues

**Issue: Jenkins not accessible**
```bash
# Check if VM is running
gcloud compute instances list | grep jenkins

# Check if Jenkins container is running
gcloud compute ssh jenkins-server --zone=us-east1-b --command='docker ps'

# Check Jenkins logs
gcloud compute ssh jenkins-server --zone=us-east1-b --command='docker logs jenkins'
```

**Issue: Build fails at Docker stage**
```bash
# Ensure Docker socket is mounted
gcloud compute ssh jenkins-server --zone=us-east1-b --command='docker exec jenkins docker ps'

# Should work without errors
```

**Issue: Can't push to GCR**
```bash
# Verify GCP credentials
# In Jenkins build log, check:
# - gcloud auth activate-service-account
# - gcloud auth configure-docker

# Test manually
gcloud auth activate-service-account --key-file=<key-file>
gcloud auth configure-docker us-east1-docker.pkg.dev
docker push us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:test
```

### SonarQube Issues

**Issue: Quality gate fails**
```bash
# Check SonarQube analysis results
# Visit: http://<JENKINS_IP>:9000/dashboard?id=card-approval-prediction

# View issues:
# - Code Smells
# - Bugs
# - Vulnerabilities
# - Coverage

# Fix issues and re-run pipeline
```

**Issue: SonarQube not accessible**
```bash
# Check container status
gcloud compute ssh jenkins-server --zone=us-east1-b --command='docker ps | grep sonarqube'

# Check logs
gcloud compute ssh jenkins-server --zone=us-east1-b --command='docker logs sonarqube'

# Restart if needed
gcloud compute ssh jenkins-server --zone=us-east1-b --command='docker restart sonarqube'
```

### Pipeline Issues

**Issue: Webhook not triggering**
```bash
# Check webhook in GitHub
# Repository → Settings → Webhooks
# Recent Deliveries should show 200 response

# Test manually
curl -X POST http://<JENKINS_IP>:8080/github-webhook/ \
  -H "Content-Type: application/json" \
  -d '{"repository": {"name": "card-approval-prediction"}}'

# Check Jenkins system log
# Manage Jenkins → System Log
```

**Issue: Helm deployment fails**
```bash
# Check Helm status
helm status card-approval -n card-approval

# View release history
helm history card-approval -n card-approval

# Get detailed error
kubectl describe pod <pod-name> -n card-approval

# Check events
kubectl get events -n card-approval --sort-by='.lastTimestamp'
```

### Build Performance

**Issue: Slow builds**

**Optimize:**
```groovy
// Use Docker layer caching
stage('Build') {
    options {
        skipDefaultCheckout true
    }
    // Build only on changes
}

// Parallel stages
parallel {
    stage('Test 1') { }
    stage('Test 2') { }
}

// Cleanup
post {
    always {
        cleanWs()
        sh 'docker image prune -f'
    }
}
```

## 📚 Best Practices

### Security

1. **Never commit secrets** - Use Jenkins credentials
2. **Scan images** - Always run Trivy before deployment
3. **Use service accounts** - Avoid user credentials
4. **Enable RBAC** - Restrict Jenkins permissions
5. **Regular updates** - Keep Jenkins and plugins updated

### Pipeline Design

1. **Fail fast** - Run quick tests first
2. **Parallel execution** - Speed up builds
3. **Atomic deployments** - Use `--atomic` flag
4. **Meaningful stages** - Clear stage names
5. **Proper error handling** - Catch and report errors

### Code Quality

1. **Enforce quality gates** - Don't merge bad code
2. **Track coverage** - Aim for >80%
3. **Fix security issues** - Address vulnerabilities immediately
4. **Regular refactoring** - Reduce technical debt
5. **Code reviews** - Use pull requests

### Monitoring

1. **Monitor metrics** - Track build success rate
2. **Set up alerts** - Get notified of failures
3. **Log aggregation** - Centralize logs
4. **Performance tracking** - Monitor build times
5. **Capacity planning** - Scale infrastructure as needed

## 🎓 Additional Resources

- [Jenkinsfile Documentation](Jenkinsfile)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [SonarQube Documentation](https://docs.sonarqube.org/)
- [Helm Documentation](https://helm.sh/docs/)
- [Ansible Playbooks](ansible/playbooks/)

## 📞 Support

### Useful Commands

```bash
# Jenkins
docker logs -f jenkins
docker restart jenkins
docker exec -it jenkins bash

# SonarQube
docker logs -f sonarqube
docker restart sonarqube

# Pipeline
helm list -n card-approval
kubectl get pods -n card-approval
kubectl logs -f deployment/card-approval-api -n card-approval

# Monitoring
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
kubectl port-forward -n monitoring svc/monitoring-prometheus-server 9090:80
```

### Getting Help

1. **Check logs** - Start with Jenkins build logs
2. **Review documentation** - Check this guide
3. **Search issues** - Look for similar problems
4. **Open ticket** - Create detailed issue report

---

**Happy Building! 🚀**
