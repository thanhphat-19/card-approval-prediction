# Card Approval Prediction API

FastAPI service for credit card approval predictions using ML models from MLflow.

## 📁 Structure

```
app/
├── core/              # Core configuration
│   ├── config.py     # Settings management
│   └── logging.py    # Logging setup
├── routers/          # API endpoints
│   ├── health.py     # Health check
│   └── predict.py    # Prediction endpoints
├── schemas/          # Request/response models
│   ├── health.py     # Health schemas
│   └── prediction.py # Prediction schemas
├── services/         # Business logic
│   ├── model_service.py          # Model loading from MLflow
│   └── preprocessing_service.py  # Data preprocessing
└── main.py           # FastAPI application
```

## 🚀 Quick Start

### 1. **Start the API**

#### **Development Mode**
```bash
cd app
python main.py
# API available at: http://localhost:8000
```

#### **Production Mode (Docker)**
```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f app
```

### 2. **Access Documentation**

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### **1. Health Check**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Credit Card Approval API",
  "version": "1.0.0"
}
```

### **2. Make Prediction**
```bash
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
```

**Response:**
```json
{
  "prediction": 1,
  "probability": 1.0,
  "decision": "APPROVED",
  "confidence": 1.0,
  "version": "3"
}
```

### **3. Get Model Info**
```bash
curl http://localhost:8000/api/v1/model-info
```

**Response:**
```json
{
  "name": "card_approval_model",
  "stage": "Production",
  "version": "3",
  "run_id": "b62483e2fca64b0eb32f81105aaa0df8",
  "loaded": true
}
```

### **4. Reload Model**
```bash
curl -X POST http://localhost:8000/api/v1/reload-model
```

## ⚙️ Configuration

Configuration is managed via environment variables (`.env` file):

```env
# Application
APP_NAME=Credit Card Approval API
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# MLflow
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
MODEL_NAME=card_approval_model
MODEL_STAGE=Production

# GCP (optional)
GOOGLE_APPLICATION_CREDENTIALS=gcp-key.json
```

## 🔧 Development

### **Run Locally**
```bash
# Install dependencies
pip install -r ../requirements.txt

# Start MLflow (in separate terminal)
mlflow ui --port 5000

# Run API
python main.py
```

### **Run with Docker**
```bash
# Build
docker build -t card-approval-api .

# Run
docker run -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  card-approval-api
```

### **Run with Docker Compose**
```bash
# From project root
docker-compose up --build
```

## 🧪 Testing

### **Test Prediction Endpoint**
```bash
# Approved case
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_data_approved.json

# Rejected case
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_data_rejected.json
```

### **Health Check**
```bash
# Should return 200 OK
curl -f http://localhost:8000/health || echo "Health check failed"
```

## 📊 Preprocessing Pipeline

The API automatically preprocesses input data:

1. **One-hot encoding** (drop_first=True)
2. **Feature alignment** (ensure 48 features match training)
3. **Scaling** (StandardScaler)
4. **PCA** (reduce to 5 components)

Preprocessing artifacts are loaded from MLflow based on the model's run_id.

## 🐳 Docker

### **Build Image**
```bash
docker build -t card-approval-api .
```

### **Run Container**
```bash
docker run -d \
  --name card-approval-api \
  -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
  -v $(pwd)/gcp-key.json:/app/gcp-key.json \
  card-approval-api
```

### **Docker Compose**
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f app

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

## 📝 Key Files

| File | Description |
|------|-------------|
| `main.py` | FastAPI application entry point |
| `routers/predict.py` | Prediction endpoint logic |
| `services/model_service.py` | Model loading from MLflow |
| `services/preprocessing_service.py` | Input preprocessing |
| `core/config.py` | Configuration management |
| `schemas/prediction.py` | Request/response schemas |

## 🚨 Troubleshooting

### **Model not loading**
```bash
# Check MLflow is running
curl http://localhost:5000

# Verify model exists
curl http://localhost:5000/api/2.0/mlflow/registered-models/get?name=card_approval_model

# Check environment variables
docker-compose exec app env | grep MLFLOW
```

### **Prediction fails**
```bash
# Check logs
docker-compose logs app

# Verify preprocessing artifacts
ls -la cap_model/data/processed/

# Test with curl verbose
curl -v -X POST http://localhost:8000/api/v1/predict ...
```

### **Feature mismatch**
Ensure `feature_names.json` contains 48 one-hot encoded features, NOT PCA columns (PC1-PC5).

## 🔄 Update Model

After training a new model:

```bash
# 1. Restart API to load new version
docker-compose restart app

# 2. Or reload without restart
curl -X POST http://localhost:8000/api/v1/reload-model

# 3. Verify new version
curl http://localhost:8000/api/v1/model-info
```

## 📌 Notes

- API automatically loads model from MLflow on startup
- Preprocessing artifacts are cached for performance
- Model version comes from MLflow Production stage
- CORS is enabled for all origins (configure for production)
- Health check endpoint is used by Docker healthcheck
