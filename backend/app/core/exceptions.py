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
