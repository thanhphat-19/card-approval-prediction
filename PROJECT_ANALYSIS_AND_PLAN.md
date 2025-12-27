# Card Approval Prediction - Comprehensive Project Analysis & Implementation Plan

**Analysis Date:** December 13, 2025
**Status:** Phase 1-2 Complete | Phase 3-4 Planning

---

## 📊 EXECUTIVE SUMMARY

### Current Project Status: ~40% Complete

**✅ Completed (Phase 1-2):**
- GCP Infrastructure (GKE, GCS, Artifact Registry)
- Kubernetes Deployments (PostgreSQL, MLflow)
- Complete ML Pipeline (Data → Training → MLflow Registry)
- Model Development & Experimentation Framework

**❌ Not Started (Phase 3-4):**
- FastAPI Application (empty files)
- Application-level Database & Redis Integration
- CI/CD Pipeline (Jenkins + SonarQube)
- Ansible Infrastructure for Jenkins
- Docker Compose for Development
- GitHub Webhooks & Automated Deployments

---

## 🏗️ DETAILED CURRENT STATE ANALYSIS

### 1. INFRASTRUCTURE LAYER ✅ (100% Complete)

#### **Terraform Configuration**
**Location:** `/terraform/`

**Resources Deployed:**
```hcl
✓ GKE Autopilot Cluster (product-recsys-mlops-gke)
✓ GCS Bucket (product-recsys-mlops-recsys-data)
✓ Artifact Registry (asia-southeast1-docker.pkg.dev)
✓ MLflow Service Account + Workload Identity
✓ IAM Bindings (Storage Admin + Workload Identity User)
```

**Configuration:**
- **Provider:** GCP (Terraform ~> 5.0)
- **Region:** us-east1 (configurable)
- **Cluster Type:** Autopilot (serverless Kubernetes)
- **Storage Lifecycle:** 90-day deletion policy
- **Cost Optimization:** Autopilot mode, HDD storage

**Strengths:**
✓ Well-structured modular design
✓ Workload Identity configured (no service account keys)
✓ Outputs well-defined for downstream use
✓ Production-ready security patterns

**Recommendations:**
⚠️ Add terraform state backend (GCS) for team collaboration
⚠️ Add environments (dev/staging/prod) via workspaces
⚠️ Implement secrets management (Google Secret Manager)
⚠️ Add cost budget alerts

---

### 2. KUBERNETES LAYER ✅ (90% Complete)

#### **Helm Charts Structure**
**Location:** `/helm-charts/`

```
helm-charts/
├── infrastructure/
│   ├── postgres/          ✅ PostgreSQL for MLflow backend
│   └── mlflow/            ✅ MLflow tracking server
└── recsys-training/       ✅ Umbrella chart (Postgres + MLflow)
```

#### **PostgreSQL Deployment**
```yaml
Image: postgres:15-alpine
Resources: 256Mi-512Mi RAM, 250m-500m CPU
Storage: 10Gi (standard-rwo HDD)
Persistence: Enabled with Retain policy
Database: mlflow (for MLflow backend)
```

**Configuration Analysis:**
- ✓ Persistent storage with retain policy (data safety)
- ✓ Resource limits defined
- ⚠️ Credentials hardcoded in values.yaml (should use K8s Secrets)
- ⚠️ No backup strategy implemented
- ⚠️ Single replica (not HA)

#### **MLflow Deployment**
```yaml
Image: ghcr.io/mlflow/mlflow:v3.6.0
Backend: PostgreSQL (connection string in deployment)
Artifacts: GCS (gs://product-recsys-mlops-recsys-data/mlflow-artifacts/)
Service Account: mlflow-sa (Workload Identity enabled)
Resources: 512Mi-1Gi RAM, 500m-1000m CPU
```

**Features:**
- ✓ PostgreSQL backend (not SQLite)
- ✓ GCS artifact storage (scalable, durable)
- ✓ Workload Identity (no keys needed)
- ✓ Health checks configured
- ⚠️ Ingress disabled (only port-forward access)
- ⚠️ No authentication/authorization

**Missing Infrastructure Components:**
- ❌ Redis (for API caching/session management)
- ❌ Application PostgreSQL database (separate from MLflow)
- ❌ Monitoring stack (Prometheus + Grafana)
- ❌ SonarQube deployment

---

### 3. ML MODEL LAYER ✅ (100% Complete)

#### **Model Development Pipeline**
**Location:** `/cap_model/`

**Architecture:**
```
cap_model/
├── data/                   # Data management
│   ├── raw/               # Original datasets
│   └── processed/         # Train/test splits
├── src/                   # Core ML code
│   ├── data/              # DataLoader
│   ├── features/          # FeatureEngineer
│   ├── models/            # ModelTrainer, ModelEvaluator
│   └── utils/             # MLflowRegistry, metrics, plotting
├── scripts/               # Executable pipelines
│   ├── run_preprocessing.py
│   ├── run_training.py
│   ├── register_model.py
│   └── inference.py
├── notebooks/             # EDA & experimentation
└── models/                # Saved artifacts
```

**ML Workflow:**
1. **Data Preprocessing** → Feature engineering, encoding, scaling
2. **Training** → Multiple models (Logistic, RandomForest, XGBoost, LightGBM)
3. **Evaluation** → Metrics, confusion matrix, ROC curves
4. **Registry** → MLflow model versioning (Staging/Production)
5. **Inference** → Single & batch predictions

**MLflow Integration:**
```python
✓ Experiment tracking
✓ Model registry (Staging/Production stages)
✓ Artifact logging (plots, metrics, models)
✓ Model versioning and lineage
✓ Registry API (MLflowRegistry class)
```

**Model Performance Targets:**
| Metric    | Baseline | Target | Production |
|-----------|----------|--------|------------|
| Accuracy  | 0.70     | 0.85   | 0.90       |
| Precision | 0.65     | 0.80   | 0.85       |
| Recall    | 0.60     | 0.75   | 0.80       |
| F1-Score  | 0.62     | 0.77   | 0.82       |
| ROC-AUC   | 0.75     | 0.88   | 0.92       |

**Strengths:**
✓ Professional ML code structure
✓ Complete preprocessing pipeline
✓ Multiple model support
✓ MLflow registry integration
✓ Inference scripts ready
✓ Well-documented with guides

**Gaps:**
⚠️ No unit tests for model code
⚠️ No data validation (Great Expectations, etc.)
⚠️ No model monitoring/drift detection
⚠️ No A/B testing framework

---

### 4. APPLICATION LAYER ❌ (0% Complete)

#### **FastAPI Application Status**
**Location:** `/app/`

**Current State:**
```
app/
├── main.py               # EMPTY ❌
├── routers/              # EMPTY ❌
├── schemas/              # EMPTY ❌
├── config/               # EMPTY ❌
├── core/                 # EMPTY ❌
└── utils/                # EMPTY ❌
```

**What's Missing:**
- ❌ FastAPI application setup
- ❌ API endpoints (/predict, /health, /models)
- ❌ Database models (SQLAlchemy)
- ❌ Redis integration
- ❌ MLflow model loading
- ❌ Request/response schemas
- ❌ Authentication/authorization
- ❌ Logging & monitoring
- ❌ Error handling
- ❌ API documentation

#### **Docker Configuration**
**Current Dockerfile:**
```dockerfile
FROM python:3.10.14-slim-bullseye
WORKDIR /app
RUN mkdir /app/src/ /app/logs/
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
```

**Issues:**
- ⚠️ No CMD/ENTRYPOINT (won't run)
- ⚠️ No application code copied
- ⚠️ No multi-stage build
- ⚠️ Basic requirements.txt (only mkdocs, mlflow)

#### **Docker Compose Status**
**Current docker-compose.yml:**
```yaml
services:
  app:
    build: .
    container_name: ai-prod-recsys
    env_file: .env
    ports:
      - 8000:8000
    restart: always
```

**Missing:**
- ❌ No PostgreSQL service
- ❌ No Redis service
- ❌ No MLflow service
- ❌ No network configuration
- ❌ No volume mounts
- ❌ Empty .env file

---

### 5. CI/CD LAYER ❌ (0% Complete)

#### **Jenkins Infrastructure**
**Status:** NOT DEPLOYED

**What's Needed:**
- ❌ GCE instance for Jenkins (n2-standard-2)
- ❌ Ansible playbooks for:
  - GCE instance creation
  - Docker installation
  - Jenkins deployment
- ❌ Jenkins configuration:
  - Kubernetes plugin
  - Docker Pipeline plugin
  - SonarQube Scanner plugin
  - GitHub plugin
  - Google Cloud SDK plugin
- ❌ Jenkins credentials:
  - GCP service account
  - GCR/Artifact Registry
  - GitHub PAT
  - SonarQube token

#### **Pipeline Components**
**Status:** NO JENKINSFILE

**Required Stages:**
```groovy
❌ Checkout (Git clone)
❌ Test (pytest + coverage)
❌ SonarQube Analysis (code quality)
❌ Quality Gate (pass/fail)
❌ Build Docker Image
❌ Push to Artifact Registry
❌ Deploy to GKE (helm upgrade)
❌ Notifications (Slack, email)
```

#### **SonarQube**
**Status:** NOT DEPLOYED

**Required:**
- ❌ SonarQube Helm deployment
- ❌ Persistent storage
- ❌ Quality gates configuration
- ❌ Python quality profile
- ❌ Project setup (prod-recsys-project)

#### **GitHub Integration**
**Status:** NOT CONFIGURED

**Missing:**
- ❌ GitHub webhook
- ❌ Multibranch pipeline job
- ❌ Branch protection rules
- ❌ PR checks automation

---

## 📚 MLOPS1 REFERENCE ANALYSIS

### Key Learnings from Reference Project

#### **1. FastAPI Application Pattern**
**Location:** `fsds/mlops1/refactor/app/main.py`

```python
✓ Simple, clean FastAPI structure
✓ Model loaded at startup (from env variable)
✓ Pydantic schemas for validation
✓ Health check endpoints
✓ Logging with loguru
✓ Data preprocessing utils
```

**Best Practices Observed:**
- Model path from environment variable
- Single responsibility (predict endpoint)
- Request/response validation
- Structured logging

#### **2. Jenkins Deployment Pattern**
**Location:** `fsds/mlops1/refactor/iac/ansible/deploy_jenkins/`

```yaml
✓ Ansible playbook for Jenkins deployment
✓ Custom Jenkins Docker image
✓ Docker-in-Docker support (privileged mode)
✓ Volume mounts for persistence
✓ Port mapping (8081:8080)
```

**Ansible Structure:**
```
ansible/
├── inventory               # IP addresses
├── deploy_jenkins/
│   ├── create_compute_instance.yaml
│   └── deploy_jenkins.yml
└── secrets/               # SSH keys
```

#### **3. CI/CD Pipeline Pattern**
**Location:** `fsds/mlops1/cicd/jenkins_tutorial/Jenkinsfile`

```groovy
✓ Test stage (Docker agent with Python)
✓ Build stage (Docker image build)
✓ Push stage (DockerHub registry)
✓ Deploy stage (placeholder)
✓ Build retention policy
✓ Timestamps enabled
```

**Advanced Pattern (Kubernetes):**
```groovy
✓ Kubernetes agent (helm container)
✓ Helm upgrade command
✓ Namespace isolation (model-serving)
```

#### **4. Helm Chart Pattern**
**Location:** `fsds/mlops1/refactor/helm-charts/hpp/`

```yaml
✓ Minimal values.yaml (image repo + tag)
✓ Always pull policy (latest updates)
✓ Templated deployments
```

#### **5. Docker Pattern**
```dockerfile
✓ Python base image
✓ WORKDIR /app
✓ Copy app + models + requirements
✓ Environment variables for config
✓ EXPOSE port for documentation
✓ CMD with uvicorn
```

---

## 🎯 IMPLEMENTATION PLAN: PHASE 3-4

### PHASE 3: APPLICATION DEVELOPMENT (Week 1-2)

#### **3.1 FastAPI Application (Priority: HIGH)**

**Tasks:**
1. **Create Application Structure**
   ```
   app/
   ├── main.py                    # FastAPI app + startup/shutdown
   ├── core/
   │   ├── config.py              # Settings (BaseSettings)
   │   ├── database.py            # PostgreSQL connection
   │   └── redis.py               # Redis connection
   ├── routers/
   │   ├── health.py              # Health check endpoints
   │   ├── predict.py             # Prediction endpoints
   │   └── models.py              # Model management endpoints
   ├── schemas/
   │   ├── prediction.py          # Request/response models
   │   └── health.py              # Health check models
   ├── services/
   │   ├── model_service.py       # MLflow model loading
   │   ├── prediction_service.py  # Prediction logic
   │   └── database_service.py    # DB operations
   └── utils/
       ├── logging.py             # Structured logging
       └── preprocessing.py       # Feature preprocessing
   ```

2. **Environment Configuration**
   ```bash
   # .env
   DATABASE_URL=postgresql://user:pass@postgres-svc:5432/app_db
   REDIS_URL=redis://redis-svc:6379/0
   MLFLOW_TRACKING_URI=http://recsys-training-mlflow:5000
   MODEL_NAME=card_approval_model
   MODEL_STAGE=Production
   GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-key.json
   LOG_LEVEL=INFO
   ```

3. **API Endpoints Design**
   ```python
   POST   /api/v1/predict           # Single prediction
   POST   /api/v1/predict/batch     # Batch predictions
   GET    /api/v1/health            # Health check
   GET    /api/v1/models            # List available models
   POST   /api/v1/models/reload     # Reload model from MLflow
   GET    /api/v1/metrics           # API metrics
   ```

4. **Database Schema (Application DB)**
   ```sql
   -- predictions table
   CREATE TABLE predictions (
       id SERIAL PRIMARY KEY,
       request_id UUID UNIQUE,
       input_data JSONB,
       prediction INTEGER,
       probability FLOAT,
       model_version VARCHAR(50),
       created_at TIMESTAMP DEFAULT NOW()
   );

   -- model_versions table
   CREATE TABLE model_versions (
       id SERIAL PRIMARY KEY,
       model_name VARCHAR(100),
       version INTEGER,
       stage VARCHAR(20),
       loaded_at TIMESTAMP,
       is_active BOOLEAN
   );
   ```

5. **Implementation Steps**
   ```bash
   # Step 1: Create core configuration
   app/core/config.py          # Pydantic Settings

   # Step 2: Setup database & Redis
   app/core/database.py        # SQLAlchemy setup
   app/core/redis.py           # Redis client

   # Step 3: Create schemas
   app/schemas/prediction.py   # Pydantic models

   # Step 4: Build services
   app/services/model_service.py      # MLflow integration
   app/services/prediction_service.py # Business logic

   # Step 5: Create routers
   app/routers/predict.py      # Prediction endpoints
   app/routers/health.py       # Health checks

   # Step 6: Main application
   app/main.py                 # FastAPI app initialization
   ```

#### **3.2 Docker & Docker Compose (Priority: HIGH)**

**Dockerfile (Production):**
```dockerfile
# Multi-stage build
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.10-slim
WORKDIR /app

# Copy dependencies
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY ./app /app
COPY ./cap_model/src /app/cap_model_src

# Create logs directory
RUN mkdir -p /app/logs

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml (Development):**
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: card-approval-api
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app
      - ./cap_model:/app/cap_model
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    container_name: app-postgres
    environment:
      POSTGRES_DB: card_approval_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: app_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    container_name: app-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # MLflow proxy (connect to K8s MLflow via port-forward)
  # kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

#### **3.3 Kubernetes Resources (Priority: MEDIUM)**

**Add to helm-charts/infrastructure/:**

1. **Redis Deployment**
   ```yaml
   # helm-charts/infrastructure/redis/
   Chart.yaml
   values.yaml
   templates/
     ├── deployment.yaml
     ├── service.yaml
     └── pvc.yaml
   ```

2. **Application PostgreSQL**
   ```yaml
   # helm-charts/infrastructure/app-postgres/
   # Separate from MLflow PostgreSQL
   ```

3. **Application Deployment**
   ```yaml
   # helm-charts/card-approval-api/
   Chart.yaml
   values.yaml
   templates/
     ├── deployment.yaml
     ├── service.yaml
     ├── ingress.yaml
     ├── configmap.yaml
     └── secrets.yaml
   ```

#### **3.4 Testing Strategy**

**Unit Tests:**
```python
# tests/test_api/
test_health.py
test_predict.py
test_model_service.py

# tests/test_services/
test_prediction_service.py
test_database_service.py
```

**Integration Tests:**
```python
# tests/integration/
test_end_to_end.py
test_database_connection.py
test_redis_connection.py
test_mlflow_integration.py
```

---

### PHASE 4: CI/CD PIPELINE (Week 3-4)

#### **4.1 Jenkins Infrastructure (Priority: HIGH)**

**Ansible Structure:**
```
ansible/
├── inventory                      # GCE instance IPs
├── group_vars/
│   └── all.yml                   # Common variables
├── playbooks/
│   ├── create_jenkins_instance.yml
│   ├── install_docker.yml
│   └── deploy_jenkins.yml
└── roles/
    ├── docker/
    └── jenkins/
```

**Step-by-Step:**

1. **Create GCE Instance (Ansible)**
   ```yaml
   # ansible/playbooks/create_jenkins_instance.yml
   ---
   - name: Create Jenkins VM on GCP
     hosts: localhost
     gather_facts: no
     tasks:
       - name: Create compute instance
         google.cloud.gcp_compute_instance:
           name: jenkins-server
           machine_type: n2-standard-2
           zone: us-east1-b
           boot_disk:
             initialize_params:
               source_image: ubuntu-2004-lts
               disk_size_gb: 50
           network_interfaces:
             - access_configs:
                 - name: External NAT
                   type: ONE_TO_ONE_NAT
           tags:
             items:
               - jenkins
               - http-server
           metadata:
             ssh-keys: "{{ ssh_public_key }}"

       - name: Create firewall rule
         google.cloud.gcp_compute_firewall:
           name: jenkins-firewall
           allowed:
             - ip_protocol: tcp
               ports: ['22', '8081']
           source_ranges: ['0.0.0.0/0']
           target_tags: ['jenkins']
   ```

2. **Install Docker (Ansible)**
   ```yaml
   # ansible/playbooks/install_docker.yml
   ---
   - name: Install Docker on Jenkins server
     hosts: jenkins
     become: yes
     tasks:
       - name: Update apt cache
         apt:
           update_cache: yes

       - name: Install prerequisites
         apt:
           pkg:
             - apt-transport-https
             - ca-certificates
             - curl
             - software-properties-common
             - python3-pip

       - name: Add Docker GPG key
         apt_key:
           url: https://download.docker.com/linux/ubuntu/gpg

       - name: Add Docker repository
         apt_repository:
           repo: deb https://download.docker.com/linux/ubuntu focal stable

       - name: Install Docker
         apt:
           name: docker-ce
           state: latest

       - name: Install Docker Compose
         pip:
           name: docker-compose
   ```

3. **Deploy Jenkins (Ansible)**
   ```yaml
   # ansible/playbooks/deploy_jenkins.yml
   ---
   - name: Deploy Jenkins with Docker
     hosts: jenkins
     become: yes
     vars:
       jenkins_image: jenkins/jenkins:lts-jdk17
       jenkins_port: 8081
     tasks:
       - name: Create Jenkins volume
         community.docker.docker_volume:
           name: jenkins_home

       - name: Run Jenkins container
         community.docker.docker_container:
           name: jenkins
           image: "{{ jenkins_image }}"
           state: started
           restart_policy: unless-stopped
           privileged: true
           user: root
           ports:
             - "{{ jenkins_port }}:8080"
             - "50000:50000"
           volumes:
             - jenkins_home:/var/jenkins_home
             - /var/run/docker.sock:/var/run/docker.sock

       - name: Wait for Jenkins to start
         wait_for:
           port: "{{ jenkins_port }}"
           delay: 10

       - name: Get initial admin password
         shell: docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
         register: jenkins_password

       - name: Display admin password
         debug:
           msg: "Jenkins initial password: {{ jenkins_password.stdout }}"
   ```

4. **Run Ansible Playbooks**
   ```bash
   # Step 1: Create GCE instance
   ansible-playbook ansible/playbooks/create_jenkins_instance.yml

   # Step 2: Update inventory with new IP
   # Edit ansible/inventory

   # Step 3: Install Docker
   ansible-playbook -i ansible/inventory ansible/playbooks/install_docker.yml

   # Step 4: Deploy Jenkins
   ansible-playbook -i ansible/inventory ansible/playbooks/deploy_jenkins.yml
   ```

#### **4.2 Jenkins Configuration (Priority: HIGH)**

**Required Plugins:**
```
1. Kubernetes Plugin
2. Docker Pipeline Plugin
3. SonarQube Scanner Plugin
4. GitHub Plugin
5. Google Cloud SDK Plugin
6. Pipeline Plugin
7. Credentials Plugin
8. Blue Ocean (optional, better UI)
```

**Credentials Setup:**
```
1. gcp-sa-key (Secret file)
   - GCP service account JSON key

2. github-pat (Secret text)
   - GitHub Personal Access Token

3. sonarqube-token (Secret text)
   - SonarQube authentication token

4. dockerhub-creds (Username/Password)
   - Docker Hub or GCR credentials

5. kubeconfig (Secret file)
   - Kubernetes config for GKE access
```

**Kubernetes Cloud Configuration:**
```
1. Add Kubernetes cloud in Jenkins
2. Kubernetes URL: https://35.x.x.x (GKE endpoint)
3. Kubernetes namespace: model-serving
4. Credentials: kubeconfig
5. Test connection
```

#### **4.3 SonarQube Deployment (Priority: MEDIUM)**

**Helm Deployment:**
```bash
# Add Helm repo
helm repo add sonarqube https://SonarSource.github.io/helm-chart-sonarqube
helm repo update

# Create namespace
kubectl create namespace sonarqube

# Deploy SonarQube
helm install sonarqube sonarqube/sonarqube \
  --namespace sonarqube \
  --set persistence.enabled=true \
  --set persistence.size=10Gi \
  --set postgresql.persistence.enabled=true \
  --set postgresql.persistence.size=10Gi

# Wait for ready
kubectl wait --namespace sonarqube \
  --for=condition=ready pod \
  --selector=app=sonarqube \
  --timeout=300s

# Port forward
kubectl port-forward -n sonarqube svc/sonarqube-sonarqube 9000:9000
```

**SonarQube Configuration:**
```
1. Access http://localhost:9000
2. Login: admin / admin
3. Change password
4. Create project: card-approval-prediction
5. Generate token
6. Configure quality gates:
   - Code coverage > 80%
   - Duplications < 3%
   - Maintainability rating = A
   - Security rating = A
```

**sonar-project.properties:**
```properties
# sonar-project.properties
sonar.projectKey=card-approval-prediction
sonar.projectName=Card Approval Prediction
sonar.projectVersion=1.0
sonar.sources=app,cap_model/src
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.version=3.10
sonar.exclusions=**/*_test.py,**/test_*.py
```

#### **4.4 Jenkinsfile (Priority: HIGH)**

**Complete Pipeline:**
```groovy
// Jenkinsfile
pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        PROJECT_ID = 'product-recsys-mlops'
        REGION = 'us-east1'
        GKE_CLUSTER = 'product-recsys-mlops-gke'
        ARTIFACT_REGISTRY = "${REGION}-docker.pkg.dev/${PROJECT_ID}/product-recsys-mlops-recsys"
        IMAGE_NAME = 'card-approval-api'
        IMAGE_TAG = "${BUILD_NUMBER}"
        NAMESPACE = 'model-serving'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            agent {
                docker {
                    image 'python:3.10-slim'
                    args '-u root:root'
                }
            }
            steps {
                echo 'Installing dependencies...'
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r app/requirements.txt
                    pip install pytest pytest-cov flake8
                '''
            }
        }

        stage('Code Quality - Linting') {
            agent {
                docker {
                    image 'python:3.10-slim'
                }
            }
            steps {
                echo 'Running linting...'
                sh '''
                    pip install flake8
                    flake8 app/ cap_model/src/ --max-line-length=120 --exclude=__pycache__,*.pyc
                '''
            }
        }

        stage('Unit Tests') {
            agent {
                docker {
                    image 'python:3.10-slim'
                }
            }
            steps {
                echo 'Running unit tests...'
                sh '''
                    pip install -r requirements.txt
                    pip install pytest pytest-cov
                    pytest tests/ --cov=app --cov-report=xml --cov-report=html
                '''
            }
            post {
                always {
                    publishHTML([
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                    junit 'test-results/*.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            when {
                branch 'PR-*'
            }
            steps {
                script {
                    withSonarQubeEnv('SonarQube') {
                        sh '''
                            sonar-scanner \
                              -Dsonar.projectKey=card-approval-prediction \
                              -Dsonar.sources=app,cap_model/src \
                              -Dsonar.python.coverage.reportPaths=coverage.xml
                        '''
                    }
                }
            }
        }

        stage('Quality Gate') {
            when {
                branch 'PR-*'
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Building Docker image: ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                    sh """
                        docker build -t ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
                        docker tag ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
                                   ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Push to Artifact Registry') {
            when {
                branch 'main'
            }
            steps {
                script {
                    withCredentials([file(credentialsId: 'gcp-sa-key', variable: 'GCP_KEY')]) {
                        sh '''
                            gcloud auth activate-service-account --key-file=${GCP_KEY}
                            gcloud config set project ${PROJECT_ID}
                            gcloud auth configure-docker ${REGION}-docker.pkg.dev

                            docker push ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                            docker push ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:latest
                        '''
                    }
                }
            }
        }

        stage('Deploy to GKE') {
            when {
                branch 'main'
            }
            agent {
                kubernetes {
                    yaml '''
                    apiVersion: v1
                    kind: Pod
                    spec:
                      containers:
                      - name: helm
                        image: alpine/helm:3.12.0
                        command: ['cat']
                        tty: true
                      - name: kubectl
                        image: bitnami/kubectl:latest
                        command: ['cat']
                        tty: true
                    '''
                }
            }
            steps {
                container('kubectl') {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh '''
                            export KUBECONFIG=${KUBECONFIG}
                            kubectl config use-context gke_${PROJECT_ID}_${REGION}_${GKE_CLUSTER}
                            kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                        '''
                    }
                }
                container('helm') {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            export KUBECONFIG=\${KUBECONFIG}
                            helm upgrade --install card-approval-api ./helm-charts/card-approval-api \
                              --namespace ${NAMESPACE} \
                              --set image.repository=${ARTIFACT_REGISTRY}/${IMAGE_NAME} \
                              --set image.tag=${IMAGE_TAG} \
                              --wait
                        """
                    }
                }
            }
        }

        stage('Verify Deployment') {
            when {
                branch 'main'
            }
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh '''
                            export KUBECONFIG=${KUBECONFIG}
                            kubectl rollout status deployment/card-approval-api -n ${NAMESPACE}
                            kubectl get pods -n ${NAMESPACE}
                            kubectl get svc -n ${NAMESPACE}
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully!'
            // Add Slack/email notification here
        }
        failure {
            echo '❌ Pipeline failed!'
            // Add Slack/email notification here
        }
        always {
            cleanWs()
        }
    }
}
```

#### **4.5 GitHub Integration (Priority: HIGH)**

**1. Create GitHub Webhook:**
```
Repository Settings → Webhooks → Add webhook
Payload URL: http://<jenkins-ip>:8081/github-webhook/
Content type: application/json
Events:
  - Pushes
  - Pull requests
```

**2. Create Multibranch Pipeline in Jenkins:**
```
1. New Item → Multibranch Pipeline
2. Branch Sources → GitHub
3. Add credentials (GitHub PAT)
4. Repository URL: https://github.com/<user>/card-approval-prediction
5. Behaviours: Discover branches + Discover PRs
6. Build Configuration: by Jenkinsfile
7. Scan triggers: Scan every 5 minutes
```

**3. Branch Protection Rules:**
```
Settings → Branches → Add rule
Branch name pattern: main
Require pull request reviews before merging: ✓
Require status checks to pass: ✓
  - Jenkins CI
  - SonarQube Quality Gate
Require branches to be up to date: ✓
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 3: Application Development

#### Week 1: FastAPI Application
- [ ] Create application structure (main.py, routers, schemas, services)
- [ ] Implement core configuration (config.py, database.py, redis.py)
- [ ] Create Pydantic schemas (prediction, health)
- [ ] Implement model service (MLflow integration)
- [ ] Implement prediction service (preprocessing + inference)
- [ ] Create health check endpoints
- [ ] Create prediction endpoints (single + batch)
- [ ] Add logging and error handling
- [ ] Write unit tests for services
- [ ] Write integration tests

#### Week 2: Docker & Kubernetes
- [ ] Update Dockerfile (multi-stage build)
- [ ] Create docker-compose.yml (app + postgres + redis)
- [ ] Update .env.example with all variables
- [ ] Test local development setup
- [ ] Create Redis Helm chart
- [ ] Create app PostgreSQL Helm chart
- [ ] Create application Helm chart
- [ ] Test Kubernetes deployments
- [ ] Configure ConfigMaps and Secrets
- [ ] Set up Ingress (optional)

### Phase 4: CI/CD Pipeline

#### Week 3: Jenkins Infrastructure
- [ ] Create Ansible directory structure
- [ ] Write create_jenkins_instance.yml playbook
- [ ] Write install_docker.yml playbook
- [ ] Write deploy_jenkins.yml playbook
- [ ] Run Ansible to create GCE instance
- [ ] Run Ansible to install Docker
- [ ] Run Ansible to deploy Jenkins
- [ ] Access Jenkins UI and complete setup
- [ ] Install required plugins
- [ ] Configure credentials (GCP, GitHub, SonarQube)
- [ ] Configure Kubernetes cloud connection
- [ ] Test Jenkins-GKE connection

#### Week 4: Pipeline & Integration
- [ ] Deploy SonarQube to Kubernetes
- [ ] Configure SonarQube (project, quality gates)
- [ ] Create Jenkinsfile with all stages
- [ ] Test Jenkinsfile syntax
- [ ] Create GitHub webhook
- [ ] Create Multibranch Pipeline job in Jenkins
- [ ] Test PR workflow (lint + test + SonarQube)
- [ ] Test main branch workflow (build + push + deploy)
- [ ] Configure branch protection rules
- [ ] Set up notifications (Slack/email)
- [ ] Write CI/CD documentation

---

## 🎯 SUCCESS CRITERIA

### Phase 3 Completion:
✅ FastAPI application running locally
✅ All endpoints working (health, predict)
✅ Docker Compose setup functional
✅ Application deployed to Kubernetes
✅ Can connect to MLflow and load models
✅ Unit tests passing (>80% coverage)

### Phase 4 Completion:
✅ Jenkins deployed and accessible
✅ SonarQube deployed and configured
✅ Pipeline triggers on PR + main branch
✅ PR checks passing (lint, test, SonarQube)
✅ Main branch auto-deploys to GKE
✅ GitHub webhook working
✅ Deployment verification successful

---

## 🚀 QUICK START GUIDE

### For Phase 3 (App Development):
```bash
# 1. Create FastAPI application structure
mkdir -p app/{core,routers,schemas,services,utils}

# 2. Implement core files
# - app/main.py
# - app/core/config.py
# - app/routers/predict.py

# 3. Update Dockerfile and docker-compose.yml

# 4. Start development environment
docker-compose up -d

# 5. Test API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"feature1": "value1"}'
```

### For Phase 4 (CI/CD):
```bash
# 1. Create Ansible structure
mkdir -p ansible/{playbooks,group_vars,roles}

# 2. Run Ansible playbooks
ansible-playbook ansible/playbooks/create_jenkins_instance.yml
ansible-playbook -i ansible/inventory ansible/playbooks/install_docker.yml
ansible-playbook -i ansible/inventory ansible/playbooks/deploy_jenkins.yml

# 3. Access Jenkins
# http://<jenkins-ip>:8081

# 4. Create Jenkinsfile in project root

# 5. Setup GitHub webhook and Multibranch Pipeline
```

---

## 📊 ESTIMATED TIMELINE

| Phase | Task | Duration | Priority |
|-------|------|----------|----------|
| **3** | FastAPI Application | 5 days | HIGH |
| **3** | Docker & Docker Compose | 2 days | HIGH |
| **3** | Kubernetes Deployments | 3 days | MEDIUM |
| **4** | Jenkins Infrastructure | 3 days | HIGH |
| **4** | SonarQube Setup | 1 day | MEDIUM |
| **4** | Jenkinsfile Creation | 2 days | HIGH |
| **4** | GitHub Integration | 1 day | HIGH |
| **4** | Testing & Documentation | 3 days | HIGH |

**Total:** ~20 working days (4 weeks)

---

## 🎓 RECOMMENDATIONS

### Architecture:
1. **Separate concerns:** App DB separate from MLflow DB
2. **Use Redis:** For caching predictions and session management
3. **Implement health checks:** Liveness + readiness probes
4. **Use Secrets:** Kubernetes Secrets for sensitive data
5. **Add monitoring:** Prometheus metrics endpoint in FastAPI

### Security:
1. **No hardcoded credentials:** Use environment variables
2. **Non-root containers:** Run as unprivileged user
3. **Secret rotation:** Regularly rotate API keys
4. **Network policies:** Restrict pod-to-pod communication
5. **RBAC:** Least privilege for service accounts

### Performance:
1. **Connection pooling:** Database and Redis
2. **Model caching:** Load model once at startup
3. **Async endpoints:** Use async/await for I/O operations
4. **Batch predictions:** Optimize for multiple predictions
5. **Request throttling:** Rate limiting with Redis

### Monitoring:
1. **Structured logging:** JSON logs with context
2. **Metrics:** Request latency, prediction time, errors
3. **Tracing:** OpenTelemetry for distributed tracing
4. **Alerts:** Set up alerts for errors and latency
5. **Dashboards:** Grafana dashboards for API metrics

---

## 📚 REFERENCE DOCUMENTATION

### Internal:
- `/cap_model/README.md` - ML model development guide
- `/cap_model/MODEL_USAGE_GUIDE.md` - Model usage and inference
- `/cap_model/STRUCTURE.md` - Project structure explained
- `/helm-charts/recsys-training/values.yaml` - Infrastructure config
- `/terraform/main.tf` - GCP infrastructure

### External (from mlops1):
- `fsds/mlops1/refactor/app/main.py` - FastAPI pattern
- `fsds/mlops1/refactor/iac/ansible/` - Ansible patterns
- `fsds/mlops1/cicd/jenkins_tutorial/Jenkinsfile` - Jenkins pipeline
- `fsds/mlops1/refactor/Jenkinsfile` - K8s deployment pattern

---

## ✅ CONCLUSION

**Current Progress:** 40% (Phase 1-2 Complete)
**Next Steps:** Phase 3 (Application) → Phase 4 (CI/CD)
**Estimated Completion:** 4 weeks
**Risk Level:** Low (well-defined requirements, reference implementation available)

**Key Success Factors:**
1. Follow reference patterns from mlops1
2. Test each component incrementally
3. Document as you build
4. Prioritize HIGH priority tasks first
5. Get feedback early and often

---

**Document Version:** 1.0
**Last Updated:** December 13, 2025
**Next Review:** Weekly during implementation
