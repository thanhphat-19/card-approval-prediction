# Credit Card Approval Prediction - Documentation

> A production-ready MLOps pipeline for credit card approval prediction using machine learning.

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Client] --> B[API Gateway]
    end

    subgraph "Application Layer"
        B --> C[FastAPI Service]
        C --> D[Model Service]
        C --> E[Preprocessing Service]
    end

    subgraph "ML Layer"
        D --> F[MLflow Model Registry]
        F --> G[GCS Artifacts]
    end

    subgraph "Data Layer"
        C --> H[PostgreSQL]
        C --> I[Redis Cache]
    end

    subgraph "Infrastructure"
        J[GKE Cluster] --> C
        K[Prometheus] --> C
        K --> L[Grafana]
    end
```

---

## 📚 Documentation

| # | Document | Description |
|---|----------|-------------|
| 01 | [Terraform Setup](./01_Terraform.md) | GCP infrastructure setup |
| 02 | [Terraform Architecture](./02_terraform_architecture.md) | Infrastructure design |
| 03 | [Helm Deployment](./03_Helm_Deployment.md) | Kubernetes deployment |
| 04 | [MLflow & Training](./04_MLflow_Training.md) | Model training pipeline |
| 05 | [API Service](./05_API_Service.md) | FastAPI application |
| 06 | [CI/CD Pipeline](./06_CICD_Pipeline.md) | Jenkins automation |
| 07 | [Monitoring](./07_Monitoring.md) | Prometheus + Grafana |

---

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/your-org/card-approval-prediction.git
cd card-approval-prediction
pip install -r requirements.txt

# 2. Start local services
docker-compose up -d

# 3. Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Access services
open http://localhost:8000/docs    # API Documentation
open http://localhost:5000         # MLflow UI
```

---

## 🗂️ Project Structure

```
card-approval-prediction/
├── app/                    # FastAPI application
├── cap_model/              # ML training pipeline
├── helm-charts/            # Kubernetes deployments
├── terraform/              # Infrastructure as Code
├── scripts/                # Utility scripts
├── tests/                  # Test suites
├── ansible/                # Configuration management
└── docs/                   # This documentation
```

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/card-approval-prediction/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/card-approval-prediction/discussions)
