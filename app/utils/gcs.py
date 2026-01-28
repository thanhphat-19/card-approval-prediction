"""Google Cloud Storage authentication utilities."""

import os

from loguru import logger


def setup_gcs_credentials(credentials_path: str) -> bool:
    """
    Setup GCS authentication using service account credentials.

    Args:
        credentials_path: Path to the GCP service account JSON key file.

    Returns:
        True if credentials were set up successfully, False otherwise.
    """
    if not credentials_path:
        logger.info("No GCS credentials specified - using default authentication")
        return False

    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        logger.info(f"Using GCS credentials from: {credentials_path}")
        return True

    logger.warning(f"GCS credentials file not found: {credentials_path}")
    return False
