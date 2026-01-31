"""
Unit tests for app/routers/predict.py module.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

from app.routers.predict import _get_prediction, _get_probabilities, _preprocess_input, get_model_info, predict
from app.schemas.prediction import PredictionInput, PredictionOutput


class TestPreprocessInput:
    """Tests for _preprocess_input helper function."""

    @pytest.fixture
    def sample_input(self):
        """Sample prediction input."""
        return PredictionInput(
            ID=123,
            CODE_GENDER="M",
            FLAG_OWN_CAR="Y",
            FLAG_OWN_REALTY="Y",
            CNT_CHILDREN=0,
            AMT_INCOME_TOTAL=100000.0,
            NAME_INCOME_TYPE="Working",
            NAME_EDUCATION_TYPE="Higher education",
            NAME_FAMILY_STATUS="Married",
            NAME_HOUSING_TYPE="House / apartment",
            DAYS_BIRTH=-10000,
            DAYS_EMPLOYED=-2000,
            FLAG_MOBIL=1,
            FLAG_WORK_PHONE=0,
            FLAG_PHONE=1,
            FLAG_EMAIL=0,
            OCCUPATION_TYPE="Managers",
            CNT_FAM_MEMBERS=2.0,
        )

    @patch("app.routers.predict.get_preprocessing_service")
    def test_returns_dataframe(self, mock_get_service, sample_input):
        """Test _preprocess_input returns DataFrame."""
        mock_service = MagicMock()
        mock_service.preprocess.return_value = pd.DataFrame({"PC1": [0.5], "PC2": [0.3]})
        mock_get_service.return_value = mock_service

        result = _preprocess_input(sample_input, "test-run-id")

        assert isinstance(result, pd.DataFrame)

    @patch("app.routers.predict.get_preprocessing_service")
    def test_calls_preprocessing_service(self, mock_get_service, sample_input):
        """Test _preprocess_input uses preprocessing service."""
        mock_service = MagicMock()
        mock_service.preprocess.return_value = pd.DataFrame({"PC1": [0.5]})
        mock_get_service.return_value = mock_service

        _preprocess_input(sample_input, "test-run-id")

        mock_service.preprocess.assert_called_once()


class TestGetPrediction:
    """Tests for _get_prediction helper function."""

    def test_returns_integer(self):
        """Test _get_prediction returns integer."""
        mock_service = MagicMock()
        mock_service.predict.return_value = np.array([1])

        result = _get_prediction(mock_service, pd.DataFrame({"PC1": [0.5]}))

        assert isinstance(result, int)
        assert result == 1

    def test_calls_model_predict(self):
        """Test _get_prediction calls model.predict."""
        mock_service = MagicMock()
        mock_service.predict.return_value = np.array([0])
        df = pd.DataFrame({"PC1": [0.5]})

        _get_prediction(mock_service, df)

        mock_service.predict.assert_called_once()


class TestGetProbabilities:
    """Tests for _get_probabilities helper function."""

    def test_returns_tuple(self):
        """Test _get_probabilities returns tuple of floats."""
        mock_service = MagicMock()
        mock_service.predict_proba.return_value = np.array([[0.2, 0.8]])

        result = _get_probabilities(mock_service, pd.DataFrame({"PC1": [0.5]}), 1)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_probability_and_confidence(self):
        """Test returns correct probability and confidence."""
        mock_service = MagicMock()
        mock_service.predict_proba.return_value = np.array([[0.15, 0.85]])

        prob_approved, confidence = _get_probabilities(mock_service, pd.DataFrame({"PC1": [0.5]}), 1)

        assert prob_approved == 0.85
        assert confidence == 0.85

    def test_fallback_when_proba_unavailable(self):
        """Test fallback values when predict_proba unavailable."""
        mock_service = MagicMock()
        mock_service.predict_proba.return_value = None

        prob_approved, confidence = _get_probabilities(mock_service, pd.DataFrame({"PC1": [0.5]}), 1)

        assert prob_approved == 1.0  # Prediction value
        assert confidence == 1.0


class TestPredictEndpoint:
    """Tests for predict endpoint function."""

    @pytest.fixture
    def sample_input(self):
        """Sample prediction input."""
        return PredictionInput(
            ID=123,
            CODE_GENDER="M",
            FLAG_OWN_CAR="Y",
            FLAG_OWN_REALTY="Y",
            CNT_CHILDREN=0,
            AMT_INCOME_TOTAL=100000.0,
            NAME_INCOME_TYPE="Working",
            NAME_EDUCATION_TYPE="Higher education",
            NAME_FAMILY_STATUS="Married",
            NAME_HOUSING_TYPE="House / apartment",
            DAYS_BIRTH=-10000,
            DAYS_EMPLOYED=-2000,
            FLAG_MOBIL=1,
            FLAG_WORK_PHONE=0,
            FLAG_PHONE=1,
            FLAG_EMAIL=0,
            OCCUPATION_TYPE="Managers",
            CNT_FAM_MEMBERS=2.0,
        )

    @patch("app.routers.predict._get_probabilities")
    @patch("app.routers.predict._get_prediction")
    @patch("app.routers.predict._preprocess_input")
    def test_returns_prediction_output(self, mock_preprocess, mock_predict, mock_proba, sample_input):
        """Test predict returns PredictionOutput."""
        mock_preprocess.return_value = pd.DataFrame({"PC1": [0.5]})
        mock_predict.return_value = 1
        mock_proba.return_value = (0.85, 0.85)

        mock_model_service = MagicMock()
        mock_model_service.run_id = "test-run"
        mock_model_service.get_model_info.return_value = {"version": "1"}

        result = predict(sample_input, mock_model_service)

        assert isinstance(result, PredictionOutput)

    @patch("app.routers.predict._get_probabilities")
    @patch("app.routers.predict._get_prediction")
    @patch("app.routers.predict._preprocess_input")
    def test_approved_decision(self, mock_preprocess, mock_predict, mock_proba, sample_input):
        """Test APPROVED decision for prediction=1."""
        mock_preprocess.return_value = pd.DataFrame({"PC1": [0.5]})
        mock_predict.return_value = 1
        mock_proba.return_value = (0.85, 0.85)

        mock_model_service = MagicMock()
        mock_model_service.run_id = "test-run"
        mock_model_service.get_model_info.return_value = {"version": "1"}

        result = predict(sample_input, mock_model_service)

        assert result.prediction == 1
        assert result.decision == "APPROVED"

    @patch("app.routers.predict._get_probabilities")
    @patch("app.routers.predict._get_prediction")
    @patch("app.routers.predict._preprocess_input")
    def test_rejected_decision(self, mock_preprocess, mock_predict, mock_proba, sample_input):
        """Test REJECTED decision for prediction=0."""
        mock_preprocess.return_value = pd.DataFrame({"PC1": [0.5]})
        mock_predict.return_value = 0
        mock_proba.return_value = (0.2, 0.8)

        mock_model_service = MagicMock()
        mock_model_service.run_id = "test-run"
        mock_model_service.get_model_info.return_value = {"version": "1"}

        result = predict(sample_input, mock_model_service)

        assert result.prediction == 0
        assert result.decision == "REJECTED"

    @patch("app.routers.predict._preprocess_input")
    def test_raises_http_exception_on_error(self, mock_preprocess, sample_input):
        """Test predict raises HTTPException on error."""
        mock_preprocess.side_effect = Exception("Processing error")

        mock_model_service = MagicMock()
        mock_model_service.run_id = "test-run"

        with pytest.raises(HTTPException) as exc_info:
            predict(sample_input, mock_model_service)

        assert exc_info.value.status_code == 500


class TestGetModelInfoEndpoint:
    """Tests for get_model_info endpoint function."""

    def test_returns_model_info(self):
        """Test get_model_info returns service info."""
        mock_service = MagicMock()
        expected_info = {
            "name": "test_model",
            "version": "1",
            "stage": "Production",
        }
        mock_service.get_model_info.return_value = expected_info

        result = get_model_info(mock_service)

        assert result == expected_info

    def test_calls_service_method(self):
        """Test get_model_info calls service.get_model_info."""
        mock_service = MagicMock()
        mock_service.get_model_info.return_value = {}

        get_model_info(mock_service)

        mock_service.get_model_info.assert_called_once()
