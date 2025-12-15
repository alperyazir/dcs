"""Common schemas used across the application."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response schema with request tracing.

    All API error responses include a request_id for debugging purposes.
    This allows correlating error responses with log entries.
    """

    error_code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "error_code": "ASSET_NOT_FOUND",
                "message": "Asset with ID 12345 does not exist",
                "details": {"asset_id": "12345"},
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-15T10:30:00Z",
            }
        }
    }
