"""
Unit tests for training/src/utils/logger.py module.
"""

from unittest.mock import patch

from training.src.utils.logger import logger, setup_file_logging  # noqa: E402


class TestLogger:
    """Tests for logger configuration."""

    def test_logger_exists(self):
        """Test logger is available for import."""
        assert logger is not None

    def test_logger_has_stderr_handler(self):
        """Test logger has stderr handler configured."""
        # Logger should have at least one handler
        assert len(logger._core.handlers) > 0


class TestSetupFileLogging:
    """Tests for setup_file_logging function."""

    @patch("training.src.utils.logger.logger")
    def test_creates_log_directory(self, mock_logger, tmp_path):
        """Test setup_file_logging creates parent directory."""
        log_file = tmp_path / "logs" / "test.log"

        setup_file_logging(str(log_file))

        # Directory should be created
        assert log_file.parent.exists()

    @patch("training.src.utils.logger.logger")
    def test_adds_file_handler(self, mock_logger, tmp_path):
        """Test setup_file_logging adds file handler."""
        log_file = tmp_path / "test.log"

        setup_file_logging(str(log_file))

        # Logger.add should be called
        mock_logger.add.assert_called_once()

    @patch("training.src.utils.logger.logger")
    def test_uses_custom_level(self, mock_logger, tmp_path):
        """Test setup_file_logging respects custom level."""
        log_file = tmp_path / "test.log"

        setup_file_logging(str(log_file), level="WARNING")

        # Check level parameter
        call_kwargs = mock_logger.add.call_args[1]
        assert call_kwargs["level"] == "WARNING"

    @patch("training.src.utils.logger.logger")
    def test_default_level_is_debug(self, mock_logger, tmp_path):
        """Test default logging level is DEBUG."""
        log_file = tmp_path / "test.log"

        setup_file_logging(str(log_file))

        # Check default level
        call_kwargs = mock_logger.add.call_args[1]
        assert call_kwargs["level"] == "DEBUG"

    @patch("training.src.utils.logger.logger")
    def test_logs_file_path(self, mock_logger, tmp_path):
        """Test setup_file_logging logs the file path."""
        log_file = tmp_path / "test.log"

        setup_file_logging(str(log_file))

        # Logger.info should be called with file path
        mock_logger.info.assert_called_once()
        assert str(log_file) in mock_logger.info.call_args[0][0]
