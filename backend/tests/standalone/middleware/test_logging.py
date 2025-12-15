"""Tests for structured JSON logging.

These tests are standalone and don't require database access.
"""

import json
import logging
from collections.abc import Generator
from io import StringIO
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient


class TestJSONFormatter:
    """Tests for the custom JSON log formatter."""

    @pytest.fixture
    def log_capture(self) -> Generator[tuple[logging.Logger, StringIO], None, None]:
        """Create a logger with StringIO handler to capture output."""
        from app.middleware.logging_config import JSONFormatter

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.addHandler(handler)

        yield logger, stream

        logger.handlers.clear()

    def test_json_format_basic_fields(
        self, log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that log output contains required basic fields."""
        logger, stream = log_capture

        logger.info("Test message")
        stream.seek(0)
        output = stream.read().strip()

        log_entry = json.loads(output)

        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "message" in log_entry
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"

    def test_json_format_timestamp_format(
        self, log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that timestamp is in ISO 8601 format with Z suffix."""
        logger, stream = log_capture

        logger.info("Test message")
        stream.seek(0)
        output = stream.read().strip()

        log_entry = json.loads(output)

        # Timestamp should be ISO format ending with Z
        timestamp = log_entry["timestamp"]
        assert timestamp.endswith("Z")
        assert "T" in timestamp

    def test_json_format_with_request_id(
        self, log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that request_id is included when provided via extra."""
        logger, stream = log_capture

        logger.info("Test message", extra={"request_id": "test-request-id-123"})
        stream.seek(0)
        output = stream.read().strip()

        log_entry = json.loads(output)

        assert "request_id" in log_entry
        assert log_entry["request_id"] == "test-request-id-123"

    def test_json_format_with_user_id(
        self, log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that user_id is included when provided via extra."""
        logger, stream = log_capture

        logger.info("Test message", extra={"user_id": "user-456"})
        stream.seek(0)
        output = stream.read().strip()

        log_entry = json.loads(output)

        assert "user_id" in log_entry
        assert log_entry["user_id"] == "user-456"

    def test_json_format_with_context(
        self, log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that context dict is included when provided via extra."""
        logger, stream = log_capture

        context = {"method": "GET", "path": "/api/v1/assets", "status_code": 200}
        logger.info("Request completed", extra={"context": context})
        stream.seek(0)
        output = stream.read().strip()

        log_entry = json.loads(output)

        assert "context" in log_entry
        assert log_entry["context"]["method"] == "GET"
        assert log_entry["context"]["path"] == "/api/v1/assets"
        assert log_entry["context"]["status_code"] == 200

    def test_json_format_exception_included(
        self, log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that exception info is included for error logs."""
        logger, stream = log_capture

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")

        stream.seek(0)
        output = stream.read().strip()

        log_entry = json.loads(output)

        assert "exception" in log_entry
        assert "ValueError" in log_entry["exception"]
        assert "Test exception" in log_entry["exception"]

    def test_json_format_all_log_levels(
        self, log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that all log levels produce valid JSON."""
        logger, stream = log_capture

        test_cases = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level, level_name in test_cases:
            stream.truncate(0)
            stream.seek(0)
            logger.log(level, f"Test {level_name}")
            stream.seek(0)
            output = stream.read().strip()

            log_entry = json.loads(output)
            assert log_entry["level"] == level_name


class TestTextFormatter:
    """Tests for the TextFormatter class."""

    @pytest.fixture
    def text_log_capture(
        self,
    ) -> Generator[tuple[logging.Logger, StringIO], None, None]:
        """Create a logger with TextFormatter and StringIO handler."""
        from app.middleware.logging_config import TextFormatter

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(TextFormatter())

        logger = logging.getLogger("test_text_logger")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.addHandler(handler)

        yield logger, stream

        logger.handlers.clear()

    def test_text_format_basic_output(
        self, text_log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that TextFormatter produces readable text output."""
        logger, stream = text_log_capture

        logger.info("Test message")
        stream.seek(0)
        output = stream.read().strip()

        # Should contain timestamp, level, and message
        assert "INFO" in output
        assert "Test message" in output
        assert "|" in output  # Delimiter

    def test_text_format_with_request_id(
        self, text_log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that request_id is included in text format."""
        logger, stream = text_log_capture

        logger.info("Test message", extra={"request_id": "test-req-123"})
        stream.seek(0)
        output = stream.read().strip()

        assert "test-req-123" in output

    def test_text_format_with_exception(
        self, text_log_capture: tuple[logging.Logger, StringIO]
    ) -> None:
        """Test that exception info is included in text format."""
        logger, stream = text_log_capture

        try:
            raise ValueError("Text format exception")
        except ValueError:
            logger.exception("Error occurred")

        stream.seek(0)
        output = stream.read().strip()

        assert "ValueError" in output
        assert "Text format exception" in output


class TestLoggingConfiguration:
    """Tests for logging configuration setup."""

    def test_setup_logging_returns_logger(self) -> None:
        """Test that setup_logging returns a configured logger."""
        from app.middleware.logging_config import setup_logging

        logger = setup_logging()
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_respects_log_level(self) -> None:
        """Test that setup_logging sets the correct log level."""
        from app.middleware.logging_config import setup_logging

        logger = setup_logging(log_level="DEBUG")
        assert logger.level == logging.DEBUG

        logger = setup_logging(log_level="WARNING")
        assert logger.level == logging.WARNING

    def test_setup_logging_uses_json_format_by_default(self) -> None:
        """Test that JSON formatting is used by default."""
        from app.middleware.logging_config import JSONFormatter, setup_logging

        logger = setup_logging()

        # Find the handler with JSONFormatter
        has_json_handler = any(
            isinstance(h.formatter, JSONFormatter) for h in logger.handlers
        )
        assert has_json_handler

    def test_setup_logging_uses_text_format(self) -> None:
        """Test that TextFormatter is used when log_format is 'text'."""
        from app.middleware.logging_config import TextFormatter, setup_logging

        logger = setup_logging(log_format="text")

        has_text_handler = any(
            isinstance(h.formatter, TextFormatter) for h in logger.handlers
        )
        assert has_text_handler


class TestGetLogger:
    """Tests for the get_logger convenience function."""

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a configured logger."""
        from app.middleware.logging_config import get_logger

        logger = get_logger("test_get_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_get_logger"

    def test_get_logger_with_none_uses_default_name(self) -> None:
        """Test that get_logger with None uses 'app' as default name."""
        from app.middleware.logging_config import get_logger

        logger = get_logger(None)
        assert logger.name == "app"


class TestLogLevelFromConfig:
    """Tests for log level configuration from environment."""

    def test_get_log_level_from_settings(self) -> None:
        """Test that log level can be retrieved from settings."""
        from app.core.config import settings

        # Settings should have LOG_LEVEL attribute
        assert hasattr(settings, "LOG_LEVEL")
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_get_log_format_from_settings(self) -> None:
        """Test that log format can be retrieved from settings."""
        from app.core.config import settings

        # Settings should have LOG_FORMAT attribute
        assert hasattr(settings, "LOG_FORMAT")
        assert settings.LOG_FORMAT in ["json", "text"]


class TestLoggingMiddleware:
    """Tests for the HTTP request/response logging middleware."""

    @pytest.fixture
    def simple_app(self) -> "FastAPI":
        """Create a simple app with logging middleware."""
        from fastapi import FastAPI
        from starlette.responses import JSONResponse

        from app.middleware.logging_middleware import LoggingMiddleware
        from app.middleware.request_id import RequestIDMiddleware

        test_app = FastAPI()
        # Add middleware in correct order (LIFO - last added runs first on request)
        test_app.add_middleware(LoggingMiddleware)
        test_app.add_middleware(RequestIDMiddleware)

        @test_app.get("/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        @test_app.get("/error")
        async def error_endpoint() -> JSONResponse:
            return JSONResponse(status_code=500, content={"error": "test"})

        return test_app

    @pytest.fixture
    def test_client(self, simple_app: "FastAPI") -> Generator["TestClient", None, None]:
        """Standalone test client."""
        from fastapi.testclient import TestClient

        with TestClient(simple_app) as client:
            yield client

    def test_logging_middleware_allows_request(self, test_client: "TestClient") -> None:
        """Test that logging middleware doesn't block requests."""
        response = test_client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_logging_middleware_preserves_request_id(
        self, test_client: "TestClient"
    ) -> None:
        """Test that request ID is preserved through logging middleware."""
        import uuid

        client_id = str(uuid.uuid4())
        response = test_client.get("/test", headers={"X-Request-ID": client_id})

        assert response.headers["X-Request-ID"] == client_id

    def test_logging_middleware_handles_errors(self, test_client: "TestClient") -> None:
        """Test that logging middleware handles error responses."""
        response = test_client.get("/error")
        assert response.status_code == 500
        # Should still have request ID
        assert "X-Request-ID" in response.headers


class TestSanitizeQuery:
    """Tests for query parameter sanitization."""

    def test_sanitize_password_param(self) -> None:
        """Test that password params are redacted."""
        from app.middleware.logging_middleware import LoggingMiddleware

        middleware = LoggingMiddleware(app=None)  # type: ignore
        result = middleware._sanitize_query("user=john&password=secret123")

        assert "password=[REDACTED]" in result
        assert "secret123" not in result
        assert "user=john" in result

    def test_sanitize_token_param(self) -> None:
        """Test that token params are redacted."""
        from app.middleware.logging_middleware import LoggingMiddleware

        middleware = LoggingMiddleware(app=None)  # type: ignore
        result = middleware._sanitize_query("access_token=abc123&page=1")

        assert "access_token=[REDACTED]" in result
        assert "abc123" not in result
        assert "page=1" in result

    def test_sanitize_preserves_safe_params(self) -> None:
        """Test that safe params are preserved."""
        from app.middleware.logging_middleware import LoggingMiddleware

        middleware = LoggingMiddleware(app=None)  # type: ignore
        result = middleware._sanitize_query("page=1&limit=50&sort=name")

        assert result == "page=1&limit=50&sort=name"
