# Deployment Verification Guide

## Infrastructure Overview

### ✅ Deployed Services

**MLflow Infrastructure (namespace: recsys-training)**
- PostgreSQL: `recsys-training-postgres` (5432)
- MLflow: `recsys-training-mlflow` (5000)

**Card Approval Infrastructure (namespace: card-approval)**
- PostgreSQL: `card-approval-postgres` (5432)
- Redis: `card-approval-redis` (6379)
- FastAPI: `card-approval-api` (80)

---

## Step 1: Test MLflow Infrastructure

### 1.1 Port Forward MLflow
```bash
# Terminal 1 - Keep this running
kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000
```

### 1.2 Verify MLflow Connectivity
```bash
# Terminal 2 - Test MLflow health
curl http://localhost:5000/health

# Access MLflow UI
# Open browser: http://localhost:5000
```

### 1.3 Run Preprocessing
```bash
cd cap_model

# Run data preprocessing
python scripts/run_preprocessing.py \
  --raw-data-dir data/raw \
  --output-dir data/processed \
  --test-size 0.2 \
  --pca-components 5

# Verify preprocessed data
ls -lh data/processed/
# Should see: X_train.csv, X_test.csv, y_train.csv, y_test.csv
# And: scaler.pkl, pca.pkl, feature_names.json
```

### 1.4 Run Training & Register Model
```bash
# Train models with MLflow tracking
python scripts/run_training.py \
  --data-dir data/processed \
  --output-dir models \
  --mlflow-uri http://localhost:5000 \
  --model-name card_approval_model \
  --metric F1-Score \
  --auto-register

# Check MLflow UI for experiments
# Browser: http://localhost:5000
# Should see: experiments, runs, and registered model "card_approval_model" in Production stage
```

### 1.5 Verify Model Registration
```bash
# Check registered models
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
client = mlflow.tracking.MlflowClient()

# List registered models
models = client.search_registered_models()
for model in models:
    print(f'Model: {model.name}')
    versions = client.search_model_versions(f\"name='{model.name}'\")
    for v in versions:
        print(f'  Version {v.version}: {v.current_stage}')
"
```

---

## Step 2: Test Card Approval API

### 2.1 Port Forward API
```bash
# Terminal 3 - Keep this running
kubectl port-forward -n card-approval svc/card-approval-api 8000:80
```

### 2.2 Health Check
```bash
# Terminal 4 - Test health endpoints
curl http://localhost:8000/

curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "mlflow_connected": true,
#   "database_connected": true,
#   "redis_connected": true
# }
```

### 2.3 Test Prediction API
```bash
# Test prediction endpoint
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

# Expected response:
# {
#   "prediction": 1,
#   "probability": 0.95,
#   "decision": "Approved",
#   "confidence": 0.95,
#   "timestamp": "2025-12-27T10:30:00"
# }
```

### 2.4 Test with Multiple Examples
```bash
# High risk applicant (likely rejected)
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008805,
    "CODE_GENDER": "F",
    "FLAG_OWN_CAR": "N",
    "FLAG_OWN_REALTY": "N",
    "CNT_CHILDREN": 3,
    "AMT_INCOME_TOTAL": 50000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Secondary / secondary special",
    "NAME_FAMILY_STATUS": "Single / not married",
    "NAME_HOUSING_TYPE": "With parents",
    "DAYS_BIRTH": -8000,
    "DAYS_EMPLOYED": -500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 0,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Laborers",
    "CNT_FAM_MEMBERS": 4.0
  }'
```

### 2.5 Access API Documentation
```bash
# Open in browser
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## Step 3: Monitoring & Logs

### View Logs
```bash
# MLflow logs
kubectl logs -n recsys-training -l app=mlflow -f

# API logs
kubectl logs -n card-approval -l app=api -f

# PostgreSQL logs (MLflow)
kubectl logs -n recsys-training -l app=postgres -f

# PostgreSQL logs (API)
kubectl logs -n card-approval -l app=postgres -f

# Redis logs
kubectl logs -n card-approval -l app=redis -f
```

### Check Pod Status
```bash
# All pods
kubectl get pods -A

# Specific namespace
kubectl get pods -n recsys-training
kubectl get pods -n card-approval

# Detailed pod info
kubectl describe pod <pod-name> -n <namespace>
```

### Check Services
```bash
# All services
kubectl get svc -A

# Test internal connectivity (from inside cluster)
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- sh
# Inside pod:
# curl recsys-training-mlflow.recsys-training.svc.cluster.local:5000/health
# curl card-approval-api.card-approval.svc.cluster.local/health
```

---

## Step 4: Persistent Data Verification

### Check Persistent Volumes
```bash
# List PVCs
kubectl get pvc -n recsys-training
kubectl get pvc -n card-approval

# Check PV details
kubectl get pv

# Describe PVC
kubectl describe pvc <pvc-name> -n <namespace>
```

### Verify Data Persistence
```bash
# Check MLflow database
kubectl exec -it -n recsys-training <postgres-pod> -- psql -U mlflow -d mlflow -c "\dt"

# Check API database
kubectl exec -it -n card-approval <postgres-pod> -- psql -U app_user -d card_approval_db -c "\dt"
```

---

## Troubleshooting

### MLflow Not Accessible
```bash
# Check MLflow pod status
kubectl get pods -n recsys-training -l app=mlflow

# Check logs
kubectl logs -n recsys-training -l app=mlflow --tail=50

# Check PostgreSQL connectivity
kubectl exec -it -n recsys-training <postgres-pod> -- psql -U mlflow -d mlflow -c "SELECT 1"
```

### API Not Responding
```bash
# Check API pod status
kubectl get pods -n card-approval -l app=api

# Check logs
kubectl logs -n card-approval -l app=api --tail=50

# Check if model is loaded
kubectl logs -n card-approval -l app=api | grep "Model loaded"
```

### Model Not Found
```bash
# Verify model is registered in MLflow
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
client = mlflow.tracking.MlflowClient()
versions = client.search_model_versions(\"name='card_approval_model'\")
for v in versions:
    print(f'Version {v.version}: Stage={v.current_stage}')
"

# If no model in Production stage, transition one:
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name='card_approval_model',
    version='1',
    stage='Production'
)
"
```

---

## Clean Up (Optional)

### Delete Deployments
```bash
# Delete card approval
helm uninstall card-approval -n card-approval
kubectl delete namespace card-approval

# Delete MLflow
helm uninstall recsys-training -n recsys-training
kubectl delete namespace recsys-training
```

### Note on Persistent Volumes
If you have `reclaimPolicy: Retain`, PVs will not be deleted automatically.
To clean them up:
```bash
# List orphaned PVs
kubectl get pv | grep Released

# Delete specific PV
kubectl delete pv <pv-name>
```

---

## Success Criteria

✅ **Infrastructure Deployed:**
- All pods in `Running` state with `1/1` READY
- Services accessible via ClusterIP
- PVCs bound to PVs

✅ **MLflow Working:**
- Health endpoint returns 200
- UI accessible at http://localhost:5000
- Can run preprocessing and training
- Model registered in Production stage

✅ **API Working:**
- Health endpoint shows all services connected
- Prediction endpoint returns valid responses
- API documentation accessible
- Logs show model loaded successfully

---

## Next Steps

1. **Set up Ingress** for external access (optional)
2. **Configure monitoring** with Prometheus/Grafana
3. **Add authentication** to API endpoints
4. **Set up CI/CD** pipeline for automated deployments
5. **Implement model monitoring** and drift detection
6. **Add integration tests** for end-to-end workflows
