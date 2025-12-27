# Card Approval Prediction - Deployment Operations Guide

## 🚀 Quick Start

### 1. Uninstall Existing Deployments
```bash
chmod +x uninstall-all.sh deploy-all.sh
./uninstall-all.sh
```

### 2. Deploy Complete Infrastructure
```bash
./deploy-all.sh
```

### 3. Verify Deployment
```bash
# Check all pods
kubectl get pods -A | grep -E '(card-approval|recsys-training)'

# Check services
kubectl get svc -A | grep -E '(card-approval|recsys-training)'

# Check helm releases
helm list -A
```

---

## 📊 Training Workflow

### Step 1: Port-Forward MLflow
```bash
# Terminal 1: Keep this running
kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000
```

Access MLflow UI: http://localhost:5000

### Step 2: Download Data (if needed)
```bash
python cap_model/scripts/download_data.py
```

### Step 3: Data Preprocessing
```bash
python cap_model/scripts/run_preprocessing.py \
  --raw-dir cap_model/data/raw \
  --output-dir cap_model/data/processed \
  --mlflow-uri http://localhost:5000
```

**Output:**
- `cap_model/data/processed/X_train.pkl`
- `cap_model/data/processed/X_test.pkl`
- `cap_model/data/processed/y_train.pkl`
- `cap_model/data/processed/y_test.pkl`
- `cap_model/data/processed/scaler.pkl`
- `cap_model/data/processed/pca.pkl`
- `cap_model/data/processed/feature_names.json`

### Step 4: Model Training
```bash
# Train all models (XGBoost, LightGBM, CatBoost, etc.)
python cap_model/scripts/run_training.py \
  --data-dir cap_model/data/processed \
  --output-dir cap_model/models \
  --mlflow-uri http://localhost:5000 \
  --metric F1-Score

# Train specific models only
python cap_model/scripts/run_training.py \
  --data-dir cap_model/data/processed \
  --output-dir cap_model/models \
  --mlflow-uri http://localhost:5000 \
  --models xgboost lightgbm \
  --metric F1-Score
```

**Available Models:**
- `xgboost` (Best performance)
- `lightgbm`
- `catboost`
- `random_forest`
- `logistic_regression`

**Metrics to Optimize:**
- `F1-Score` (default, recommended)
- `Accuracy`
- `Precision`
- `Recall`
- `ROC-AUC`

### Step 5: Register Model to Production
```bash
# In MLflow UI (http://localhost:5000):
# 1. Navigate to Models → card_approval_model
# 2. Select the best model version
# 3. Click "Stage" → "Transition to Production"

# Or via Python:
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name='card_approval_model',
    version=1,  # Change to your model version
    stage='Production'
)
"
```

---

## 🐳 Docker Image Build & Push

### Build Image
```bash
# Option 1: Build with specific tag
docker build -t us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:v1.0.0 .

# Option 2: Build with git commit hash
GIT_COMMIT=$(git rev-parse --short HEAD)
docker build -t us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:${GIT_COMMIT} .

# Option 3: Build with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker build -t us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:${TIMESTAMP} .
```

### Authenticate with Artifact Registry
```bash
# Configure Docker to authenticate with GCP Artifact Registry
gcloud auth configure-docker us-east1-docker.pkg.dev
```

### Push Image
```bash
# Push specific version
docker push us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:v1.0.0

# Also tag and push as latest
docker tag us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:v1.0.0 \
           us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:latest
docker push us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:latest
```

### Test Image Locally
```bash
# Run container locally
docker run -d \
  --name card-approval-test \
  -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e MODEL_NAME=card_approval_model \
  -e MODEL_STAGE=Production \
  us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:v1.0.0

# Check logs
docker logs -f card-approval-test

# Test endpoint
curl http://localhost:8000/health

# Stop and remove
docker stop card-approval-test
docker rm card-approval-test
```

---

## 🔄 Update Deployment with New Image

### Method 1: Using Helm Upgrade
```bash
helm upgrade card-approval ./helm-charts/card-approval \
  --namespace card-approval \
  --set api.image.tag=v1.0.0 \
  --wait
```

### Method 2: Using kubectl
```bash
kubectl set image deployment/card-approval-api \
  card-approval-api=us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:v1.0.0 \
  -n card-approval

# Watch rollout status
kubectl rollout status deployment/card-approval-api -n card-approval
```

### Method 3: Edit values.yaml and redeploy
```bash
# Edit helm-charts/card-approval/values.yaml
# Change api.image.tag to your new version

# Then redeploy
helm upgrade card-approval ./helm-charts/card-approval \
  --namespace card-approval \
  --wait
```

---

## 🧪 Testing the API

### Port-Forward API
```bash
# Terminal: Keep this running
kubectl port-forward -n card-approval svc/card-approval-api 8000:80
```

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "model_name": "card_approval_model",
  "model_stage": "Production",
  "model_version": "1",
  "timestamp": "2025-12-27T07:00:00.000Z"
}
```

### 2. Root Endpoint
```bash
curl http://localhost:8000/
```

### 3. API Documentation
Open in browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Single Prediction
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "CODE_GENDER": "F",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 180000,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -2500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 1,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2
  }'
```

**Expected Response:**
```json
{
  "prediction": 1,
  "probability": 0.95,
  "prediction_label": "Approved",
  "confidence": "high",
  "request_id": "uuid-here",
  "model_version": "1",
  "timestamp": "2025-12-27T07:00:00.000Z"
}
```

### 5. Batch Prediction
```bash
curl -X POST http://localhost:8000/api/v1/predict/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "data": [
      {
        "CODE_GENDER": "F",
        "FLAG_OWN_CAR": "Y",
        "AMT_INCOME_TOTAL": 180000,
        "NAME_EDUCATION_TYPE": "Higher education",
        ...
      },
      {
        "CODE_GENDER": "M",
        "FLAG_OWN_CAR": "N",
        "AMT_INCOME_TOTAL": 120000,
        ...
      }
    ]
  }'
```

### 6. Model Information
```bash
curl http://localhost:8000/api/v1/model/info
```

### 7. Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

---

## 🔍 Monitoring & Debugging

### View Logs
```bash
# MLflow logs
kubectl logs -f deployment/recsys-training-mlflow -n recsys-training

# API logs
kubectl logs -f deployment/card-approval-api -n card-approval

# PostgreSQL logs
kubectl logs -f deployment/card-approval-postgres -n card-approval

# Redis logs
kubectl logs -f deployment/card-approval-redis -n card-approval
```

### Check Pod Status
```bash
# All pods
kubectl get pods -A

# Specific namespace
kubectl get pods -n card-approval
kubectl get pods -n recsys-training

# Describe pod for details
kubectl describe pod <pod-name> -n <namespace>
```

### Exec into Pod
```bash
# API pod
kubectl exec -it deployment/card-approval-api -n card-approval -- /bin/bash

# PostgreSQL pod
kubectl exec -it deployment/card-approval-postgres -n card-approval -- psql -U app_user -d card_approval_db

# MLflow pod
kubectl exec -it deployment/recsys-training-mlflow -n recsys-training -- /bin/bash
```

### Check Resource Usage
```bash
# All pods
kubectl top pods -A

# Specific namespace
kubectl top pods -n card-approval

# Nodes
kubectl top nodes
```

### View Events
```bash
# All events
kubectl get events -A --sort-by='.lastTimestamp'

# Specific namespace
kubectl get events -n card-approval --sort-by='.lastTimestamp'
```

---

## 🗄️ Database Operations

### Connect to Application Database
```bash
# Port-forward PostgreSQL
kubectl port-forward -n card-approval svc/card-approval-postgres 5432:5432

# Connect with psql
psql -h localhost -p 5432 -U app_user -d card_approval_db
# Password: phatngothanh19
```

### Connect to MLflow Database
```bash
# Port-forward PostgreSQL
kubectl port-forward -n recsys-training svc/recsys-training-postgres 5432:5432

# Connect with psql
psql -h localhost -p 5432 -U mlflow -d mlflow
# Password: thanhphat192001
```

### Database Backup
```bash
# Backup application database
kubectl exec -n card-approval deployment/card-approval-postgres -- \
  pg_dump -U app_user card_approval_db > backup_app_$(date +%Y%m%d).sql

# Backup MLflow database
kubectl exec -n recsys-training deployment/recsys-training-postgres -- \
  pg_dump -U mlflow mlflow > backup_mlflow_$(date +%Y%m%d).sql
```

### Database Restore
```bash
# Restore application database
cat backup_app_20251227.sql | \
  kubectl exec -i -n card-approval deployment/card-approval-postgres -- \
  psql -U app_user -d card_approval_db

# Restore MLflow database
cat backup_mlflow_20251227.sql | \
  kubectl exec -i -n recsys-training deployment/recsys-training-postgres -- \
  psql -U mlflow -d mlflow
```

---

## 📈 Performance Testing

### Load Testing with Apache Bench
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Simple load test (100 requests, 10 concurrent)
ab -n 100 -c 10 -H "Content-Type: application/json" \
  -p prediction_payload.json \
  http://localhost:8000/api/v1/predict
```

### Create Test Payload
```bash
cat > prediction_payload.json << 'EOF'
{
  "CODE_GENDER": "F",
  "FLAG_OWN_CAR": "Y",
  "FLAG_OWN_REALTY": "Y",
  "CNT_CHILDREN": 0,
  "AMT_INCOME_TOTAL": 180000,
  "NAME_INCOME_TYPE": "Working",
  "NAME_EDUCATION_TYPE": "Higher education",
  "NAME_FAMILY_STATUS": "Married",
  "NAME_HOUSING_TYPE": "House / apartment",
  "DAYS_BIRTH": -12000,
  "DAYS_EMPLOYED": -2500,
  "FLAG_MOBIL": 1,
  "FLAG_WORK_PHONE": 0,
  "FLAG_PHONE": 1,
  "FLAG_EMAIL": 1,
  "OCCUPATION_TYPE": "Managers",
  "CNT_FAM_MEMBERS": 2
}
EOF
```

---

## 🔧 Troubleshooting

### Issue: MLflow Host Header Validation Error
**Symptom:** MLflow logs show "Rejected request with invalid Host header"

**Solution:** Already fixed in `mlflow/templates/deployment.yaml` with:
```yaml
env:
- name: MLFLOW_ALLOWED_HOSTS
  value: "*"
```

### Issue: API Can't Connect to MLflow
**Check:**
```bash
# From API pod
kubectl exec -it deployment/card-approval-api -n card-approval -- /bin/bash
curl http://recsys-training-mlflow.recsys-training.svc.cluster.local:5000/health
```

### Issue: Image Pull Error
**Check:**
```bash
# Verify image exists
gcloud artifacts docker images list us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys

# Check credentials
kubectl describe pod <pod-name> -n card-approval | grep -A 5 "Events:"
```

### Issue: Pod CrashLoopBackOff
```bash
# View logs
kubectl logs <pod-name> -n <namespace> --previous

# Describe pod
kubectl describe pod <pod-name> -n <namespace>
```

---

## 📝 Complete Workflow Example

```bash
# 1. Clean slate
cd /home/thanhphat/workspace/card-approval-prediction/helm-charts
./uninstall-all.sh
# Answer: yes, yes, yes (delete PVCs and namespaces)

# 2. Deploy infrastructure
./deploy-all.sh
# Wait for completion (~5-10 minutes)

# 3. Verify deployment
kubectl get pods -A | grep -E '(card-approval|recsys-training)'

# 4. Start port-forwards (in separate terminals)
kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000 &
kubectl port-forward -n card-approval svc/card-approval-api 8000:80 &

# 5. Train model
cd /home/thanhphat/workspace/card-approval-prediction
python cap_model/scripts/run_preprocessing.py --mlflow-uri http://localhost:5000
python cap_model/scripts/run_training.py --mlflow-uri http://localhost:5000

# 6. Register model to Production (via MLflow UI at http://localhost:5000)

# 7. Build and push image
docker build -t us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:v1.0.0 .
gcloud auth configure-docker us-east1-docker.pkg.dev
docker push us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:v1.0.0

# 8. Update deployment
helm upgrade card-approval ./helm-charts/card-approval \
  --namespace card-approval \
  --set api.image.tag=v1.0.0 \
  --wait

# 9. Test API
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Open in browser

# 10. Make a prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -d @test_payload.json
```

---

## 🎯 Best Practices

1. **Always use specific image tags** (not `latest`) in production
2. **Test locally** before pushing to cluster
3. **Monitor logs** during deployment
4. **Backup databases** before major changes
5. **Use secrets** for sensitive data (not hardcoded passwords)
6. **Set resource limits** to prevent cluster resource exhaustion
7. **Enable HPA** for auto-scaling under load
8. **Use namespaces** for environment isolation
9. **Tag images** with git commit hash for traceability
10. **Monitor metrics** via Prometheus endpoint

---

## 📞 Quick Reference

| Command | Description |
|---------|-------------|
| `./uninstall-all.sh` | Remove all deployments |
| `./deploy-all.sh` | Deploy complete infrastructure |
| `helm list -A` | List all Helm releases |
| `kubectl get pods -A` | List all pods |
| `kubectl logs -f <pod> -n <ns>` | Follow pod logs |
| `kubectl describe pod <pod> -n <ns>` | Pod details |
| `kubectl port-forward ...` | Forward service to localhost |
| `helm upgrade --install ...` | Install or upgrade release |
| `docker build -t ...` | Build Docker image |
| `docker push ...` | Push image to registry |

---

**Last Updated:** 2025-12-27
**Maintainer:** MLOps Team
