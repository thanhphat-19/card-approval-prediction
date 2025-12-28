"""Health check API endpoints."""
from datetime import datetime

import mlflow
from fastapi import APIRouter
from loguru import logger

from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns system health status including:
    - Application status
    - MLflow connection status
    - Database connection status
    """
    logger.info("Health check requested")

    # Check MLflow connection
    mlflow_connected = False
    try:
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.search_experiments(max_results=1)
        mlflow_connected = True
        logger.debug("MLflow connection: OK")
    except (ConnectionError, mlflow.exceptions.MlflowException) as e:
        logger.warning(f"MLflow connection failed: {e}")

    # Determine overall status
    status = "healthy" if mlflow_connected else "degraded"

    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        mlflow_connected=mlflow_connected,
        database_connected=False,  # Will implement later
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes

    Returns 200 if service is ready to accept traffic
    """
    return {"status": "ready"}
