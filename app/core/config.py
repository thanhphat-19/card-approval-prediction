"""Application configuration settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # App Info
    APP_NAME: str = "Card Approval API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://127.0.0.1:5000"
    MODEL_NAME: str = "card_approval_model"
    MODEL_STAGE: str = "Production"

    # Model Loading - if MODEL_PATH is set, load from local path (embedded in image)
    # Otherwise, fall back to loading from MLflow at runtime
    MODEL_PATH: str = ""  # e.g., "/app/models" when embedded in Docker image

    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_FORMAT: str = "text"

    # CORS - comma-separated list of allowed origins (use "*" for development only)
    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
