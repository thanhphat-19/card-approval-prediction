from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # App Info
    APP_NAME: str = "Card Approval API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/db"

    # PostgreSQL credentials
    POSTGRES_DB: str = "mlflow"
    POSTGRES_USER: str = "mlflow"
    POSTGRES_PASSWORD: str = "thanhphat192001"

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://127.0.0.1:5000"
    MODEL_NAME: str = "card_approval_model"
    MODEL_STAGE: str = "Production"

    # Google Cloud (for GCS artifact storage)
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
