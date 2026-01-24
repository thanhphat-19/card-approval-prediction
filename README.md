# Credit Card Approval Prediction - MLOps Project

End-to-end **MLOps pipeline** for credit card approval prediction using machine learning on **Google Cloud Platform**.

## 🏗️ Architecture

![Architecture Diagram](./docs/architecture-diagram.jpg)

## 📑 Table of Contents

- [Credit Card Approval Prediction - MLOps Project](#credit-card-approval-prediction---mlops-project)
  - [🏗️ Architecture](#️-architecture)
  - [📑 Table of Contents](#-table-of-contents)
  - [Overview](#overview)
  - [🛠️ Tech Stack](#️-tech-stack)
  - [📁 Project Structure](#-project-structure)
  - [🚀 Quick Start](#-quick-start)
    - [Prerequisites](#prerequisites)
    - [Clone \& Configure](#clone--configure)
  - [📡 API Endpoints](#-api-endpoints)
    - [Example Prediction Request](#example-prediction-request)
    - [Example Response](#example-response)
  - [📚 Documentation](#-documentation)
  - [🔮 Future Improvements](#-future-improvements)
  - [📄 License](#-license)
  - [👤 Author](#-author)

---

## Overview

This project demonstrates a complete MLOps workflow for a **credit card approval prediction** system, from model training to deployment. It includes:

- **ML Training Pipeline**: Automated model training with multiple algorithms (XGBoost, LightGBM, CatBoost)
- **Model Registry**: MLflow for experiment tracking and model versioning
- **APIs**: FastAPI service with preprocessing and real-time inference
- **Infrastructure as Code**: Terraform for GCP resources (GKE, GCS, Artifact Registry)
- **Kubernetes Deployment**: Helm charts for scalable, reproducible deployments
- **CI/CD Pipeline**: Jenkins with GitHub webhooks for automated builds and deployments
- **Monitoring**: Prometheus + Grafana observability stack

---


## 🛠️ Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Cloud & Infrastructure** | GCP, Terraform, GKE, GCS, Artifact Registry |
| **Container & Orchestration** | Docker, Kubernetes, Helm |
| **CI/CD & Configuration** | Jenkins, Ansible, GitHub Webhooks, SonarQube |
| **Application** | FastAPI, Python 3.11, Pydantic, Uvicorn |
| **Data Storage** | PostgreSQL, Redis (caching) |
| **ML & Data Science** | scikit-learn, XGBoost, LightGBM, CatBoost, pandas, numpy |
| **ML Operations** | MLflow (tracking & registry), Google Cloud Storage (artifacts) |
| **Monitoring** | Prometheus, Grafana, kube-prometheus-stack |
| **Code Quality** | Black, isort, Flake8, Pylint, pre-commit |

---

## 📁 Project Structure

```
card-approval-prediction/
├── app/                        # FastAPI application
│   ├── main.py                 # Application entrypoint
│   ├── core/                   # Config, logging, metrics
│   ├── routers/                # API routes (health, predict)
│   ├── schemas/                # Pydantic models (request/response)
│   └── services/               # Business logic (model, preprocessing)
│
├── cap_model/                  # ML training pipeline
│   ├── data/                   # Raw and processed datasets
│   ├── notebooks/              # EDA and experimentation
│   ├── scripts/                # Training automation scripts
│   ├── src/                    # Training source code
│   │   ├── data/               # Data loading
│   │   ├── features/           # Feature engineering
│   │   ├── models/             # Model training & evaluation
│   │   └── utils/              # Utilities
│   └── models/                 # Saved model artifacts
│
├── helm-charts/                # Kubernetes deployments
│   ├── card-approval/          # API stack (API + Postgres + Redis)
│   ├── card-approval-training/ # MLflow + Postgres for training
│   └── infrastructure/         # Shared components
│       ├── card-approval-api/
│       ├── card-approval-monitoring/
│       ├── mlflow/
│       ├── postgres/
│       ├── redis/
│       └── nginx-ingress/
│
├── terraform/                  # GCP infrastructure as code
│   ├── main.tf                 # GKE, GCS, Artifact Registry, IAM
│   ├── variables.tf            # Input variables
│   └── outputs.tf              # Resource outputs
│
├── ansible/                    # Configuration management
│   └── playbooks/              # Jenkins VM setup
│
├── tests/                      # Test suites
│   ├── test_api.py
│   ├── test_health.py
│   └── test_predict.py
│
├── docs/                       # Documentation (MkDocs)
│   ├── 00_Setup_Guide.md       # Getting started
│   ├── 01_Terraform.md         # Infrastructure setup
│   ├── 03_Helm_Deployment.md   # Kubernetes deployment
│   ├── 04_MLflow_Training.md   # ML training guide
│   ├── 05_API_Service.md       # API reference
│   ├── 06_CICD_Pipeline.md     # CI/CD setup
│   └── 07_Monitoring.md        # Observability
│
├── Dockerfile                  # API container image
├── Jenkinsfile                 # CI/CD pipeline definition
├── docker-compose.yml          # Local development services
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
├── mkdocs.yml                  # Documentation configuration
├── config.example.env          # Configuration template
└── sonar-project.properties    # SonarQube configuration
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- GCP account with billing enabled
- Terraform >= 1.6.0
- kubectl & Helm 3

### Clone & Configure

```bash
# Clone the repository
git clone https://github.com/yourusername/card-approval-prediction.git
cd card-approval-prediction

# Configure environment
cp config.example.env config.env
# Edit config.env with your GCP project ID and passwords

# Configure Terraform
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your project settings
```

> 📖 **Full setup guide**: See [docs/00_Setup_Guide.md](docs/00_Setup_Guide.md)




## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info and status |
| `GET` | `/docs` | Swagger UI documentation |
| `GET` | `/health` | Health check |
| `GET` | `/health/ready` | Readiness probe |
| `GET` | `/health/live` | Liveness probe |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/api/v1/predict` | Credit approval prediction |
| `POST` | `/api/v1/reload-model` | Reload model from MLflow |
| `GET` | `/api/v1/model-info` | Current model information |

### Example Prediction Request

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
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
```

### Example Response

```json
{
  "prediction": 1,
  "probability": 1.0,
  "decision": "APPROVED",
  "confidence": 1.0,
  "version": "1",
  "timestamp": "2025-01-24T15:47:00"
}
```

---


## 📚 Documentation

View the full documentation with MkDocs:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
# Open http://localhost:8000
```

| Document | Description |
|----------|-------------|
| [00_Setup_Guide.md](docs/00_Setup_Guide.md) | ⚙️ **Start here!** - Complete setup guide |
| [01_Terraform.md](docs/01_Terraform.md) | Infrastructure provisioning |
| [02_terraform_architecture.md](docs/02_terraform_architecture.md) | Architecture design decisions |
| [03_Helm_Deployment.md](docs/03_Helm_Deployment.md) | Kubernetes deployment guide |
| [04_MLflow_Training.md](docs/04_MLflow_Training.md) | Model training pipeline |
| [05_API_Service.md](docs/05_API_Service.md) | API service reference |
| [06_CICD_Pipeline.md](docs/06_CICD_Pipeline.md) | Jenkins CI/CD setup |
| [07_Monitoring.md](docs/07_Monitoring.md) | Observability & alerting |

---

## 🔮 Future Improvements

- [ ] **KServe**: Serverless model inference with autoscaling
- [ ] **Knative Eventing**: Event-driven model retraining
- [ ] **Data Pipeline**: Automated data ingestion and preprocessing
- [ ] **Unit Tests in CI/CD**: Automated testing in Jenkins pipeline
- [ ] **A/B Testing**: Canary deployments for model versions
- [ ] **Feature Store**: Centralized feature management

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Thanh Phat** - [GitHub](https://github.com/thanhphat-19)
