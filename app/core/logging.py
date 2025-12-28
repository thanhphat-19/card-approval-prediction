"""Logging configuration for the application."""
import sys

from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """Configure logging for the application"""

    # Remove default handler
    logger.remove()

    # Console handler (colored)
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # File handler (for production logs)
    logger.add(
        settings.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=settings.LOG_LEVEL,
        rotation="500 MB",
        retention="10 days",
        compression="zip",
    )

    logger.info(f"Logging configured: level={settings.LOG_LEVEL}, file={settings.LOG_FILE}")
