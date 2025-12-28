"""
Pytest configuration and fixtures for Card Approval Prediction API tests.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def mock_mlflow():
    """Mock MLflow to avoid connecting to real server during tests."""
    with patch("mlflow.set_tracking_uri"), patch("mlflow.pyfunc.load_model") as mock_load:
        # Create a mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = [1]  # Default: Approved
        mock_load.return_value = mock_model
        yield mock_model


@pytest.fixture(scope="session")
def mock_redis():
    """Mock Redis client."""
    with patch("redis.from_url") as mock_redis:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_redis.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="session")
def mock_database():
    """Mock database connection."""
    with patch("sqlalchemy.create_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_engine


@pytest.fixture
def client(mock_mlflow, mock_redis, mock_database):
    """Create test client with mocked dependencies."""
    # Set environment variables for testing
    os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["MODEL_NAME"] = "card_approval_model"
    os.environ["MODEL_STAGE"] = "Production"

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


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
