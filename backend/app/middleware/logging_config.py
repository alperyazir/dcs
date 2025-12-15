"""Structured JSON logging configuration.

Provides:
- JSONFormatter: Custom formatter that outputs logs as JSON
- setup_logging: Configure the root logger with JSON formatting
- Context injection for request_id, user_id, and custom context
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Custom log formatter that outputs JSON structured logs.

    Output format:
    {
        "timestamp": "2025-12-15T10:30:00.123Z",
        "level": "INFO",
        "message": "Request completed",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "660e8400-e29b-41d4-a716-446655440001",
        "context": {"method": "GET", "path": "/api/v1/assets"},
        "exception": "Traceback..." (only for errors with exc_info)
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        # Build the log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[
                :-3
            ]
            + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add optional fields from extra
        if hasattr(record, "request_id") and record.request_id:
            log_entry["request_id"] = record.request_id

        if hasattr(record, "user_id") and record.user_id:
            log_entry["user_id"] = record.user_id

        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context

        # Add exception info if present (for ERROR/CRITICAL with exc_info)
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class TextFormatter(logging.Formatter):
    """Standard text formatter for development/debugging.

    Output format:
    2025-12-15 10:30:00.123 | INFO | [request-id] message
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        request_id = getattr(record, "request_id", "-")

        base_msg = (
            f"{timestamp} | {record.levelname:8} | [{request_id}] {record.getMessage()}"
        )

        # Add exception info if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"

        return base_msg


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    logger_name: str = "app",
) -> logging.Logger:
    """Configure and return the application logger.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format - "json" for structured logs, "text" for readable
        logger_name: Name for the logger

    Returns:
        Configured logger instance
    """
    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    logger.handlers.clear()  # Remove any existing handlers

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    # Set formatter based on format preference
    if log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    logger.addHandler(handler)

    # Don't propagate to root logger to avoid duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance with the application configuration.

    Args:
        name: Optional logger name. If None, returns the root app logger.

    Returns:
        Logger instance
    """
    from app.core.config import settings

    if name is None:
        name = "app"

    return setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        logger_name=name,
    )
