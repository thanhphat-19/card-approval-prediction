"""
Unit tests for app/utils/gcs.py module.
"""

import os
from unittest.mock import patch

from app.utils.gcs import setup_gcs_credentials


class TestSetupGcsCredentials:
    """Tests for setup_gcs_credentials function."""

    def test_empty_credentials_path(self):
        """Test with empty credentials path returns False."""
        result = setup_gcs_credentials("")

        assert result is False

    def test_none_credentials_path(self):
        """Test with None credentials path returns False."""
        result = setup_gcs_credentials(None)

        assert result is False

    def test_nonexistent_file(self):
        """Test with non-existent file returns False."""
        result = setup_gcs_credentials("/path/to/nonexistent/credentials.json")

        assert result is False

    @patch("os.path.exists")
    def test_existing_file_sets_env_var(self, mock_exists):
        """Test with existing file sets environment variable."""
        mock_exists.return_value = True
        credentials_path = "/path/to/credentials.json"

        # Clear env var if exists
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        result = setup_gcs_credentials(credentials_path)

        assert result is True
        assert os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") == credentials_path

    @patch("os.path.exists")
    def test_returns_true_on_success(self, mock_exists):
        """Test returns True when credentials are set successfully."""
        mock_exists.return_value = True

        result = setup_gcs_credentials("/valid/path.json")

        assert result is True

    @patch("os.path.exists")
    def test_logs_success_message(self, mock_exists):
        """Test logs message on successful setup."""
        mock_exists.return_value = True

        with patch("app.utils.gcs.logger") as mock_logger:
            setup_gcs_credentials("/valid/credentials.json")
            mock_logger.info.assert_called()

    def test_logs_warning_for_missing_file(self):
        """Test logs warning when file doesn't exist."""
        with patch("app.utils.gcs.logger") as mock_logger:
            setup_gcs_credentials("/nonexistent/path.json")
            mock_logger.warning.assert_called()

    def test_logs_info_for_empty_path(self):
        """Test logs info when no credentials specified."""
        with patch("app.utils.gcs.logger") as mock_logger:
            setup_gcs_credentials("")
            mock_logger.info.assert_called()
