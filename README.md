# Credit Card Approval Prediction - MLOps Project

End-to-end **MLOps pipeline** for credit card approval prediction using machine learning on **Google Cloud Platform**.

## 🏗️ Architecture

![Architecture Diagram](./img/architecture.png)

## 📑 Table of Contents

- [Credit Card Approval Prediction - MLOps Project](#credit-card-approval-prediction---mlops-project)
  - [🏗️ Architecture](#️-architecture)
  - [📑 Table of Contents](#-table-of-contents)
  - [Overview](#overview)
  - [🛠️ Tech Stack](#️-tech-stack)
  - [📁 Project Structure](#-project-structure)
  - [Quick Start](#quick-start)
    - [Prerequisites](#prerequisites)
    - [Clone \& Configure](#clone--configure)
  - [📡 API Endpoints](#-api-endpoints)
    - [Example Prediction Request](#example-prediction-request)
    - [Example Response](#example-response)
  - [Demo Video](#demo-video)
  - [📚 Documentation](#-documentation)
  - [🔮 Future Improvements](#-future-improvements)
  - [📄 License](#-license)
  - [👤 Citation](#-citation)
  - [Contact](#contact)

---

## Overview

This project is a learning-oriented MLOps playground focused on understanding the end-to-end lifecycle of machine learning model development. It includes:

- **Infrastructure as Code**: Terraform for GCP resources (GKE, GCS, Artifact Registry)
- **Kubernetes Deployment**: Helm charts for scalable, reproducible deployments
- **CI/CD Pipeline**: Jenkins with GitHub webhooks for automated builds and deployments
- **Monitoring**: Prometheus + Grafana observability stack
- **MLflow**: MLflow for experiment tracking and model versioning
- **APIs**: FastAPI service with preprocessing and real-time inference

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
│   ├── core/                   # Core configurations
│   │   ├── config.py           # Settings & environment variables
│   │   ├── logging.py          # Logging configuration
│   │   └── metrics.py          # Prometheus metrics
│   ├── routers/                # API route handlers
│   │   ├── health.py           # Health check endpoints
│   │   └── predict.py          # Prediction endpoints
│   ├── schemas/                # Pydantic models
│   │   ├── request.py          # Request validation schemas
│   │   └── response.py         # Response models
│   └── services/               # Business logic
│       ├── model_service.py    # Model loading & inference
│       └── preprocessing.py    # Feature preprocessing
│
├── training/                   # ML training pipeline
│   ├── data/                   # Data storage
│   │   ├── raw/                # Raw Kaggle dataset (gitignored)
│   │   │   ├── application_record.csv
│   │   │   └── credit_record.csv
│   │   └── processed/          # Processed features + artifacts
│   │       ├── X_train.csv, X_test.csv
│   │       ├── y_train.csv, y_test.csv
│   │       ├── scaler.pkl      # StandardScaler
│   │       ├── pca.pkl         # PCA transformer
│   │       └── feature_names.json
│   ├── scripts/                # Training automation
│   │   ├── download_data.py    # Download from Kaggle
│   │   ├── run_preprocessing.py # Feature engineering
│   │   └── run_training.py     # Train & register models
│   └── src/                    # Training source code
│       ├── data/               # Data loading
│       │   └── data_loader.py
│       ├── features/           # Feature engineering
│       │   └── feature_engineering.py
│       ├── models/             # Model training
│       │   ├── train.py        # Training orchestration
│       │   └── evaluate.py     # Model evaluation
│       └── utils/              # Utilities
│           └── model_configs.py # Model hyperparameters
│
├── scripts/                    # CI/CD helper scripts
│   ├── evaluate_model.py       # Model quality gate (F1 threshold)
│   └── download_model.py       # Download from MLflow registry
│
├── helm-charts/                # Kubernetes deployments
│   ├── card-approval/          # API stack
│   │   ├── Chart.yaml
│   │   ├── values.yaml         # API configuration
│   │   └── templates/          # K8s manifests
│   ├── card-approval-training/ # MLflow training stack
│   │   ├── Chart.yaml
│   │   ├── values.yaml         # MLflow configuration
│   │   └── templates/
│   └── infrastructure/         # Base charts
│       ├── postgres/           # PostgreSQL chart
│       ├── mlflow/             # MLflow server chart
│       └── redis/              # Redis cache chart
│
├── terraform/                  # GCP infrastructure as code
│   ├── main.tf                 # Main configuration
│   │   # - GKE cluster
│   │   # - GCS bucket for MLflow artifacts
│   │   # - Artifact Registry for Docker images
│   │   # - Service accounts & IAM roles
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Resource outputs
│   ├── terraform.tfvars.example # Configuration template
│   └── provider.tf             # GCP provider setup
│
├── ansible/                    # Jenkins deployment automation
│   ├── playbooks/              # Ansible playbooks
│   │   ├── deploy_jenkins.yml  # Deploy Jenkins to VM
│   │   └── configure_jenkins.yml # Configure Jenkins
│   ├── inventory/              # Host configurations
│   │   └── hosts.ini
│   └── group_vars/             # Group variables
│
├── docs/                       # Project documentation
│   ├── index.md                # Documentation index
│   ├── 00_Setup_Guide.md       # Setup & configuration reference
│   ├── 01_Helm_Deployment.md   # Kubernetes deployment guide
│   ├── 02_MLflow_Training.md   # Model training guide
│   ├── 03_CICD_Pipeline.md     # Jenkins CI/CD setup
│   └── 04_NGINX.md             # NGINX Ingress configuration
│
├── .github/                    # GitHub configuration
│   └── workflows/              # GitHub Actions (optional)
│
├── Dockerfile                  # API container image
├── Jenkinsfile                 # CI/CD pipeline definition
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
├── config.env.example          # Configuration template
├── sonar-project.properties    # SonarQube configuration
├── .gitignore                  # Git ignore patterns
├── .pre-commit-config.yaml     # Pre-commit hooks (Black, isort, Flake8)
└── README.md                   # This file
```

---

##   Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- GCP account with billing enabled
- Terraform >= 1.6.0
- kubectl & Helm 3

### Clone & Configure

```bash
# Clone the repository
git clone https://github.com/thanhphat-19/card-approval-prediction.git
cd card-approval-prediction

# Configure environment
cp config.env.example config.env
# Edit config.env: Set GCP_PROJECT_ID, passwords, service accounts

# Configure Terraform
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars: Set project_id
```

> 📖 **Full setup guide**: See [docs/00_Setup_Guide.md](docs/00_Setup_Guide.md) for complete setup and configuration reference




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

## Demo Video

[▶ Watch the demo video on Google Drive](https://drive.google.com/drive/folders/1ZjPjfBKeP1AoTEvL-5GgAoK9CSbr1KBx?usp=sharing)



## 📚 Documentation

| Document | Description |
|----------|-------------|
| [📖 Documentation Index](docs/index.md) | Complete documentation overview |
| [00_Setup_Guide.md](docs/00_Setup_Guide.md) | ⚙️ **Start here!** - Setup & configuration |
| [01_Helm_Deployment.md](docs/01_Helm_Deployment.md) | Deploy MLflow, API, and monitoring |
| [02_MLflow_Training.md](docs/02_MLflow_Training.md) | Train and register models |
| [03_CICD_Pipeline.md](docs/03_CICD_Pipeline.md) | Jenkins CI/CD pipeline setup |
| [04_NGINX.md](docs/04_NGINX.md) | NGINX Ingress configuration |

---

## 🔮 Future Improvements

- [ ] **KServe**: Serverless model inference with autoscaling
- [ ] **Knative Eventing**: Event-driven model retraining
- [ ] **Data Pipeline**: Automated data ingestion and preprocessing
- [ ] **Unit Tests in CI/CD**: Integrate Unit Test to CI/CD pipeline
- [ ] **A/B Testing**: Canary deployments for model versions
- [ ] **Feature Store**: Centralized feature management

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Citation

If you use Card Approval Prediction in your research, please cite it as follows:
```
@software{CardApprovalPrediction2025,
  author = {Thanh Phat},
  title = {Card Approval Prediction: End-to-end MLOps pipeline for credit card approval prediction using machine learning on Google Cloud Platform.},
  year = {2025},
  url = {https://github.com/thanhphat-19/card-approval-prediction}
}
```

## Contact

For questions, issues, or collaborations, please open an issue or contact thanhphat352@gmail.com
