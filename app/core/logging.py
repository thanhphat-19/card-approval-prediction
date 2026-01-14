"""Logging configuration for the application."""
import json
import sys

from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def json_serializer(record):
    """Serialize log record to JSON for Loki/Alloy parsing"""
    subset = {
        "time": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "message": record["message"],
        "name": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    # Add exception info if present
    if record["exception"]:
        subset["exception"] = str(record["exception"])
    # Add extra fields
    if record["extra"]:
        subset["extra"] = record["extra"]
    return json.dumps(subset)


def json_sink(message):
    """Custom sink that outputs JSON format"""
    record = message.record
    serialized = json_serializer(record)
    sys.stdout.write(serialized + "\n")
    sys.stdout.flush()


def setup_logging():
    """Configure logging for the application"""

    # Remove default handler
    logger.remove()

    # Check if running in Kubernetes (JSON output for Loki)
    is_kubernetes = settings.LOG_FORMAT == "json"

    if is_kubernetes:
        # JSON handler for Kubernetes/Loki
        logger.add(
            json_sink,
            level=settings.LOG_LEVEL,
            format="{message}",  # Format handled by json_sink
        )
    else:
        # Console handler (colored) for local development
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

    logger.info(
        f"Logging configured: level={settings.LOG_LEVEL}, format={'json' if is_kubernetes else 'text'}"  # noqa: 503
    )
