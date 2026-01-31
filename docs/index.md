# Card Approval Prediction - Documentation

MLOps pipeline for credit card approval prediction on GCP.

---

## Quick Start

```bash
git clone https://github.com/thanhphat-19/card-approval-prediction.git
cd card-approval-prediction
cp config.example.env config.env  # Edit with your GCP project ID
```

> 📖 **Full guide**: [Setup Guide](./00_Setup_Guide.md)

---

## Documentation

| Doc | Description |
|-----|-------------|
| [00_Setup_Guide](./00_Setup_Guide.md) | ⚙️ **Start here!** Setup & configuration reference |
| [01_Helm_Deployment](./01_Helm_Deployment.md) | Deploy MLflow, API, and monitoring to Kubernetes |
| [02_MLflow_Training](./02_MLflow_Training.md) | Train and register models with MLflow |
| [03_CICD_Pipeline](./03_CICD_Pipeline.md) | Jenkins CI/CD pipeline setup |
| [04_NGINX](./04_NGINX.md) | NGINX Ingress configuration |

---

## Project Structure

```
card-approval-prediction/
├── app/              # FastAPI application
├── training/         # ML training pipeline
│   ├── scripts/      # Training, evaluation, download scripts
│   └── src/          # Data processing and model utilities
├── scripts/          # CI/CD helper scripts
├── helm-charts/      # Kubernetes deployments
│   ├── card-approval/           # API stack
│   ├── card-approval-training/  # MLflow stack
│   └── infrastructure/          # Base charts
├── terraform/        # GCP infrastructure as code
├── ansible/          # Jenkins deployment automation
└── docs/             # Documentation
```

---

## Support

- [GitHub Issues](https://github.com/thanhphat-19/card-approval-prediction/issues)
