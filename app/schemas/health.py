"""Health check response schemas."""
from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    timestamp: datetime
    mlflow_connected: bool = False
    database_connected: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-12-13T11:30:00",
                "mlflow_connected": True,
                "database_connected": True,
            }
        }
