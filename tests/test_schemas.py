"""
Unit tests for app/schemas module.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.health import HealthResponse
from app.schemas.prediction import PredictionInput, PredictionOutput


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_create_health_response(self):
        """Test creating a valid HealthResponse."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            mlflow_connected=True,
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.mlflow_connected is True

    def test_health_response_default_mlflow_connected(self):
        """Test mlflow_connected defaults to False."""
        response = HealthResponse(
            status="degraded",
            version="1.0.0",
            timestamp=datetime.utcnow(),
        )

        assert response.mlflow_connected is False

    def test_health_response_various_statuses(self):
        """Test various status values."""
        statuses = ["healthy", "degraded", "unhealthy"]

        for status in statuses:
            response = HealthResponse(
                status=status,
                version="1.0.0",
                timestamp=datetime.utcnow(),
            )
            assert response.status == status

    def test_health_response_json_schema(self):
        """Test HealthResponse has json_schema_extra."""
        schema = HealthResponse.model_json_schema()
        assert "properties" in schema


class TestPredictionInput:
    """Tests for PredictionInput schema."""

    @pytest.fixture
    def valid_input(self):
        """Valid prediction input data."""
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

    def test_create_valid_input(self, valid_input):
        """Test creating a valid PredictionInput."""
        prediction_input = PredictionInput(**valid_input)

        assert prediction_input.ID == 5008804
        assert prediction_input.CODE_GENDER == "M"
        assert prediction_input.AMT_INCOME_TOTAL == 180000.0

    def test_missing_required_field(self, valid_input):
        """Test validation fails with missing required field."""
        del valid_input["CODE_GENDER"]

        with pytest.raises(ValidationError) as exc_info:
            PredictionInput(**valid_input)

        assert "CODE_GENDER" in str(exc_info.value)

    def test_negative_children_fails(self, valid_input):
        """Test CNT_CHILDREN cannot be negative."""
        valid_input["CNT_CHILDREN"] = -1

        with pytest.raises(ValidationError):
            PredictionInput(**valid_input)

    def test_zero_income_fails(self, valid_input):
        """Test AMT_INCOME_TOTAL must be greater than 0."""
        valid_input["AMT_INCOME_TOTAL"] = 0

        with pytest.raises(ValidationError):
            PredictionInput(**valid_input)

    def test_negative_income_fails(self, valid_input):
        """Test AMT_INCOME_TOTAL cannot be negative."""
        valid_input["AMT_INCOME_TOTAL"] = -1000

        with pytest.raises(ValidationError):
            PredictionInput(**valid_input)

    def test_flag_mobil_out_of_range(self, valid_input):
        """Test FLAG_MOBIL must be 0 or 1."""
        valid_input["FLAG_MOBIL"] = 2

        with pytest.raises(ValidationError):
            PredictionInput(**valid_input)

    def test_flag_work_phone_out_of_range(self, valid_input):
        """Test FLAG_WORK_PHONE must be 0 or 1."""
        valid_input["FLAG_WORK_PHONE"] = -1

        with pytest.raises(ValidationError):
            PredictionInput(**valid_input)

    def test_zero_family_members_fails(self, valid_input):
        """Test CNT_FAM_MEMBERS must be greater than 0."""
        valid_input["CNT_FAM_MEMBERS"] = 0

        with pytest.raises(ValidationError):
            PredictionInput(**valid_input)

    def test_model_dump(self, valid_input):
        """Test model_dump converts to dictionary."""
        prediction_input = PredictionInput(**valid_input)
        dumped = prediction_input.model_dump()

        assert isinstance(dumped, dict)
        assert dumped["ID"] == 5008804
        assert len(dumped) == len(valid_input)

    def test_different_gender_values(self, valid_input):
        """Test different gender values are accepted."""
        for gender in ["M", "F"]:
            valid_input["CODE_GENDER"] = gender
            prediction_input = PredictionInput(**valid_input)
            assert prediction_input.CODE_GENDER == gender

    def test_different_income_types(self, valid_input):
        """Test different income types are accepted."""
        income_types = ["Working", "Commercial associate", "Pensioner", "State servant"]

        for income_type in income_types:
            valid_input["NAME_INCOME_TYPE"] = income_type
            prediction_input = PredictionInput(**valid_input)
            assert prediction_input.NAME_INCOME_TYPE == income_type


class TestPredictionOutput:
    """Tests for PredictionOutput schema."""

    def test_create_valid_output(self):
        """Test creating a valid PredictionOutput."""
        output = PredictionOutput(
            prediction=1,
            probability=0.85,
            decision="APPROVED",
            confidence=0.85,
            version="1",
        )

        assert output.prediction == 1
        assert output.probability == 0.85
        assert output.decision == "APPROVED"
        assert output.confidence == 0.85
        assert output.version == "1"

    def test_prediction_output_auto_timestamp(self):
        """Test timestamp is auto-generated."""
        output = PredictionOutput(
            prediction=0,
            probability=0.2,
            decision="REJECTED",
            confidence=0.8,
        )

        assert output.timestamp is not None
        assert isinstance(output.timestamp, datetime)

    def test_probability_must_be_between_0_and_1(self):
        """Test probability must be in [0, 1] range."""
        # Below 0
        with pytest.raises(ValidationError):
            PredictionOutput(
                prediction=1,
                probability=-0.1,
                decision="APPROVED",
                confidence=0.5,
            )

        # Above 1
        with pytest.raises(ValidationError):
            PredictionOutput(
                prediction=1,
                probability=1.1,
                decision="APPROVED",
                confidence=0.5,
            )

    def test_confidence_must_be_between_0_and_1(self):
        """Test confidence must be in [0, 1] range."""
        with pytest.raises(ValidationError):
            PredictionOutput(
                prediction=1,
                probability=0.8,
                decision="APPROVED",
                confidence=1.5,
            )

    def test_version_optional(self):
        """Test version is optional."""
        output = PredictionOutput(
            prediction=1,
            probability=0.9,
            decision="APPROVED",
            confidence=0.9,
        )

        assert output.version is None

    def test_approved_output(self):
        """Test APPROVED prediction output."""
        output = PredictionOutput(
            prediction=1,
            probability=0.95,
            decision="APPROVED",
            confidence=0.95,
        )

        assert output.prediction == 1
        assert output.decision == "APPROVED"

    def test_rejected_output(self):
        """Test REJECTED prediction output."""
        output = PredictionOutput(
            prediction=0,
            probability=0.15,
            decision="REJECTED",
            confidence=0.85,
        )

        assert output.prediction == 0
        assert output.decision == "REJECTED"

    def test_output_json_schema(self):
        """Test PredictionOutput has json_schema_extra."""
        schema = PredictionOutput.model_json_schema()
        assert "properties" in schema
