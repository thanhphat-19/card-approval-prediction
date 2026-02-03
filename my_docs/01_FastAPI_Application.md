# Component 1: FastAPI Application

## Executive Summary

The FastAPI application serves as the production ML inference API for credit card approval prediction. It provides RESTful endpoints for real-time predictions, health monitoring, and metrics collection. The application implements industry best practices including model lifecycle management, distributed tracing, Prometheus metrics, and structured logging.

---

## 1. Concept & Theory

### What is this component?

The FastAPI application is the **serving layer** of the MLOps pipeline. It:
- Loads trained ML models from local storage or MLflow registry
- Preprocesses incoming credit card application data
- Performs real-time inference and returns approval decisions
- Exposes health endpoints for Kubernetes probes
- Collects metrics for observability

### Why FastAPI for ML APIs?

| Feature | Benefit for ML |
|---------|----------------|
| **Async support** | Handle concurrent prediction requests efficiently |
| **Pydantic validation** | Strict input validation for 18 credit features |
| **OpenAPI/Swagger** | Auto-generated API documentation |
| **Dependency injection** | Clean model lifecycle management |
| **Middleware support** | Easy integration with tracing, metrics, CORS |

### Core Concepts

1. **Lifespan Management**: Model loading at startup, cleanup at shutdown
2. **Request/Response Schemas**: Pydantic models for type-safe I/O
3. **Service Pattern**: Separation of concerns (model, preprocessing, routing)
4. **Observability**: Metrics, traces, and structured logs

### MLOps Lifecycle Position

```
Training Pipeline → MLflow Registry → [FastAPI API] → User Requests
                                           ↓
                              Prometheus ← Metrics ← Inference
```

---

## 2. Architecture & Design Decisions

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Routers    │  │   Schemas    │  │   Services   │          │
│  │  - health    │  │  - request   │  │  - model     │          │
│  │  - predict   │  │  - response  │  │  - preproc   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     Core     │  │    Utils     │  │  Middleware  │          │
│  │  - config    │  │  - gcs       │  │  - CORS      │          │
│  │  - logging   │  │  - mlflow    │  │  - Metrics   │          │
│  │  - metrics   │  │              │  │  - Tracing   │          │
│  │  - tracing   │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
          ┌───────────────────┴───────────────────┐
          ↓                                       ↓
    Local Model                            MLflow Registry
   (/app/models)                        (via MLFLOW_TRACKING_URI)
```

### Key Design Decisions

#### 1. Dual Model Loading Strategy
```python
# From app/services/model_service.py
if self.settings.MODEL_PATH:
    self._load_from_local_path()  # Embedded in Docker
else:
    self._load_from_mlflow()       # Runtime loading
```

**Trade-off**: Embedded models provide immutability and faster startup, but require rebuilding images for model updates.

#### 2. Singleton Model Service (LRU Cache)
```python
@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    """Get or create model service instance (cached singleton)"""
    return ModelService()
```

**Rationale**: Ensures model is loaded once and reused across requests.

#### 3. Async Lifespan Context
```python
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: Load model eagerly
    model_service = get_model_service()
    yield
    # Shutdown: Cleanup
```

**Benefit**: Model is ready before first request; no cold-start latency.

#### 4. Native Model Loading for predict_proba
```python
# Try multiple flavors for probability support
flavor_loaders = [
    ("xgboost", mlflow.xgboost.load_model),
    ("lightgbm", mlflow.lightgbm.load_model),
    ("catboost", mlflow.catboost.load_model),
    ("sklearn", mlflow.sklearn.load_model),
]
```

**Rationale**: MLflow pyfunc doesn't always expose `predict_proba`; native loaders do.

---

## 3. Implementation Guide

### Directory Structure

```
app/
├── main.py                 # Application entrypoint with lifespan
├── core/
│   ├── config.py           # Pydantic BaseSettings configuration
│   ├── logging.py          # Loguru structured logging setup
│   ├── metrics.py          # Prometheus counters, histograms, gauges
│   └── tracing.py          # OpenTelemetry instrumentation
├── routers/
│   ├── health.py           # /health, /ready, /live endpoints
│   └── predict.py          # /predict endpoint
├── schemas/
│   ├── health.py           # Health response models
│   └── prediction.py       # PredictionInput/Output models
├── services/
│   ├── model_service.py    # Model loading, inference, versioning
│   └── preprocessing_service.py  # Feature encoding, scaling, PCA
└── utils/
    ├── gcs.py              # GCS credential setup
    └── mlflow_helpers.py   # MLflow connection utilities
```

### Step-by-Step Implementation

#### Step 1: Configuration with Pydantic Settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Card Approval API"
    APP_VERSION: str = "1.0.0"

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://127.0.0.1:5000"
    MODEL_NAME: str = "card_approval_model"
    MODEL_STAGE: str = "Production"

    # Model Loading - local path or MLflow
    MODEL_PATH: str = ""  # Empty = load from MLflow

    # OpenTelemetry
    OTEL_ENABLED: bool = True
    OTEL_EXPORTER_ENDPOINT: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True
```

#### Step 2: Input/Output Schemas

```python
# app/schemas/prediction.py
from pydantic import BaseModel, Field

class PredictionInput(BaseModel):
    """18 features for credit card approval"""
    ID: int = Field(..., description="Customer ID")
    CODE_GENDER: str = Field(..., description="Gender (M/F)")
    FLAG_OWN_CAR: str = Field(..., description="Owns car (Y/N)")
    AMT_INCOME_TOTAL: float = Field(..., gt=0, description="Total income")
    # ... 14 more features

    class Config:
        json_schema_extra = {"example": {...}}

class PredictionOutput(BaseModel):
    prediction: int  # 0=Rejected, 1=Approved
    probability: float  # Approval probability
    decision: str  # "APPROVED" or "REJECTED"
    confidence: float
    version: Optional[str]
    timestamp: datetime
```

#### Step 3: Model Service Implementation

```python
# app/services/model_service.py
class ModelService:
    def __init__(self):
        self.model = None
        self.sklearn_model = None  # For predict_proba
        self.version = None
        self._load_model()

    def _load_model(self):
        if self.settings.MODEL_PATH:
            self._load_from_local_path()
        else:
            self._load_from_mlflow()

    def predict(self, features):
        with tracer.start_as_current_span("model_inference"):
            return self.model.predict(features)

    def predict_proba(self, features):
        if self.sklearn_model and hasattr(self.sklearn_model, "predict_proba"):
            return self.sklearn_model.predict_proba(features)
        return None
```

#### Step 4: Preprocessing Pipeline

```python
# app/services/preprocessing_service.py
class PreprocessingService:
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode → Align → Scale → PCA"""
        # One-hot encode categorical features
        df_encoded = pd.get_dummies(df, drop_first=True)

        # Align with training features
        df_aligned = self.align_features(df_encoded, self.feature_names)

        # Scale with StandardScaler
        df_scaled = self.scaler.transform(df_aligned)

        # Apply PCA
        df_pca = self.pca.transform(df_scaled)

        return pd.DataFrame(df_pca)
```

#### Step 5: Prediction Router

```python
# app/routers/predict.py
@router.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    # Convert to DataFrame
    df = pd.DataFrame([input_data.model_dump()])

    # Preprocess
    preprocessing_service = get_preprocessing_service()
    features = preprocessing_service.preprocess(df)

    # Predict
    model_service = get_model_service()
    prediction = model_service.predict(features)[0]
    proba = model_service.predict_proba(features)

    return PredictionOutput(
        prediction=int(prediction),
        probability=float(proba[0][1]) if proba else 0.5,
        decision="APPROVED" if prediction == 1 else "REJECTED",
        confidence=max(proba[0]) if proba else 0.5,
        version=model_service.version,
    )
```

#### Step 6: Prometheus Metrics

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "fastapi_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "fastapi_request_duration_seconds",
    "Request duration",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge("active_requests", "Active requests")
```

#### Step 7: Main Application

```python
# app/main.py
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting application...")
    model_service = get_model_service()
    logger.info(f"Model loaded: v{model_service.version}")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Setup tracing
setup_tracing(app)

# Add middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Include routers
app.include_router(health.router)
app.include_router(predict.router)
```

### Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `APP_NAME` | "Card Approval API" | Application name |
| `APP_VERSION` | "1.0.0" | API version |
| `MODEL_PATH` | "" | Local model path (empty = MLflow) |
| `MLFLOW_TRACKING_URI` | "http://127.0.0.1:5000" | MLflow server URL |
| `MODEL_NAME` | "card_approval_model" | Registered model name |
| `MODEL_STAGE` | "Production" | Model stage/alias |
| `LOG_LEVEL` | "INFO" | Logging level |
| `OTEL_ENABLED` | true | Enable tracing |
| `OTEL_EXPORTER_ENDPOINT` | "" | Tempo/Jaeger endpoint |

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Loading model on every request | Use `@lru_cache` singleton pattern |
| Feature mismatch with training | Store `feature_names.json` with model |
| Missing categorical values | Align features with reference columns |
| No health checks | Implement `/health`, `/ready`, `/live` |

### Security Considerations

1. **Input Validation**: Pydantic enforces type constraints
   ```python
   AMT_INCOME_TOTAL: float = Field(..., gt=0)  # Must be positive
   ```

2. **CORS Configuration**: Restrict origins in production
   ```python
   allow_origins=settings.CORS_ORIGINS.split(",")
   ```

3. **Rate Limiting**: Consider adding via middleware or API gateway

4. **Secrets Management**: Use environment variables, never hardcode

### Performance Optimization

1. **Eager Model Loading**: Load at startup, not first request
2. **Async Endpoints**: Use `async def` for I/O-bound operations
3. **Connection Pooling**: For database connections
4. **Caching**: Consider Redis for repeated predictions

### Debugging Guide

```bash
# Check model loading
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"ID": 1, "CODE_GENDER": "M", ...}'

# View metrics
curl http://localhost:8000/metrics

# Check traces in Tempo/Grafana
```

---

## 5. Testing & Validation

### Test Categories

```python
# tests/conftest.py - Mock fixtures
@pytest.fixture
def mock_model():
    mock = MagicMock()
    mock.predict.return_value = np.array([1])
    mock.predict_proba.return_value = np.array([[0.15, 0.85]])
    return mock

@pytest.fixture
def client(mock_model):
    with patch("app.services.model_service.mlflow"):
        with TestClient(app) as client:
            yield client
```

### Test Scenarios

| Test | Expected |
|------|----------|
| Valid prediction | 200 OK with approval decision |
| Missing required field | 422 Validation Error |
| Invalid data type | 422 Validation Error |
| Health endpoint | 200 OK with "healthy" status |
| Metrics endpoint | Prometheus format output |

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_predict.py -v
```

### Validation Checklist

- [ ] Model loads successfully at startup
- [ ] Prediction returns valid JSON response
- [ ] Health endpoints respond correctly
- [ ] Metrics are exposed at `/metrics`
- [ ] Traces appear in Tempo/Jaeger
- [ ] Error responses follow schema

---

## 6. Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [MLflow Model Loading](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Prometheus Python Client](https://prometheus.github.io/client_python/)
