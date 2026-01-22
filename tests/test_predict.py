"""
Prediction endpoint tests for Card Approval Prediction API.
"""


class TestPredictEndpoint:
    """Tests for the prediction endpoint."""

    def test_predict_returns_200(self, client, sample_prediction_input):
        """Test prediction endpoint returns 200 with valid input."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        assert response.status_code == 200

    def test_predict_returns_prediction(self, client, sample_prediction_input):
        """Test prediction endpoint returns prediction field."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        data = response.json()

        assert "prediction" in data
        assert data["prediction"] in [0, 1]

    def test_predict_returns_probability(self, client, sample_prediction_input):
        """Test prediction endpoint returns probability."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        data = response.json()

        assert "probability" in data
        assert 0.0 <= data["probability"] <= 1.0

    def test_predict_returns_decision(self, client, sample_prediction_input):
        """Test prediction endpoint returns human-readable decision."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        data = response.json()

        assert "decision" in data
        assert data["decision"] in ["APPROVED", "REJECTED"]

    def test_predict_returns_confidence(self, client, sample_prediction_input):
        """Test prediction endpoint returns confidence score."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        data = response.json()

        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_returns_timestamp(self, client, sample_prediction_input):
        """Test prediction endpoint returns timestamp."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        data = response.json()

        assert "timestamp" in data

    def test_predict_decision_matches_prediction(self, client, sample_prediction_input):
        """Test that decision text matches prediction value."""
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        data = response.json()

        if data["prediction"] == 1:
            assert data["decision"] == "APPROVED"
        else:
            assert data["decision"] == "REJECTED"


class TestPredictValidation:
    """Tests for prediction input validation."""

    def test_predict_missing_required_field(self, client, sample_prediction_input):
        """Test prediction fails with missing required field."""
        del sample_prediction_input["CODE_GENDER"]
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        assert response.status_code == 422  # Validation error

    def test_predict_invalid_gender(self, client, sample_prediction_input):
        """Test prediction with invalid gender value."""
        sample_prediction_input["CODE_GENDER"] = "X"
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        # Should either accept or return 422
        assert response.status_code in [200, 422]

    def test_predict_negative_income(self, client, sample_prediction_input):
        """Test prediction with negative income."""
        sample_prediction_input["AMT_INCOME_TOTAL"] = -1000
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        # API should handle this gracefully
        assert response.status_code in [200, 422]

    def test_predict_empty_body(self, client):
        """Test prediction with empty body."""
        response = client.post("/api/v1/predict", json={})
        assert response.status_code == 422

    def test_predict_invalid_json(self, client):
        """Test prediction with invalid JSON."""
        response = client.post(
            "/api/v1/predict",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestPredictPerformance:
    """Performance-related tests for prediction endpoint."""

    def test_predict_response_time(self, client, sample_prediction_input):
        """Test prediction response time is reasonable."""
        import time

        start = time.time()
        response = client.post("/api/v1/predict", json=sample_prediction_input)
        duration = time.time() - start

        assert response.status_code == 200
        # Should respond within 5 seconds
        assert duration < 5.0

    def test_predict_multiple_requests(self, client, sample_prediction_input):
        """Test multiple sequential predictions."""
        for _ in range(5):
            response = client.post("/api/v1/predict", json=sample_prediction_input)
            assert response.status_code == 200


class TestPredictDifferentProfiles:
    """Test predictions with different applicant profiles."""

    def test_high_risk_applicant(self, client, high_risk_input):
        """Test prediction for high-risk applicant."""
        response = client.post("/api/v1/predict", json=high_risk_input)
        assert response.status_code == 200
        data = response.json()

        assert "prediction" in data
        assert "decision" in data

    def test_different_income_types(self, client, sample_prediction_input):
        """Test predictions with different income types."""
        income_types = ["Working", "Commercial associate", "Pensioner", "State servant"]

        for income_type in income_types:
            sample_prediction_input["NAME_INCOME_TYPE"] = income_type
            response = client.post("/api/v1/predict", json=sample_prediction_input)
            assert response.status_code == 200

    def test_different_education_levels(self, client, sample_prediction_input):
        """Test predictions with different education levels."""
        education_levels = [
            "Higher education",
            "Secondary / secondary special",
            "Incomplete higher",
            "Lower secondary",
        ]

        for edu in education_levels:
            sample_prediction_input["NAME_EDUCATION_TYPE"] = edu
            response = client.post("/api/v1/predict", json=sample_prediction_input)
            assert response.status_code == 200
