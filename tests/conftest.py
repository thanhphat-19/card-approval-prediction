"""
Pytest configuration and fixtures for Card Approval Prediction API tests.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
    # Return a DataFrame with PCA-transformed features
    mock.preprocess.return_value = pd.DataFrame({"PC1": [0.5], "PC2": [-0.3], "PC3": [0.1]})
    return mock


@pytest.fixture
def client(mock_model, mock_preprocessing_service):
    """Create test client with mocked dependencies."""
    # Set environment variables for testing
    os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"
    os.environ["MODEL_NAME"] = "card_approval_model"
    os.environ["MODEL_STAGE"] = "Production"

    # Patch all external dependencies
    with patch("app.services.model_service.mlflow") as mock_mlflow, patch(
        "app.utils.mlflow_helpers.mlflow"
    ) as mock_utils_mlflow, patch("app.services.preprocessing_service.mlflow") as mock_preproc_mlflow, patch(
        "app.services.preprocessing_service.joblib"
    ) as mock_joblib, patch(
        "app.utils.mlflow_helpers.check_mlflow_connection"
    ) as mock_check_mlflow:
        # Mock MLflow client for model service
        mock_client = MagicMock()
        mock_version = MagicMock()
        mock_version.version = "1"
        mock_version.run_id = "test-run-id"
        mock_version.current_stage = "Production"
        mock_client.search_model_versions.return_value = [mock_version]
        mock_utils_mlflow.tracking.MlflowClient.return_value = mock_client
        mock_mlflow.pyfunc.load_model.return_value = mock_model

        # Mock preprocessing service artifacts loading
        mock_preproc_mlflow.artifacts.download_artifacts.return_value = "/tmp/mock_artifacts"
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.5, -0.3, 0.1]])
        mock_pca = MagicMock()
        mock_pca.transform.return_value = np.array([[0.5, -0.3, 0.1]])
        mock_joblib.load.side_effect = [mock_scaler, mock_pca]

        # Mock health check MLflow connection
        mock_check_mlflow.return_value = True

        # Clear any cached services
        from app.services.model_service import get_model_service
        from app.services.preprocessing_service import get_preprocessing_service

        get_model_service.cache_clear()
        get_preprocessing_service.cache_clear()

        from app.main import app

        with TestClient(app) as test_client:
            yield test_client

        # Clean up caches after test
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
