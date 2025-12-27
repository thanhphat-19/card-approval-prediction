# Next Steps: Implementation Guide

**Start Date:** Week of December 16, 2025
**Duration:** 4 weeks
**Current Status:** Ready to begin Phase 3

---

## 🎯 IMMEDIATE PRIORITIES

### This Week (Week 1): FastAPI Application Foundation

**Goal:** Get a working FastAPI application that can serve predictions from MLflow models.

#### Day 1-2: Project Setup & Core Configuration

**1. Create requirements.txt for the app**
```bash
# Location: /app/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
mlflow==2.9.2
python-multipart==0.0.6
loguru==0.7.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
joblib==1.3.2
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
```

**2. Create application structure**
```bash
cd /home/thanhphat/workspace/card-approval-prediction/app

# Create directories
mkdir -p core routers schemas services utils

# Create __init__.py files
touch __init__.py
touch core/__init__.py
touch routers/__init__.py
touch schemas/__init__.py
touch services/__init__.py
touch utils/__init__.py
```

**3. Create .env file**
```bash
# Location: /app/.env
DATABASE_URL=postgresql://app_user:app_password@localhost:5432/card_approval_db
REDIS_URL=redis://localhost:6379/0
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
MODEL_NAME=card_approval_model
MODEL_STAGE=Production
LOG_LEVEL=INFO
APP_NAME=Card Approval API
APP_VERSION=1.0.0
```

#### Day 3: Core Application Files

**File 1: app/core/config.py**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Card Approval API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # MLflow
    MLFLOW_TRACKING_URI: str
    MODEL_NAME: str = "card_approval_model"
    MODEL_STAGE: str = "Production"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**File 2: app/core/database.py**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**File 3: app/core/redis_client.py**
```python
import redis
from app.core.config import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

def get_redis():
    return redis_client
```

#### Day 4: Schemas and Services

**File 4: app/schemas/prediction.py**
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PredictionInput(BaseModel):
    ID: int
    CODE_GENDER: str
    FLAG_OWN_CAR: str
    FLAG_OWN_REALTY: str
    CNT_CHILDREN: int
    AMT_INCOME_TOTAL: float
    NAME_INCOME_TYPE: str
    NAME_EDUCATION_TYPE: str
    NAME_FAMILY_STATUS: str
    NAME_HOUSING_TYPE: str
    DAYS_BIRTH: int
    DAYS_EMPLOYED: int
    FLAG_MOBIL: int
    FLAG_WORK_PHONE: int
    FLAG_PHONE: int
    FLAG_EMAIL: int
    OCCUPATION_TYPE: str
    CNT_FAM_MEMBERS: float

    class Config:
        json_schema_extra = {
            "example": {
                "ID": 5008804,
                "CODE_GENDER": "M",
                "FLAG_OWN_CAR": "Y",
                "FLAG_OWN_REALTY": "Y",
                "CNT_CHILDREN": 0,
                "AMT_INCOME_TOTAL": 180000.0,
                "NAME_INCOME_TYPE": "Working",
                "NAME_EDUCATION_TYPE": "Higher education",
                "NAME_FAMILY_STATUS": "Married",
                "NAME_HOUSING_TYPE": "House / apartment",
                "DAYS_BIRTH": -14000,
                "DAYS_EMPLOYED": -2500,
                "FLAG_MOBIL": 1,
                "FLAG_WORK_PHONE": 0,
                "FLAG_PHONE": 1,
                "FLAG_EMAIL": 0,
                "OCCUPATION_TYPE": "Managers",
                "CNT_FAM_MEMBERS": 2.0
            }
        }

class PredictionOutput(BaseModel):
    prediction: int = Field(..., description="0=Rejected, 1=Approved")
    probability: float = Field(..., description="Probability of approval")
    decision: str = Field(..., description="Approved or Rejected")
    confidence: float = Field(..., description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str
    version: str
    mlflow_connected: bool
    database_connected: bool
    redis_connected: bool
```

**File 5: app/services/model_service.py**
```python
import mlflow
from loguru import logger
from app.core.config import get_settings

class ModelService:
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.model_version = None
        self._load_model()

    def _load_model(self):
        """Load model from MLflow registry"""
        try:
            mlflow.set_tracking_uri(self.settings.MLFLOW_TRACKING_URI)
            model_uri = f"models:/{self.settings.MODEL_NAME}/{self.settings.MODEL_STAGE}"
            logger.info(f"Loading model from: {model_uri}")

            self.model = mlflow.pyfunc.load_model(model_uri)

            # Get model version info
            client = mlflow.tracking.MlflowClient()
            model_versions = client.get_latest_versions(
                self.settings.MODEL_NAME,
                stages=[self.settings.MODEL_STAGE]
            )
            if model_versions:
                self.model_version = model_versions[0].version

            logger.info(f"✓ Model loaded: {self.settings.MODEL_NAME} v{self.model_version}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def predict(self, features):
        """Make prediction"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        prediction = self.model.predict(features)
        return prediction

    def reload_model(self):
        """Reload model from MLflow"""
        logger.info("Reloading model...")
        self._load_model()

# Global instance
model_service = ModelService()
```

**File 6: app/services/prediction_service.py**
```python
import pandas as pd
from app.services.model_service import model_service
from app.schemas.prediction import PredictionInput, PredictionOutput
from loguru import logger

class PredictionService:
    def __init__(self):
        self.model_service = model_service

    def predict_single(self, input_data: PredictionInput) -> PredictionOutput:
        """Make single prediction"""
        try:
            # Convert input to DataFrame
            df = pd.DataFrame([input_data.model_dump()])

            # Get prediction
            prediction = self.model_service.predict(df)[0]

            # Get probability if available
            try:
                proba = self.model_service.model.predict_proba(df)[0]
                probability = float(proba[1])  # Probability of class 1 (Approved)
            except:
                probability = 1.0 if prediction == 1 else 0.0

            # Create response
            decision = "Approved" if prediction == 1 else "Rejected"
            confidence = max(probability, 1 - probability)

            return PredictionOutput(
                prediction=int(prediction),
                probability=probability,
                decision=decision,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

prediction_service = PredictionService()
```

#### Day 5: API Routes

**File 7: app/routers/health.py**
```python
from fastapi import APIRouter, Depends
from app.schemas.prediction import HealthResponse
from app.core.config import get_settings
from app.core.database import engine
from app.core.redis_client import get_redis
from app.services.model_service import model_service
import mlflow

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    settings = get_settings()

    # Check MLflow
    mlflow_connected = False
    try:
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.search_experiments()
        mlflow_connected = True
    except:
        pass

    # Check database
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_connected = True
    except:
        pass

    # Check Redis
    redis_connected = False
    try:
        redis_client = get_redis()
        redis_client.ping()
        redis_connected = True
    except:
        pass

    status = "healthy" if all([mlflow_connected, db_connected, redis_connected]) else "degraded"

    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        mlflow_connected=mlflow_connected,
        database_connected=db_connected,
        redis_connected=redis_connected
    )
```

**File 8: app/routers/predict.py**
```python
from fastapi import APIRouter, HTTPException
from app.schemas.prediction import PredictionInput, PredictionOutput
from app.services.prediction_service import prediction_service
from loguru import logger

router = APIRouter(prefix="/api/v1", tags=["Predictions"])

@router.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    """
    Make a credit card approval prediction

    Returns:
    - prediction: 0 (Rejected) or 1 (Approved)
    - probability: Probability of approval
    - decision: Human-readable decision
    - confidence: Model confidence
    """
    try:
        result = prediction_service.predict_single(input_data)
        logger.info(f"Prediction made: {result.decision}")
        return result
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload-model")
async def reload_model():
    """Reload model from MLflow registry"""
    try:
        from app.services.model_service import model_service
        model_service.reload_model()
        return {"status": "success", "message": "Model reloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**File 9: app/main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import get_settings
from app.routers import health, predict

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="INFO")

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Credit Card Approval Prediction API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(predict.router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"MLflow URI: {settings.MLFLOW_TRACKING_URI}")
    logger.info(f"Model: {settings.MODEL_NAME} ({settings.MODEL_STAGE})")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### Week 2: Docker & Testing

#### Day 6-7: Docker Configuration

**File 10: /Dockerfile (Update)**
```dockerfile
# Multi-stage build for smaller image
FROM python:3.10-slim as builder

WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY ./app /app
COPY ./cap_model/src /app/cap_model_src

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File 11: /docker-compose.yml (Update)**
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: card-approval-api
    env_file:
      - ./app/.env
    environment:
      - DATABASE_URL=postgresql://app_user:app_password@postgres:5432/card_approval_db
      - REDIS_URL=redis://redis:6379/0
      - MLFLOW_TRACKING_URI=http://host.docker.internal:5000
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app
      - ./app/logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
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
      - "5433:5432"  # Different port to avoid conflict with K8s port-forward
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d card_approval_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    container_name: app-redis
    ports:
      - "6380:6379"  # Different port
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

#### Day 8-9: Testing

**File 12: tests/test_api.py**
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_predict():
    payload = {
        "ID": 5008804,
        "CODE_GENDER": "M",
        "FLAG_OWN_CAR": "Y",
        "FLAG_OWN_REALTY": "Y",
        "CNT_CHILDREN": 0,
        "AMT_INCOME_TOTAL": 180000.0,
        "NAME_INCOME_TYPE": "Working",
        "NAME_EDUCATION_TYPE": "Higher education",
        "NAME_FAMILY_STATUS": "Married",
        "NAME_HOUSING_TYPE": "House / apartment",
        "DAYS_BIRTH": -14000,
        "DAYS_EMPLOYED": -2500,
        "FLAG_MOBIL": 1,
        "FLAG_WORK_PHONE": 0,
        "FLAG_PHONE": 1,
        "FLAG_EMAIL": 0,
        "OCCUPATION_TYPE": "Managers",
        "CNT_FAM_MEMBERS": 2.0
    }

    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "decision" in data
    assert data["prediction"] in [0, 1]
```

#### Day 10: Local Testing

**Testing Commands:**
```bash
# 1. Start MLflow (if not already running in K8s)
kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000

# 2. Build and start services
docker-compose up --build -d

# 3. Check logs
docker-compose logs -f app

# 4. Test health endpoint
curl http://localhost:8000/health

# 5. Test prediction endpoint
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008804,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 180000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -14000,
    "DAYS_EMPLOYED": -2500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2.0
  }'

# 6. Run tests
docker-compose exec app pytest tests/ -v

# 7. Access docs
# Open http://localhost:8000/docs
```

---

### Week 3: CI/CD Infrastructure

#### Day 11-12: Ansible Setup

**Directory structure:**
```bash
mkdir -p ansible/{playbooks,group_vars,inventory}
```

**File 13: ansible/inventory/hosts**
```ini
[jenkins]
# Will be updated after GCE instance creation

[jenkins:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/gcp-key
```

**File 14: ansible/playbooks/01_create_jenkins_vm.yml**
```yaml
---
- name: Create Jenkins GCE Instance
  hosts: localhost
  gather_facts: no
  vars:
    project_id: product-recsys-mlops
    zone: us-east1-b
    machine_type: n2-standard-2
    image_project: ubuntu-os-cloud
    image_family: ubuntu-2004-lts

  tasks:
    - name: Create firewall rule for Jenkins
      command: >
        gcloud compute firewall-rules create jenkins-firewall
        --allow tcp:22,tcp:8081
        --source-ranges 0.0.0.0/0
        --target-tags jenkins
        --project {{ project_id }}
      ignore_errors: yes

    - name: Create GCE instance
      command: >
        gcloud compute instances create jenkins-server
        --project={{ project_id }}
        --zone={{ zone }}
        --machine-type={{ machine_type }}
        --image-project={{ image_project }}
        --image-family={{ image_family }}
        --boot-disk-size=50GB
        --tags=jenkins,http-server
        --metadata=enable-oslogin=TRUE
      register: instance_output

    - name: Get external IP
      command: >
        gcloud compute instances describe jenkins-server
        --zone={{ zone }}
        --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
      register: external_ip

    - name: Display instance info
      debug:
        msg: "Jenkins server created at: {{ external_ip.stdout }}"

    - name: Update inventory
      lineinfile:
        path: ansible/inventory/hosts
        regexp: '^# Will be updated'
        line: "{{ external_ip.stdout }}"
```

**File 15: ansible/playbooks/02_install_docker.yml**
```yaml
---
- name: Install Docker
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
        state: present

    - name: Add Docker GPG key
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present

    - name: Add Docker repository
      apt_repository:
        repo: deb https://download.docker.com/linux/ubuntu focal stable
        state: present

    - name: Install Docker CE
      apt:
        name: docker-ce
        state: latest
        update_cache: yes

    - name: Install Docker Compose
      get_url:
        url: https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64
        dest: /usr/local/bin/docker-compose
        mode: '0755'

    - name: Start Docker service
      systemd:
        name: docker
        state: started
        enabled: yes
```

**File 16: ansible/playbooks/03_deploy_jenkins.yml**
```yaml
---
- name: Deploy Jenkins
  hosts: jenkins
  become: yes
  vars:
    jenkins_image: jenkins/jenkins:lts-jdk17
    jenkins_container_name: jenkins
    jenkins_port: 8081

  tasks:
    - name: Create Jenkins home directory
      file:
        path: /var/jenkins_home
        state: directory
        owner: 1000
        group: 1000
        mode: '0755'

    - name: Pull Jenkins image
      command: docker pull {{ jenkins_image }}

    - name: Stop existing Jenkins container
      command: docker stop {{ jenkins_container_name }}
      ignore_errors: yes

    - name: Remove existing Jenkins container
      command: docker rm {{ jenkins_container_name }}
      ignore_errors: yes

    - name: Run Jenkins container
      command: >
        docker run -d
        --name {{ jenkins_container_name }}
        --restart unless-stopped
        --privileged
        -u root
        -p {{ jenkins_port }}:8080
        -p 50000:50000
        -v /var/jenkins_home:/var/jenkins_home
        -v /var/run/docker.sock:/var/run/docker.sock
        {{ jenkins_image }}

    - name: Wait for Jenkins to start
      wait_for:
        port: "{{ jenkins_port }}"
        delay: 30
        timeout: 300

    - name: Get initial admin password
      shell: docker exec {{ jenkins_container_name }} cat /var/jenkins_home/secrets/initialAdminPassword
      register: admin_password
      retries: 5
      delay: 10
      until: admin_password.rc == 0

    - name: Display Jenkins URL and password
      debug:
        msg:
          - "Jenkins is ready!"
          - "URL: http://{{ ansible_host }}:{{ jenkins_port }}"
          - "Initial admin password: {{ admin_password.stdout }}"
```

#### Day 13-14: Run Ansible & Configure Jenkins

**Commands:**
```bash
# 1. Run Ansible playbooks
cd ansible
ansible-playbook playbooks/01_create_jenkins_vm.yml
ansible-playbook -i inventory/hosts playbooks/02_install_docker.yml
ansible-playbook -i inventory/hosts playbooks/03_deploy_jenkins.yml

# 2. Access Jenkins
# URL from output: http://<external-ip>:8081

# 3. Complete Jenkins setup wizard
# - Install suggested plugins
# - Create admin user

# 4. Install additional plugins
# - Kubernetes
# - Docker Pipeline
# - Google Cloud SDK
# - Blue Ocean (optional)

# 5. Configure credentials
# - Add GCP service account key
# - Add GitHub PAT
# - Add kubeconfig
```

#### Day 15: Jenkinsfile Creation

**File 17: /Jenkinsfile**
```groovy
pipeline {
    agent any

    environment {
        PROJECT_ID = 'product-recsys-mlops'
        REGION = 'us-east1'
        ARTIFACT_REGISTRY = "${REGION}-docker.pkg.dev/${PROJECT_ID}/product-recsys-mlops-recsys"
        IMAGE_NAME = 'card-approval-api'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            agent {
                docker {
                    image 'python:3.10-slim'
                    args '-u root:root'
                }
            }
            steps {
                sh '''
                    pip install -r app/requirements.txt
                    pip install pytest pytest-cov
                    pytest tests/ --cov=app --cov-report=xml
                '''
            }
        }

        stage('Build') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh """
                        docker build -t ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
                        docker tag ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
                                   ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([file(credentialsId: 'gcp-sa-key', variable: 'GCP_KEY')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=${GCP_KEY}
                        gcloud auth configure-docker ${REGION}-docker.pkg.dev
                        docker push ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${ARTIFACT_REGISTRY}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

---

### Week 4: Integration & Testing

#### Day 16-18: GitHub Integration

**Tasks:**
1. Create GitHub repository webhook
2. Create Multibranch Pipeline in Jenkins
3. Test PR workflow
4. Test main branch deployment

#### Day 19-20: Documentation & Cleanup

**Tasks:**
1. Update README with new features
2. Document API endpoints
3. Create deployment guide
4. Test end-to-end workflow

---

## 📝 DAILY CHECKLIST

### Week 1
- [ ] Day 1: Create app structure and requirements
- [ ] Day 2: Implement core config files
- [ ] Day 3: Create schemas and model service
- [ ] Day 4: Implement prediction service
- [ ] Day 5: Create API routes and main.py
- [ ] **Milestone:** FastAPI app running locally

### Week 2
- [ ] Day 6: Update Dockerfile
- [ ] Day 7: Update docker-compose.yml
- [ ] Day 8: Write unit tests
- [ ] Day 9: Test with docker-compose
- [ ] Day 10: Integration testing
- [ ] **Milestone:** Containerized app working

### Week 3
- [ ] Day 11: Create Ansible structure
- [ ] Day 12: Write Ansible playbooks
- [ ] Day 13: Deploy Jenkins with Ansible
- [ ] Day 14: Configure Jenkins plugins & credentials
- [ ] Day 15: Create Jenkinsfile
- [ ] **Milestone:** Jenkins running with pipeline

### Week 4
- [ ] Day 16: Setup GitHub webhook
- [ ] Day 17: Create Multibranch Pipeline
- [ ] Day 18: Test CI/CD workflow
- [ ] Day 19: Documentation
- [ ] Day 20: Final testing & review
- [ ] **Milestone:** Full CI/CD operational

---

## 🎯 SUCCESS METRICS

**Phase 3 Complete:**
- ✅ API responds to health checks
- ✅ Predictions working locally
- ✅ Docker Compose runs all services
- ✅ Tests passing (>80% coverage)

**Phase 4 Complete:**
- ✅ Jenkins deployed on GCP
- ✅ Pipeline triggers automatically
- ✅ Docker images pushed to Artifact Registry
- ✅ GitHub integration working
- ✅ Full workflow tested

---

## 🚨 TROUBLESHOOTING

### Common Issues

**1. MLflow model not loading**
```bash
# Check MLflow is accessible
kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000

# Test connection
curl http://localhost:5000/health

# Check model exists
python -c "import mlflow; mlflow.set_tracking_uri('http://localhost:5000'); print(mlflow.search_registered_models())"
```

**2. Docker build fails**
```bash
# Check Dockerfile syntax
docker build -t test .

# Build with no cache
docker build --no-cache -t test .
```

**3. Database connection fails**
```bash
# Check PostgreSQL running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U app_user -d card_approval_db
```

**4. Ansible fails**
```bash
# Test connection
ansible -i inventory/hosts jenkins -m ping

# Run with verbose
ansible-playbook -vvv playbooks/deploy_jenkins.yml
```

---

## 📞 NEXT STEPS AFTER COMPLETION

1. **Deploy to Kubernetes**
   - Create Helm chart for the app
   - Deploy to GKE
   - Configure Ingress

2. **Add Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Alerting rules

3. **Enhance Security**
   - Add authentication
   - Use Kubernetes Secrets
   - Implement RBAC

4. **Optimize Performance**
   - Add caching with Redis
   - Implement connection pooling
   - Add load balancing

---

**Ready to start? Begin with Week 1, Day 1! 🚀**
