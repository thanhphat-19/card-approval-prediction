"""
Centralized logging configuration using loguru
"""

import sys
from pathlib import Path

from loguru import logger

# Remove default handler
logger.remove()

# Add console handler with custom format
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",  # noqa: E501
    level="INFO",
    colorize=True,
)


def setup_file_logging(log_file: str, level: str = "DEBUG"):
    """
    Add file logging handler

    Args:
        log_file: Path to log file
        level: Logging level (default: DEBUG)
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",  # noqa: E501
        level=level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
    logger.info(f"File logging enabled: {log_file}")


__all__ = ["logger", "setup_file_logging"]
