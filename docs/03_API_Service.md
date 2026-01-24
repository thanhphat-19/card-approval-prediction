# Card Approval API Guide

## Overview

FastAPI service for credit card approval predictions.

```
app/
├── main.py                    # Application entry
├── core/
│   ├── config.py              # Settings
│   ├── logging.py             # Logging config
│   └── metrics.py             # Prometheus metrics
├── routers/
│   ├── health.py              # Health endpoints
│   └── predict.py             # Prediction endpoint
├── services/
│   ├── model_service.py       # Model loading
│   └── preprocessing_service.py  # Feature preprocessing
└── schemas/
    ├── health.py              # Health response
    └── prediction.py          # Prediction I/O
```

---

## Step 1: Configure Environment

Create `.env` file:

```bash
# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MODEL_NAME=card_approval_model
MODEL_STAGE=Production

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text

# App
APP_NAME=Card Approval API
APP_VERSION=1.0.0
```

**What each setting does:**
- `MLFLOW_TRACKING_URI` - Where to load models from
- `MODEL_NAME` - Registered model name
- `MODEL_STAGE` - Which stage (Production/Staging)
- `LOG_FORMAT` - `text` for local, `json` for Kubernetes

---

## Step 2: Run API Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**What this does:**
1. Starts FastAPI server on port 8000
2. Loads model from MLflow
3. Enables auto-reload for development

**Output you'll see:**
```bash
INFO:     Loading model card_approval_model from Production stage
INFO:     ✓ Model loaded: card_approval_model v3
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Access API docs:**
```bash
open http://localhost:8000/docs
```

---


## Step 3: Run API in Kubernetes

```bash
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
```

---

## Step 4: Test Health Endpoint

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-23T01:20:00Z",
  "mlflow_connected": true,
  "database_connected": true
}
```

---

## Step 5: Make a Prediction

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 150000,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -3000,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 1,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2
  }'
```

**Response:**
```json
{
  "decision": "APPROVED",
  "probability": 0.8523,
  "model_version": "3",
  "processing_time_ms": 45
}
```

**Decision mapping:**
- `prediction = 1` → `APPROVED` (Good credit)
- `prediction = 0` → `REJECTED` (Bad credit)

---

## Step 6: Check Metrics

```bash
curl http://localhost:8000/metrics
```

**Response (Prometheus format):**
```
# HELP prediction_requests_total Total prediction requests
prediction_requests_total{status="success"} 42

# HELP prediction_latency_seconds Prediction latency
prediction_latency_seconds_sum 1.89
prediction_latency_seconds_count 42

# HELP model_version_info Current model version
model_version_info{model="card_approval_model",version="3"} 1
```

---

## Step 7: Reload Model

```bash
curl -X POST http://localhost:8000/api/v1/model/reload
```

**Response:**
```json
{
  "status": "success",
  "message": "Model reloaded successfully",
  "new_version": "4"
}
```

**Why useful:**
- Load new model version without restart
- Zero-downtime model updates

---

## Step 8: Run Tests

```bash
pytest tests/ -v
```

**What tests cover:**
- Health endpoints
- Prediction endpoint
- Input validation
- Error handling

**Expected output:**
```bash
tests/test_api.py::TestHealthEndpoint::test_health_returns_200 PASSED
tests/test_api.py::TestHealthEndpoint::test_health_returns_status PASSED
tests/test_predict.py::TestPredictEndpoint::test_predict_valid_input PASSED
...
========================= 15 passed in 2.34s =========================
```

---

## API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |
| POST | `/api/v1/predict` | Make prediction |
| POST | `/api/v1/model/reload` | Reload model |
| GET | `/api/v1/model/info` | Model information |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | Swagger UI |

---

## Troubleshooting

**Model not loading:**
```bash
# Check MLflow connection
curl http://localhost:5000/api/2.0/mlflow/registered-models/list
```

**Slow predictions:**
```bash
# Check preprocessing artifacts loaded
curl http://localhost:8000/api/v1/model/info
```
