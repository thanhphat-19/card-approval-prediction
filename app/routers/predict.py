import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.schemas.prediction import PredictionInput, PredictionOutput
from app.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="/api/v1", tags=["Predictions"])


@router.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput, model_service: ModelService = Depends(get_model_service)):
    """
    Make credit card approval prediction

    - **Input**: Customer data
    - **Output**: Approval decision (APPROVED/REJECTED) with probability
    """
    try:
        logger.info(f"Prediction request for customer ID: {input_data.ID}")

        # Convert input to DataFrame
        df = pd.DataFrame([input_data.model_dump()])

        # Get prediction
        prediction = model_service.predict(df)[0]

        # Get probability if available

        proba = model_service.model.predict_proba(df)[0]
        probability = float(proba[1])  # Probability of approval (class 1)

        # Format response
        decision = "APPROVED" if prediction == 1 else "REJECTED"
        confidence = max(probability, 1 - probability)

        model_info = model_service.get_model_info()

        result = PredictionOutput(
            prediction=int(prediction),
            probability=probability,
            decision=decision,
            confidence=confidence,
            model_version=model_info["version"],
        )

        logger.info(f"Prediction: {decision} (probability={probability:.2%})")
        return result

    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


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

        return {"status": "success", "message": "Model reloaded successfully", "model_info": model_info}
    except Exception as e:
        logger.error(f"Model reload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")


@router.get("/model-info")
async def get_model_info(model_service: ModelService = Depends(get_model_service)):
    """Get current model information"""
    return model_service.get_model_info()
