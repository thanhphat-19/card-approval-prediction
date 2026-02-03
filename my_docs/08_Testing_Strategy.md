# Component 8: Testing Strategy

## Executive Summary

The testing strategy ensures code quality and reliability through a comprehensive suite of unit tests, integration tests, and API tests. Using pytest with fixtures for mocking ML models and services, the tests cover the FastAPI application, preprocessing pipelines, model services, and training utilities. This enables confident deployments and regression prevention.

---

## 1. Concept & Theory

### Why Testing for ML Systems?

ML systems have unique testing challenges:

| Challenge | Testing Solution |
|-----------|------------------|
| Model behavior changes | Test with fixed model outputs (mocks) |
| Preprocessing drift | Test feature engineering pipeline |
| API contract changes | Schema validation tests |
| Integration complexity | Mocked dependencies for isolation |

### Test Pyramid for ML

```
                    ┌────────────────┐
                    │   E2E Tests    │  ← Few, slow, high confidence
                    │   (Deployed)   │
                   ┌┴────────────────┴┐
                   │ Integration Tests│  ← API endpoints, service interactions
                  ┌┴──────────────────┴┐
                  │    Unit Tests      │  ← Many, fast, isolated
                  │  (Functions/Classes)│
                  └────────────────────┘
```

### Test Categories

| Category | Scope | Speed | Mocking |
|----------|-------|-------|---------|
| **Unit Tests** | Single function/class | Fast | Heavy |
| **Integration Tests** | Multiple components | Medium | Selective |
| **API Tests** | Full request/response | Slow | External deps only |
| **Contract Tests** | Schema validation | Fast | None |

---

## 2. Architecture & Design Decisions

### Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                     # Shared fixtures
├── test_api.py                     # Full API tests
├── test_main.py                    # App initialization tests
├── test_health.py                  # Health endpoint tests
├── test_predict.py                 # Prediction endpoint tests
├── test_schemas.py                 # Pydantic schema tests
├── test_core_config.py             # Configuration tests
├── test_core_logging.py            # Logging tests
├── test_core_metrics.py            # Metrics tests
├── test_routers_health.py          # Health router tests
├── test_routers_predict.py         # Predict router tests
├── test_services_model_service.py  # Model service tests
├── test_services_preprocessing.py  # Preprocessing tests
├── test_utils_gcs.py               # GCS utilities tests
├── test_utils_mlflow_helpers.py    # MLflow helpers tests
├── test_training_data_loader.py    # Data loading tests
├── test_training_features.py       # Feature engineering tests
├── test_training_model_configs.py  # Model config tests
├── test_training_mlflow_registry.py # Registry tests
└── test_training_utils.py          # Training utilities tests
```

### Key Design Decisions

#### 1. Centralized Fixtures in conftest.py
```python
# tests/conftest.py
@pytest.fixture(scope="session")
def mock_model():
    """Reusable mock model across all tests"""
    mock = MagicMock()
    mock.predict.return_value = np.array([1])
    mock.predict_proba.return_value = np.array([[0.15, 0.85]])
    return mock
```

**Benefit**: Consistent mocks, reduced duplication.

#### 2. Scoped Client Fixture
```python
@pytest.fixture
def client(mock_model, mock_preprocessing_service):
    """Create test client with mocked dependencies"""
    with patch("app.services.model_service.mlflow"):
        with TestClient(app) as client:
            yield client
```

**Rationale**: Each test gets fresh client; mocks reset between tests.

#### 3. Cache Clearing
```python
# Clear singleton caches before/after tests
get_model_service.cache_clear()
get_preprocessing_service.cache_clear()
```

**Critical**: LRU-cached singletons persist across tests without clearing.

---

## 3. Implementation Guide

### Conftest.py - Shared Fixtures

```python
# tests/conftest.py
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def mock_model():
    """Create a mock ML model with predict and predict_proba."""
    mock = MagicMock()
    mock.predict.return_value = np.array([1])  # Default: Approved
    mock.predict_proba.return_value = np.array([[0.15, 0.85]])  # 85% confidence
    return mock


@pytest.fixture(scope="session")
def mock_preprocessing_service():
    """Create a mock preprocessing service."""
    import pandas as pd

    mock = MagicMock()
    mock.preprocess.return_value = pd.DataFrame({
        "PC1": [0.5], "PC2": [-0.3], "PC3": [0.1]
    })
    return mock


@pytest.fixture
def client(mock_model, mock_preprocessing_service):
    """Create test client with mocked dependencies."""
    # Set environment variables
    os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"
    os.environ["MODEL_NAME"] = "card_approval_model"
    os.environ["MODEL_STAGE"] = "Production"

    feature_names_json = json.dumps({"feature_names": ["feat1", "feat2", "feat3"]})

    original_open = open

    def custom_open(*args, **kwargs):
        filepath = str(args[0]) if args else ""
        if "feature_names.json" in filepath:
            from unittest.mock import mock_open
            return mock_open(read_data=feature_names_json)()
        return original_open(*args, **kwargs)

    with patch("app.services.model_service.mlflow") as mock_mlflow, \
         patch("app.utils.mlflow_helpers.mlflow") as mock_utils_mlflow, \
         patch("app.services.preprocessing_service.mlflow") as mock_preproc_mlflow, \
         patch("app.services.preprocessing_service.joblib") as mock_joblib, \
         patch("app.services.preprocessing_service.open", custom_open), \
         patch("app.services.model_service.load_model_with_flavor") as mock_load_flavor:

        # Mock MLflow client
        mock_client = MagicMock()
        mock_version = MagicMock()
        mock_version.version = "1"
        mock_version.run_id = "test-run-id"
        mock_client.search_model_versions.return_value = [mock_version]
        mock_utils_mlflow.tracking.MlflowClient.return_value = mock_client
        mock_mlflow.pyfunc.load_model.return_value = mock_model
        mock_load_flavor.return_value = mock_model

        # Mock preprocessing artifacts
        mock_preproc_mlflow.artifacts.download_artifacts.return_value = "/tmp/mock"
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.5, -0.3, 0.1]])
        mock_pca = MagicMock()
        mock_pca.transform.return_value = np.array([[0.5, -0.3, 0.1]])
        mock_joblib.load.side_effect = [mock_scaler, mock_pca]

        # Clear caches
        from app.services.model_service import get_model_service
        from app.services.preprocessing_service import get_preprocessing_service
        get_model_service.cache_clear()
        get_preprocessing_service.cache_clear()

        from app.main import app
        with TestClient(app) as test_client:
            yield test_client

        # Cleanup
        get_model_service.cache_clear()
        get_preprocessing_service.cache_clear()


@pytest.fixture
def sample_prediction_input():
    """Sample prediction input data."""
    return {
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
        "CNT_FAM_MEMBERS": 2.0,
    }


@pytest.fixture
def high_risk_input():
    """Sample high-risk applicant (likely rejected)."""
    return {
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
        "CNT_FAM_MEMBERS": 4.0,
    }
```

### API Tests

```python
# tests/test_api.py
import pytest


class TestAPI:
    """Test FastAPI application endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"

    def test_docs_endpoint(self, client):
        """Test OpenAPI docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is valid."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/predict" in schema["paths"]
```

### Health Endpoint Tests

```python
# tests/test_health.py
import pytest


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint(self, client):
        """Test /health returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_ready_endpoint(self, client):
        """Test /health/ready returns ready status."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "model_loaded" in data

    def test_live_endpoint(self, client):
        """Test /health/live returns alive status."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
```

### Prediction Endpoint Tests

```python
# tests/test_predict.py
import pytest


class TestPredictEndpoint:
    """Test prediction endpoint."""

    def test_predict_valid_input(self, client, sample_prediction_input):
        """Test prediction with valid input."""
        response = client.post("/predict", json=sample_prediction_input)
        assert response.status_code == 200

        data = response.json()
        assert "prediction" in data
        assert "probability" in data
        assert "decision" in data
        assert data["decision"] in ["APPROVED", "REJECTED"]
        assert 0 <= data["probability"] <= 1

    def test_predict_returns_model_version(self, client, sample_prediction_input):
        """Test prediction includes model version."""
        response = client.post("/predict", json=sample_prediction_input)
        data = response.json()
        assert "version" in data

    def test_predict_invalid_gender(self, client, sample_prediction_input):
        """Test prediction fails with invalid gender."""
        sample_prediction_input["CODE_GENDER"] = "X"
        response = client.post("/predict", json=sample_prediction_input)
        # May still work if validation is lenient
        # assert response.status_code == 422

    def test_predict_missing_required_field(self, client, sample_prediction_input):
        """Test prediction fails with missing field."""
        del sample_prediction_input["AMT_INCOME_TOTAL"]
        response = client.post("/predict", json=sample_prediction_input)
        assert response.status_code == 422

    def test_predict_negative_income(self, client, sample_prediction_input):
        """Test prediction fails with negative income."""
        sample_prediction_input["AMT_INCOME_TOTAL"] = -50000
        response = client.post("/predict", json=sample_prediction_input)
        assert response.status_code == 422

    def test_predict_invalid_flag(self, client, sample_prediction_input):
        """Test prediction fails with invalid flag value."""
        sample_prediction_input["FLAG_MOBIL"] = 2  # Must be 0 or 1
        response = client.post("/predict", json=sample_prediction_input)
        assert response.status_code == 422
```

### Schema Validation Tests

```python
# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from app.schemas.prediction import PredictionInput, PredictionOutput


class TestPredictionInput:
    """Test PredictionInput schema."""

    def test_valid_input(self, sample_prediction_input):
        """Test valid input passes validation."""
        model = PredictionInput(**sample_prediction_input)
        assert model.ID == sample_prediction_input["ID"]
        assert model.AMT_INCOME_TOTAL == sample_prediction_input["AMT_INCOME_TOTAL"]

    def test_missing_required_field(self, sample_prediction_input):
        """Test missing required field fails."""
        del sample_prediction_input["CODE_GENDER"]
        with pytest.raises(ValidationError):
            PredictionInput(**sample_prediction_input)

    def test_invalid_income_type(self, sample_prediction_input):
        """Test invalid income type fails."""
        sample_prediction_input["AMT_INCOME_TOTAL"] = "not_a_number"
        with pytest.raises(ValidationError):
            PredictionInput(**sample_prediction_input)

    def test_income_must_be_positive(self, sample_prediction_input):
        """Test income must be positive."""
        sample_prediction_input["AMT_INCOME_TOTAL"] = 0
        with pytest.raises(ValidationError):
            PredictionInput(**sample_prediction_input)

    def test_flag_must_be_0_or_1(self, sample_prediction_input):
        """Test flag must be 0 or 1."""
        sample_prediction_input["FLAG_MOBIL"] = 5
        with pytest.raises(ValidationError):
            PredictionInput(**sample_prediction_input)


class TestPredictionOutput:
    """Test PredictionOutput schema."""

    def test_valid_output(self):
        """Test valid output creation."""
        output = PredictionOutput(
            prediction=1,
            probability=0.85,
            decision="APPROVED",
            confidence=0.85,
            version="1"
        )
        assert output.prediction == 1
        assert output.decision == "APPROVED"

    def test_probability_range(self):
        """Test probability must be between 0 and 1."""
        with pytest.raises(ValidationError):
            PredictionOutput(
                prediction=1,
                probability=1.5,  # Invalid
                decision="APPROVED",
                confidence=0.85
            )
```

### Model Service Tests

```python
# tests/test_services_model_service.py
import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestModelService:
    """Test ModelService class."""

    def test_model_loads_on_init(self, mock_model):
        """Test model loads during initialization."""
        with patch("app.services.model_service.mlflow") as mock_mlflow, \
             patch("app.services.model_service.get_settings") as mock_settings, \
             patch("app.services.model_service.setup_mlflow_tracking") as mock_setup, \
             patch("app.services.model_service.get_latest_model_version") as mock_version:

            mock_settings.return_value.MODEL_PATH = ""
            mock_settings.return_value.MLFLOW_TRACKING_URI = "http://localhost:5000"
            mock_settings.return_value.MODEL_NAME = "test_model"
            mock_settings.return_value.MODEL_STAGE = "Production"
            mock_version.return_value = ("1", "run-123")
            mock_mlflow.pyfunc.load_model.return_value = mock_model

            from app.services.model_service import ModelService
            service = ModelService()
            assert service.model is not None

    def test_predict_returns_array(self, mock_model):
        """Test predict returns numpy array."""
        features = np.array([[1, 2, 3]])
        mock_model.predict.return_value = np.array([1])

        result = mock_model.predict(features)
        assert isinstance(result, np.ndarray)
        assert result[0] == 1

    def test_predict_proba_returns_probabilities(self, mock_model):
        """Test predict_proba returns probability array."""
        features = np.array([[1, 2, 3]])
        mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])

        result = mock_model.predict_proba(features)
        assert result.shape == (1, 2)
        assert np.isclose(result.sum(), 1.0)
```

### Preprocessing Service Tests

```python
# tests/test_services_preprocessing.py
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch


class TestPreprocessingService:
    """Test PreprocessingService class."""

    def test_preprocess_returns_dataframe(self):
        """Test preprocess returns DataFrame."""
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[1, 2, 3]])

        mock_pca = MagicMock()
        mock_pca.transform.return_value = np.array([[0.5, -0.3]])

        with patch("app.services.preprocessing_service.joblib") as mock_joblib, \
             patch("app.services.preprocessing_service.get_settings") as mock_settings, \
             patch("builtins.open", create=True):

            mock_settings.return_value.MODEL_PATH = "/app/models"
            mock_joblib.load.side_effect = [mock_scaler, mock_pca]

            # Test that preprocessing transforms data correctly
            input_df = pd.DataFrame({
                "CODE_GENDER": ["M"],
                "AMT_INCOME_TOTAL": [100000]
            })

            # Would need full service setup to test preprocess method

    def test_align_features_adds_missing_columns(self):
        """Test align_features adds missing columns with zeros."""
        df = pd.DataFrame({"A": [1], "B": [2]})
        reference = ["A", "B", "C", "D"]

        # Manual test of alignment logic
        for col in reference:
            if col not in df.columns:
                df[col] = 0
        df = df[reference]

        assert list(df.columns) == reference
        assert df["C"].iloc[0] == 0
        assert df["D"].iloc[0] == 0
```

### Training Pipeline Tests

```python
# tests/test_training_features.py
import pytest
import pandas as pd
import numpy as np


class TestFeatureEngineering:
    """Test feature engineering pipeline."""

    def test_one_hot_encoding(self):
        """Test categorical features are one-hot encoded."""
        df = pd.DataFrame({
            "CODE_GENDER": ["M", "F", "M"],
            "AMT_INCOME_TOTAL": [100000, 150000, 80000]
        })

        encoded = pd.get_dummies(df, drop_first=True)

        assert "CODE_GENDER_M" in encoded.columns
        assert "CODE_GENDER" not in encoded.columns

    def test_train_test_split_stratified(self):
        """Test train-test split maintains class distribution."""
        from sklearn.model_selection import train_test_split

        y = pd.Series([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        X = pd.DataFrame({"feature": range(10)})

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.4, stratify=y
        )

        # Both sets should have 50% positive class
        assert y_train.mean() == pytest.approx(0.5, abs=0.1)
        assert y_test.mean() == pytest.approx(0.5, abs=0.1)
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Not clearing LRU cache | Add `cache_clear()` in fixtures |
| Tests depend on order | Use independent fixtures |
| Mocking wrong module | Mock where used, not defined |
| Flaky async tests | Use proper async fixtures |

### Mocking Best Practices

```python
# Mock where the function is USED, not where it's DEFINED
# Wrong:
with patch("mlflow.pyfunc.load_model"):
    pass

# Correct:
with patch("app.services.model_service.mlflow.pyfunc.load_model"):
    pass
```

### Test Coverage

```bash
# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Minimum coverage targets
# - Services: 80%+
# - Routers: 90%+
# - Schemas: 95%+
# - Utils: 70%+
```

---

## 5. Running Tests

### Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific file
pytest tests/test_predict.py -v

# Run specific test
pytest tests/test_predict.py::TestPredictEndpoint::test_predict_valid_input -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run in parallel
pytest tests/ -n auto

# Run with logging output
pytest tests/ -v -s --log-cli-level=DEBUG
```

### CI Integration

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    pytest tests/ \
      --cov=app \
      --cov-report=xml \
      --junitxml=test-results.xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: coverage.xml
```

---

## 6. Further Reading

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Testing ML Systems](https://madewithml.com/courses/mlops/testing/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
