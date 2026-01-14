"""Prediction API endpoints."""
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.schemas.prediction import PredictionInput, PredictionOutput
from app.services.model_service import ModelService, get_model_service
from app.services.preprocessing_service import get_preprocessing_service

router = APIRouter(prefix="/api/v1", tags=["Predictions"])


@router.post("/predict", response_model=PredictionOutput)
async def predict(
    input_data: PredictionInput,
    model_service: ModelService = Depends(get_model_service),
):
    """Make credit card approval prediction"""
    try:
        logger.info(f"Prediction request received for customer ID: {input_data.ID}")

        # Preprocess
        preprocessing_service = get_preprocessing_service(run_id=model_service.run_id)
        df = pd.DataFrame([input_data.model_dump()])
        df_processed = preprocessing_service.preprocess(df)

        # Predict
        prediction_result = model_service.predict(df_processed)
        if hasattr(prediction_result, "__iter__"):
            prediction = int(prediction_result[0])
        else:
            prediction = int(prediction_result)

        # Format response
        # Label mapping from training:
        # Label 1 = Good credit (STATUS 0,C,X) → APPROVED
        # Label 0 = Bad credit (STATUS 1-5) → REJECTED
        decision = "APPROVED" if prediction == 1 else "REJECTED"

        logger.info(
            f"Prediction completed: customer_id={input_data.ID}, "
            f"decision={decision}, income={input_data.AMT_INCOME_TOTAL}"
        )

        return PredictionOutput(
            prediction=prediction,
            probability=float(prediction),  # Binary: 0.0 or 1.0
            decision=decision,
            confidence=1.0,  # Always confident in binary predictions
            version=model_service.get_model_info()["version"],
        )

    except Exception as e:
        logger.error(f"Prediction failed for customer ID {input_data.ID}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}") from e


@router.post("/reload-model")
async def reload_model(model_service: ModelService = Depends(get_model_service)):
    """
    Reload model from MLflow registry

    Useful after training a new model version
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
async def get_model_info(model_service: ModelService = Depends(get_model_service)):
    """Get current model information"""
    return model_service.get_model_info()
