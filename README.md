# Credit Card Approval Prediction - MLOps Project

End-to-end MLOps pipeline for a **Credit Card Approval** prediction system.


### 🏗️ Architecture

This project implements:
- **Infrastructure**: GCP (GKE, GCS, Artifact Registry) with Terraform
- **CI/CD**: Jenkins + SonarQube
- **ML Tracking**: MLflow for experiment tracking and model registry
- **API**: FastAPI with PostgreSQL and Redis
- **Deployment**: Kubernetes with Helm charts
- **Monitoring**: Prometheus + Grafana

### 📋 Tech Stack

**Infrastructure & Cloud**
- GCP, Terraform, Kubernetes, Helm

**CI/CD & Quality**
- Jenkins, Ansible, SonarQube, GitHub Webhooks

**Application**
- FastAPI, SQLAlchemy, PostgreSQL, Redis, MLflow

**ML & Data**
- scikit-learn, pandas, numpy, XGBoost, classification models

**Monitoring**
- Prometheus, Grafana, kube-prometheus-stack

---

## 🚀 Quick Start

### Prerequisites

- GCP Account with billing enabled
- `gcloud`, `kubectl`, `helm`, `terraform` installed
- Python 3.10+

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/card-approval-prediction.git
cd card-approval-prediction

# 2. Configure your environment
cp config.example.env config.env
# Edit config.env with your GCP project ID and passwords

# 3. Configure Terraform
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your project_id

# 4. Deploy infrastructure
cd terraform && terraform init && terraform apply

# 5. Deploy applications (see docs/00_Setup_Guide.md for full instructions)
```

### Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### View Documentation

```bash
mkdocs serve
```

> 📖 **Full setup instructions**: See [docs/00_Setup_Guide.md](docs/00_Setup_Guide.md)

---

## 📁 Project Structure

```
card-approval-prediction/
├── app/                        # FastAPI application
├── cap_model/                  # ML training pipeline
├── helm-charts/                # Kubernetes deployments
│   ├── card-approval/          # API stack (API + Postgres + Redis)
│   ├── card-approval-training/ # MLflow + Postgres
│   └── infrastructure/         # Monitoring, Postgres, MLflow, nginx-ingress
├── terraform/                  # GCP infrastructure (GKE, GCS, Artifact Registry)
├── scripts/                    # Operational scripts (scale up/down, etc.)
├── ansible/                    # Jenkins/infra configuration
├── tests/                      # Test suites
├── docs/                       # Project documentation
│   ├── 00_Setup_Guide.md       # ⚙️ Start here!
│   ├── 01_Terraform.md
│   ├── ...
│   └── index.md
├── config.example.env          # Configuration template (copy to config.env)
├── Jenkinsfile                 # CI/CD pipeline
├── docker-compose.yml          # Optional local services
├── Dockerfile                  # API image
└── requirements.txt            # Python dependencies
```

---

## 🎯 Project Goals

This project demonstrates:
- ✅ **MLOps Best Practices**: End-to-end automation
- ✅ **Infrastructure as Code**: Reproducible environments
- ✅ **CI/CD**: Automated testing and deployment
- ✅ **ML Tracking**: Experiment management with MLflow
- ✅ **Scalable Deployment**: Kubernetes orchestration
- ✅ **Monitoring**: Full observability stack
- ✅ **Production Ready**: Real-world patterns and practices

---



## Improvements
- [] Kserve
- [] Knative Eventing
- [] Data Pipeline
- [] Unit Test via CICD
# Test Jenkins integration
