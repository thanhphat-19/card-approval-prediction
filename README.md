# Credit Card Approval Prediction - MLOps Project

End-to-end MLOps pipeline for a production-ready credit card approval prediction system.


### 🏗️ Architecture

This project implements:
- **Infrastructure**: GCP (GKE, GCS, Artifact Registry) with Terraform
- **CI/CD**: Jenkins + SonarQube (automated PR checks and deployments)
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

```bash
# Install tools
pip install -r requirements.txt


### Local Development Setup


1. **Install pre-commit hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```


2. **Start local services**:
   ```shell
   ./scripts/run-dev
   ```

3. **Access services**:
   - API: http://localhost:8000/docs
   - MLflow: http://localhost:5000
   - PostgreSQL: localhost:5432

### View Documentation

```bash
mkdocs serve
```

Access at: http://127.0.0.1:8000/



---

## 📁 Project Structure

```
card-approval-prediction/
├── docs/                           # 📚 Complete implementation guides
│   ├── 00_README.md               # Documentation overview
│   ├── 01_Terraform.md            # Infrastructure setup
│   ├── 03_Helm_Deployment.md      # Kubernetes deployment
│   └── 05_MLflow_Model_Development.md # ML development guide
├── src/
│   ├── api/                       # FastAPI application
│   ├── db/                        # Database models & migrations
│   ├── ml/                        # ML models & training
│   └── core/                      # Config & utilities
├── terraform/                     # Infrastructure as Code
│   ├── main.tf                    # GCP resources (GKE, GCS, Artifact Registry)
│   └── modules/                   # Terraform modules
├── helm-charts/                   # Kubernetes deployments
│   ├── recsys-training/          # MLflow + PostgreSQL
│   ├── infrastructure/           # Shared infrastructure charts
│   └── monitoring/               # Prometheus + Grafana
├── tests/                         # pytest tests
├── notebooks/                     # Jupyter notebooks for EDA
├── Jenkinsfile                    # CI/CD pipeline
├── docker-compose.yml             # Local development
├── Dockerfile                     # Container image
└── requirements.txt               # Python dependencies
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




## 🎓 Learning Outcomes

By completing this project, you will learn:
- Building production ML systems
- Infrastructure as Code with Terraform
- CI/CD pipelines with Jenkins
- Kubernetes & Helm for deployment
- MLflow for experiment tracking
- Monitoring with Prometheus & Grafana
- Best practices for MLOps

---

**🚀 Ready to start? Head to [docs/03_NEXT_STEPS_QUICKSTART.md](./docs/03_NEXT_STEPS_QUICKSTART.md)!**
