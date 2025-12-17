"""
Custom exceptions for Dream Central Storage (Story 2.2).

Provides:
- PermissionDeniedException for authorization failures (Task 5)
- Standardized error response format

References:
- AC: #7 (403 Forbidden with error_code)
- AC: #8 (audit logging on denial)
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class PermissionDeniedException(HTTPException):
    """
    Exception raised when user lacks permission to access a resource.

    Returns 403 Forbidden with standardized error format (AC: #7):
    {
        "error_code": "PERMISSION_DENIED",
        "message": "...",
        "details": {...},
        "timestamp": "..."
    }

    Also logs the denial for audit trail (AC: #8).
    """

    def __init__(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID | None,
        action: str,
        reason: str,
        request_id: str | None = None,
    ):
        """
        Initialize PermissionDeniedException.

        Args:
            user_id: ID of the user who was denied
            resource_type: Type of resource (e.g., "admin_endpoint", "asset")
            resource_id: ID of specific resource (None for endpoint-level denials)
            action: Action attempted (e.g., "access", "delete", "update")
            reason: Human-readable reason for denial
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "PERMISSION_DENIED",
            "message": f"You do not have permission to {action} this {resource_type}",
            "details": {
                "user_id": str(user_id),
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "action": action,
                "reason": reason,
            },
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

        # Log the denial for audit trail (AC: #8)
        logger.warning(
            "Authorization denied",
            extra={
                "user_id": str(user_id),
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "action": action,
                "reason": reason,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class InvalidFileTypeError(HTTPException):
    """
    Exception raised when uploaded file has invalid MIME type (Story 3.1, AC: #10).

    Returns 400 Bad Request with standardized error format:
    {
        "error_code": "INVALID_FILE_TYPE",
        "message": "...",
        "details": {...},
        "timestamp": "..."
    }
    """

    def __init__(
        self,
        mime_type: str,
        allowed_types: list[str],
        request_id: str | None = None,
    ):
        """
        Initialize InvalidFileTypeError.

        Args:
            mime_type: The invalid MIME type that was rejected
            allowed_types: List of allowed MIME types
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "INVALID_FILE_TYPE",
            "message": f"File type '{mime_type}' is not allowed. "
            f"Supported types: {', '.join(allowed_types[:5])}{'...' if len(allowed_types) > 5 else ''}",
            "details": {
                "mime_type": mime_type,
                "allowed_types": allowed_types,
            },
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

        logger.warning(
            "Invalid file type upload rejected",
            extra={
                "mime_type": mime_type,
                "allowed_types": allowed_types,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class FileTooLargeError(HTTPException):
    """
    Exception raised when uploaded file exceeds size limit (Story 3.1, AC: #11).

    Returns 400 Bad Request with standardized error format:
    {
        "error_code": "FILE_TOO_LARGE",
        "message": "...",
        "details": {...},
        "timestamp": "..."
    }
    """

    def __init__(
        self,
        size_bytes: int,
        max_size_bytes: int,
        mime_type: str,
        request_id: str | None = None,
    ):
        """
        Initialize FileTooLargeError.

        Args:
            size_bytes: Actual file size in bytes
            max_size_bytes: Maximum allowed size in bytes
            mime_type: MIME type of the file (determines limit)
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Format sizes for user-friendly message
        size_mb = size_bytes / (1024 * 1024)
        max_size_mb = max_size_bytes / (1024 * 1024)

        detail: dict[str, Any] = {
            "error_code": "FILE_TOO_LARGE",
            "message": f"File size ({size_mb:.1f} MB) exceeds maximum "
            f"allowed size ({max_size_mb:.1f} MB) for {mime_type} files",
            "details": {
                "size_bytes": size_bytes,
                "max_size_bytes": max_size_bytes,
                "size_mb": round(size_mb, 2),
                "max_size_mb": round(max_size_mb, 2),
                "mime_type": mime_type,
            },
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

        logger.warning(
            "File too large upload rejected",
            extra={
                "size_bytes": size_bytes,
                "max_size_bytes": max_size_bytes,
                "mime_type": mime_type,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class InvalidFilenameError(HTTPException):
    """
    Exception for invalid filename (path traversal, invalid characters, etc.).

    Returns 400 Bad Request with INVALID_FILENAME error code.
    """

    def __init__(
        self,
        filename: str,
        reason: str = "Invalid filename",
        request_id: str | None = None,
    ):
        """
        Initialize InvalidFilenameError.

        Args:
            filename: The invalid filename
            reason: Reason for rejection
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "INVALID_FILENAME",
            "message": f"Filename is not valid: {reason}",
            "details": {
                "file_name": filename,
            },
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

        logger.warning(
            "Invalid filename rejected",
            extra={
                "file_name": filename,
                "reason": reason,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class UploadError(HTTPException):
    """
    Generic upload error for unexpected failures.

    Returns 500 Internal Server Error with standardized format.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        """
        Initialize UploadError.

        Args:
            message: Error message
            details: Additional error details
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "UPLOAD_ERROR",
            "message": message,
            "details": details,
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )

        logger.error(
            "Upload error",
            extra={
                "error_msg": message,
                "details": details,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )
