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


class AssetNotFoundError(HTTPException):
    """
    Exception raised when requested asset does not exist (Story 3.2, AC: #8).

    Returns 404 Not Found - prevents asset enumeration attacks.
    """

    def __init__(
        self,
        asset_id: UUID | str,
        request_id: str | None = None,
    ):
        """
        Initialize AssetNotFoundError.

        Args:
            asset_id: ID of the asset that was not found
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "ASSET_NOT_FOUND",
            "message": "Asset not found",
            "details": {
                "asset_id": str(asset_id),
            },
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

        logger.info(
            "Asset not found",
            extra={
                "asset_id": str(asset_id),
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class AssetAccessDeniedError(HTTPException):
    """
    Exception raised when user lacks permission to access an asset (Story 3.2, AC: #8).

    Returns 403 Forbidden with standardized error format.
    """

    def __init__(
        self,
        asset_id: UUID | str,
        user_id: UUID | str,
        reason: str = "You do not have permission to access this asset",
        request_id: str | None = None,
    ):
        """
        Initialize AssetAccessDeniedError.

        Args:
            asset_id: ID of the asset being accessed
            user_id: ID of the user denied access
            reason: Reason for denial
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "PERMISSION_DENIED",
            "message": reason,
            "details": {
                "asset_id": str(asset_id),
            },
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

        logger.warning(
            "Asset access denied",
            extra={
                "asset_id": str(asset_id),
                "user_id": str(user_id),
                "reason": reason,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class DangerousFileError(HTTPException):
    """
    Exception raised when file contains dangerous patterns (Story 3.4, AC: #9).

    Returns 400 Bad Request with standardized error format.
    Detects: double extensions, null bytes, unicode tricks, executable formats.
    """

    def __init__(
        self,
        filename: str,
        pattern_type: str,
        reason: str,
        request_id: str | None = None,
    ):
        """
        Initialize DangerousFileError.

        Args:
            filename: The dangerous filename
            pattern_type: Type of pattern detected (e.g., "double_extension", "null_byte")
            reason: Human-readable explanation
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "DANGEROUS_FILE_DETECTED",
            "message": f"File rejected for security reasons: {reason}",
            "details": {
                "filename": filename,
                "pattern_type": pattern_type,
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
            "Dangerous file pattern detected",
            extra={
                "file_name": filename,
                "pattern_type": pattern_type,
                "reason": reason,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class ExtensionMismatchError(HTTPException):
    """
    Exception raised when file extension doesn't match Content-Type (Story 3.4, AC: #2).

    Returns 400 Bad Request - prevents Content-Type spoofing attacks.
    """

    def __init__(
        self,
        filename: str,
        extension: str,
        claimed_mime: str,
        expected_mimes: list[str],
        request_id: str | None = None,
    ):
        """
        Initialize ExtensionMismatchError.

        Args:
            filename: The filename with mismatched extension
            extension: File extension found
            claimed_mime: MIME type from Content-Type header
            expected_mimes: Expected MIME types for the extension
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "EXTENSION_MISMATCH",
            "message": f"File extension '{extension}' does not match Content-Type '{claimed_mime}'. "
            f"Expected types for {extension}: {', '.join(expected_mimes)}",
            "details": {
                "filename": filename,
                "extension": extension,
                "claimed_mime": claimed_mime,
                "expected_mimes": expected_mimes,
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
            "Extension-MIME mismatch detected (possible spoofing)",
            extra={
                "file_name": filename,
                "extension": extension,
                "claimed_mime": claimed_mime,
                "expected_mimes": expected_mimes,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )


class ExecutableDetectedError(HTTPException):
    """
    Exception raised when file is detected as executable format (Story 3.4, AC: #10).

    Returns 400 Bad Request - executables are ALWAYS rejected regardless of Content-Type.
    """

    def __init__(
        self,
        format_name: str,
        claimed_mime: str,
        request_id: str | None = None,
    ):
        """
        Initialize ExecutableDetectedError.

        Args:
            format_name: Detected executable format (e.g., "Windows PE", "Linux ELF")
            claimed_mime: Claimed MIME type from upload
            request_id: Optional request ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        detail: dict[str, Any] = {
            "error_code": "EXECUTABLE_DETECTED",
            "message": f"File appears to be an executable ({format_name}). "
            "Executable files are not allowed for security reasons.",
            "details": {
                "detected_format": format_name,
                "claimed_mime": claimed_mime,
            },
            "timestamp": timestamp,
        }

        if request_id:
            detail["request_id"] = request_id

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

        logger.error(
            "SECURITY: Executable file upload blocked",
            extra={
                "format_name": format_name,
                "claimed_mime": claimed_mime,
                "request_id": request_id,
                "timestamp": timestamp,
            },
        )
