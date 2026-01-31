"""
Unit tests for app/core/logging.py module.
"""

import json
import sys
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, patch

from app.core.logging import json_serializer, json_sink, setup_logging


class TestJsonSerializer:
    """Tests for the json_serializer function."""

    def test_serializes_basic_log_record(self):
        """Test serialization of basic log record."""
        mock_record = {
            "time": datetime(2025, 1, 15, 10, 30, 45, 123456),
            "level": MagicMock(name="INFO"),
            "message": "Test message",
            "name": "test_module",
            "function": "test_func",
            "line": 42,
            "exception": None,
            "extra": {},
        }
        mock_record["level"].name = "INFO"

        result = json_serializer(mock_record)
        parsed = json.loads(result)

        assert parsed["time"] == "2025-01-15T10:30:45.123456Z"
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["name"] == "test_module"
        assert parsed["function"] == "test_func"
        assert parsed["line"] == 42

    def test_serializes_with_exception(self):
        """Test serialization includes exception info."""
        mock_record = {
            "time": datetime(2025, 1, 15, 10, 30, 45, 0),
            "level": MagicMock(name="ERROR"),
            "message": "Error occurred",
            "name": "test_module",
            "function": "test_func",
            "line": 100,
            "exception": "ValueError: test error",
            "extra": {},
        }
        mock_record["level"].name = "ERROR"

        result = json_serializer(mock_record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert parsed["exception"] == "ValueError: test error"

    def test_serializes_with_extra_fields(self):
        """Test serialization includes extra fields."""
        mock_record = {
            "time": datetime(2025, 1, 15, 10, 30, 45, 0),
            "level": MagicMock(name="DEBUG"),
            "message": "Debug message",
            "name": "test_module",
            "function": "test_func",
            "line": 50,
            "exception": None,
            "extra": {"user_id": 123, "request_id": "abc-123"},
        }
        mock_record["level"].name = "DEBUG"

        result = json_serializer(mock_record)
        parsed = json.loads(result)

        assert "extra" in parsed
        assert parsed["extra"]["user_id"] == 123
        assert parsed["extra"]["request_id"] == "abc-123"

    def test_output_is_valid_json(self):
        """Test output is always valid JSON."""
        mock_record = {
            "time": datetime(2025, 1, 15, 10, 30, 45, 0),
            "level": MagicMock(name="WARNING"),
            "message": 'Message with "quotes" and special chars: \n\t',
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": None,
            "extra": {},
        }
        mock_record["level"].name = "WARNING"

        result = json_serializer(mock_record)

        # Should not raise JSONDecodeError
        parsed = json.loads(result)
        assert isinstance(parsed, dict)


class TestJsonSink:
    """Tests for the json_sink function."""

    def test_writes_to_stdout(self):
        """Test json_sink writes to stdout."""
        mock_message = MagicMock()
        mock_message.record = {
            "time": datetime(2025, 1, 15, 10, 30, 45, 0),
            "level": MagicMock(name="INFO"),
            "message": "Test",
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": None,
            "extra": {},
        }
        mock_message.record["level"].name = "INFO"

        captured = StringIO()
        with patch.object(sys, "stdout", captured):
            json_sink(mock_message)

        output = captured.getvalue()
        assert output.endswith("\n")
        # Should be valid JSON
        parsed = json.loads(output.strip())
        assert parsed["message"] == "Test"


class TestSetupLogging:
    """Tests for the setup_logging function."""

    @patch("app.core.logging.logger")
    @patch("app.core.logging.get_settings")
    def test_setup_logging_text_format(self, mock_get_settings, mock_logger):
        """Test setup_logging configures text format."""
        mock_settings = MagicMock()
        mock_settings.LOG_FORMAT = "text"
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOG_FILE = "logs/test.log"
        mock_get_settings.return_value = mock_settings

        setup_logging()

        # Should remove default handler
        mock_logger.remove.assert_called_once()
        # Should add handlers (at least 2: console + file)
        assert mock_logger.add.call_count >= 2

    @patch("app.core.logging.logger")
    @patch("app.core.logging.get_settings")
    def test_setup_logging_json_format(self, mock_get_settings, mock_logger):
        """Test setup_logging configures JSON format for Kubernetes."""
        mock_settings = MagicMock()
        mock_settings.LOG_FORMAT = "json"
        mock_settings.LOG_LEVEL = "DEBUG"
        mock_settings.LOG_FILE = "logs/test.log"
        mock_get_settings.return_value = mock_settings

        setup_logging()

        mock_logger.remove.assert_called_once()
        # Should add JSON sink for Kubernetes
        assert mock_logger.add.call_count >= 2

    @patch("app.core.logging.logger")
    @patch("app.core.logging.settings")
    def test_setup_logging_respects_log_level(self, mock_settings, mock_logger):
        """Test setup_logging uses configured log level."""
        mock_settings.LOG_FORMAT = "text"
        mock_settings.LOG_LEVEL = "WARNING"
        mock_settings.LOG_FILE = "logs/test.log"

        setup_logging()

        # Check that log level is passed to add calls
        add_calls = mock_logger.add.call_args_list
        for call in add_calls:
            _, kwargs = call
            if "level" in kwargs:
                assert kwargs["level"] == "WARNING"
