# Credit Card Approval Prediction

A production-ready MLOps pipeline for credit card approval prediction using machine learning.

## Project Overview

This project implements an end-to-end machine learning system that predicts credit card approval decisions based on applicant data. It demonstrates modern MLOps practices including:

- **ML Model Training**: Multiple classification models (XGBoost, LightGBM, CatBoost, etc.)
- **Experiment Tracking**: MLflow for model versioning and experiment management
- **API Service**: FastAPI for serving real-time predictions
- **Infrastructure**: Kubernetes deployment with Helm charts
- **CI/CD**: Jenkins pipeline with SonarQube quality checks
- **Monitoring**: Prometheus + Grafana for observability

## Quick Links

- [Project Structure](./STRUCTURE_EXPLAINED.md) - Architecture overview
- [Terraform Setup](./01_Terraform.md) - Infrastructure provisioning
- [Helm Deployment](./03_Helm_Deployment.md) - Kubernetes deployment
- [MLflow Development](./05_MLflow_Model_Development.md) - Model development guide
- [CI/CD Guide](./CI_CD_README.md) - Pipeline documentation
- [Deployment Guide](./06_DEPLOYMENT_GUIDE.md) - Deployment instructions

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Start local services
docker-compose up -d

# Run API
uvicorn app.main:app --reload

# Access services
# API: http://localhost:8000/docs
# MLflow: http://localhost:5000
```
