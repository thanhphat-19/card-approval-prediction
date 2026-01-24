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
| [00_Setup_Guide](./00_Setup_Guide.md) | ⚙️ **Start here!** |
| [01_Helm_Deployment](./01_Helm_Deployment.md) | Kubernetes deployment |
| [02_MLflow_Training](./02_MLflow_Training.md) | Model training |
| [03_API_Service](./03_API_Service.md) | FastAPI reference |
| [04_CICD_Pipeline](./04_CICD_Pipeline.md) | Jenkins CI/CD |
| [05_Monitoring](./05_Monitoring.md) | Prometheus + Grafana |
| [06_NGINX](./06_NGINX.md) | Services via NGINX |

---

## Project Structure

```
card-approval-prediction/
├── app/              # FastAPI application
├── cap_model/        # ML training pipeline
├── helm-charts/      # Kubernetes deployments
├── terraform/        # Infrastructure as Code
├── ansible/          # Jenkins VM setup
├── tests/            # Test suites
└── docs/             # Documentation
```

---

## Support

- [GitHub Issues](https://github.com/thanhphat-19/card-approval-prediction/issues)
