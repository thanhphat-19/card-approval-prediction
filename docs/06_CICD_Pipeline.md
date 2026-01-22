# CI/CD Pipeline Guide

## Overview

Jenkins pipeline for automated testing, building, and deployment.

```
Pipeline Flow:
Code Push → Jenkins → Test → Build → Push → Deploy → Verify
```

---

# **Step 1: Pipeline Stages**

```
┌─────────────────────────────────────────────────────────────┐
│                     JENKINS PIPELINE                         │
├─────────────────────────────────────────────────────────────┤
│  1. Checkout Code                                            │
│         ↓                                                    │
│  2. Lint & Test (parallel)                                   │
│         ↓                                                    │
│  3. Build Docker Image                                       │
│         ↓                                                    │
│  4. Security Scan (Trivy)                                    │
│         ↓                                                    │
│  5. Push to Artifact Registry                                │
│         ↓                                                    │
│  6. Deploy to GKE (Helm)                                     │
│         ↓                                                    │
│  7. Smoke Tests                                              │
└─────────────────────────────────────────────────────────────┘
```

---

# **Step 2: Jenkinsfile Structure**

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        PROJECT_ID = 'product-recsys-mlops'
        REGISTRY = 'us-east1-docker.pkg.dev'
        IMAGE = "${REGISTRY}/${PROJECT_ID}/product-recsys-mlops-recsys/card-approval-api"
    }

    stages {
        stage('Checkout') { ... }
        stage('Lint & Test') { ... }
        stage('Build') { ... }
        stage('Push') { ... }
        stage('Deploy') { ... }
    }
}
```

---

# **Step 3: Lint & Test Stage**

```groovy
stage('Lint & Test') {
    parallel {
        stage('Lint') {
            steps {
                sh 'pip install flake8 black isort'
                sh 'flake8 app/ --max-line-length=120'
                sh 'black --check app/'
                sh 'isort --check-only app/'
            }
        }
        stage('Test') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pytest tests/ -v --junitxml=test-results.xml'
            }
        }
    }
}
```

**What this does:**
- Runs linting and tests in parallel
- Checks code style (black, isort, flake8)
- Runs pytest with JUnit output

---

# **Step 4: Build Docker Image**

```groovy
stage('Build') {
    steps {
        sh "docker build -t ${IMAGE}:${BUILD_NUMBER} ."
        sh "docker tag ${IMAGE}:${BUILD_NUMBER} ${IMAGE}:latest"
    }
}
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# **Step 5: Security Scan**

```groovy
stage('Security Scan') {
    steps {
        sh "trivy image --severity HIGH,CRITICAL ${IMAGE}:${BUILD_NUMBER}"
    }
}
```

**What this does:**
- Scans image for vulnerabilities
- Fails if HIGH or CRITICAL found
- Reports CVEs

---

# **Step 6: Push to Registry**

```groovy
stage('Push') {
    steps {
        sh "gcloud auth configure-docker ${REGISTRY}"
        sh "docker push ${IMAGE}:${BUILD_NUMBER}"
        sh "docker push ${IMAGE}:latest"
    }
}
```

**What this does:**
- Authenticates to Artifact Registry
- Pushes versioned image
- Updates latest tag

---

# **Step 7: Deploy to GKE**

```groovy
stage('Deploy') {
    steps {
        sh """
            gcloud container clusters get-credentials card-approval-prediction-mlops-gke \
                --zone us-east1-b --project ${PROJECT_ID}

            helm upgrade --install card-approval helm-charts/card-approval \
                -n card-approval \
                --set api.image.tag=${BUILD_NUMBER}
        """
    }
}
```

**What this does:**
- Gets cluster credentials
- Updates Helm release with new image tag
- Rolling update (zero downtime)

---

# **Step 8: Smoke Tests**

```groovy
stage('Smoke Test') {
    steps {
        sh """
            sleep 30
            kubectl port-forward svc/card-approval-api 8000:80 -n card-approval &
            sleep 5
            curl -f http://localhost:8000/health
            pkill -f port-forward
        """
    }
}
```

**What this does:**
- Waits for deployment
- Tests health endpoint
- Fails pipeline if unhealthy

---

# **Step 9: Manual Trigger**

```bash
# Trigger via Jenkins CLI
java -jar jenkins-cli.jar -s http://jenkins:8080 build card-approval-pipeline

# Or via curl
curl -X POST http://jenkins:8080/job/card-approval-pipeline/build \
  --user admin:token
```

---

# **Step 10: View Pipeline**

```bash
# Jenkins URL
open http://jenkins:8080/job/card-approval-pipeline

# Blue Ocean UI (better visualization)
open http://jenkins:8080/blue/organizations/jenkins/card-approval-pipeline
```

---

## Jenkins Credentials Required

| Credential ID | Type | Purpose |
|---------------|------|---------|
| `gcp-service-account` | File | GCP authentication |
| `docker-registry` | Username/Password | Artifact Registry |
| `github-token` | Secret text | GitHub webhook |

---

## Troubleshooting

**Build failed - lint:**
```bash
# Fix locally
black app/
isort app/
flake8 app/ --max-line-length=120
```

**Deploy failed - helm:**
```bash
# Check helm status
helm list -n card-approval
helm history card-approval -n card-approval

# Rollback
helm rollback card-approval 1 -n card-approval
```
