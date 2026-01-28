"""Prediction API endpoints.

Note: These endpoints use synchronous functions because the underlying
operations (MLflow, pandas, model inference) are blocking I/O.
FastAPI will automatically run sync endpoints in a thread pool.
"""

from typing import Dict

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.schemas.prediction import PredictionInput, PredictionOutput
from app.services.model_service import ModelService, get_model_service
from app.services.preprocessing_service import get_preprocessing_service

router = APIRouter(prefix="/api/v1", tags=["Predictions"])


@router.post("/predict", response_model=PredictionOutput)
def predict(
    input_data: PredictionInput,
    model_service: ModelService = Depends(get_model_service),
) -> PredictionOutput:
    """Make credit card approval prediction."""
    try:
        logger.info(f"Prediction request received for customer ID: {input_data.ID}")

        # Preprocess input data
        df_processed = _preprocess_input(input_data, model_service.run_id)

        # Make prediction
        prediction = _get_prediction(model_service, df_processed)

        # Get probabilities
        prob_approved, confidence = _get_probabilities(model_service, df_processed, prediction)

        # Build response
        decision = "APPROVED" if prediction == 1 else "REJECTED"

        logger.info(
            f"Prediction completed: customer_id={input_data.ID}, "
            f"decision={decision}, probability={prob_approved:.3f}, "
            f"income={input_data.AMT_INCOME_TOTAL}"
        )

        return PredictionOutput(
            prediction=prediction,
            probability=prob_approved,
            decision=decision,
            confidence=confidence,
            version=model_service.get_model_info()["version"],
        )

    except Exception as e:
        logger.error(f"Prediction failed for customer ID {input_data.ID}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}") from e


def _preprocess_input(input_data: PredictionInput, run_id: str) -> pd.DataFrame:
    """Preprocess input data for model inference."""
    preprocessing_service = get_preprocessing_service(run_id=run_id)
    df = pd.DataFrame([input_data.model_dump()])
    return preprocessing_service.preprocess(df)


def _get_prediction(model_service: ModelService, df_processed: pd.DataFrame) -> int:
    """Get model prediction."""
    prediction_result = model_service.predict(df_processed)
    return int(prediction_result[0])


def _get_probabilities(
    model_service: ModelService,
    df_processed: pd.DataFrame,
    prediction: int,
) -> tuple[float, float]:
    """
    Get prediction probabilities.

    Returns:
        Tuple of (probability_approved, confidence).
    """
    proba_result = model_service.predict_proba(df_processed)

    if proba_result is not None:
        # proba_result shape: (n_samples, n_classes) -> [[prob_class_0, prob_class_1]]
        prob_approved = float(proba_result[0][1])  # Probability of class 1 (Approved)
        confidence = float(max(proba_result[0]))  # Confidence = max probability
    else:
        # Fallback if predict_proba not available
        prob_approved = float(prediction)
        confidence = 1.0

    return prob_approved, confidence


@router.post("/reload-model")
def reload_model(
    model_service: ModelService = Depends(get_model_service),
) -> Dict[str, object]:
    """
    Reload model from MLflow registry.

    Useful after training a new model version.
    """
    try:
        logger.info("Model reload requested")
        model_service.reload_model()
        model_info = model_service.get_model_info()

        return {
            "status": "success",
            "message": "Model reloaded successfully",
            "model_info": model_info,
        }
    except Exception as e:
        logger.error(f"Model reload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}") from e


@router.get("/model-info")
def get_model_info(
    model_service: ModelService = Depends(get_model_service),
) -> Dict[str, object]:
    """Get current model information."""
    return model_service.get_model_info()
