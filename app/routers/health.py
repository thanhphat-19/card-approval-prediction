"""Health check API endpoints.
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter
from loguru import logger

from app.core.config import get_settings
from app.schemas.health import HealthResponse
from app.utils.mlflow_helpers import check_mlflow_connection

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns system health status including:
    - Application status
    - MLflow connection status
    """
    logger.info("Health check requested")

    # Check MLflow connection
    mlflow_connected = check_mlflow_connection(settings.MLFLOW_TRACKING_URI)
    if mlflow_connected:
        logger.debug("MLflow connection: OK")

    # Determine overall status
    status = "healthy" if mlflow_connected else "degraded"

    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        mlflow_connected=mlflow_connected,
    )


@router.get("/ready")
def readiness_check() -> Dict[str, str]:
    """
    Readiness check for Kubernetes.

    Returns 200 if service is ready to accept traffic.
    """
    return {"status": "ready"}


@router.get("/live")
def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Kubernetes.

    Returns 200 if service is alive.
    """
    return {"status": "alive"}
