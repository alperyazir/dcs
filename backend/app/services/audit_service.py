"""
Audit Service for authorization denial logging (Story 2.2, Task 6).

Provides structured logging for authorization denials to support:
- Security auditing and compliance (AC: #8)
- Incident response and investigation
- Access pattern analysis

Uses existing structured logging infrastructure from Story 1.5.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for logging authorization-related events.

    All log entries use structured JSON format with request_id for traceability.
    """

    @staticmethod
    def log_authorization_denial(
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        reason: str,
        ip_address: str | None = None,
        request_id: str | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an authorization denial event.

        Args:
            user_id: ID of the user who was denied
            action: Action attempted (access, delete, update, etc.)
            resource_type: Type of resource (admin_endpoint, asset, etc.)
            resource_id: ID of specific resource (None for endpoint-level)
            reason: Human-readable denial reason
            ip_address: Client IP address
            request_id: Request correlation ID
            additional_context: Extra context for the log entry

        Log Format (JSON):
            {
                "event": "authorization_denied",
                "user_id": "...",
                "action": "...",
                "resource_type": "...",
                "resource_id": "...",
                "ip_address": "...",
                "request_id": "...",
                "reason": "...",
                "timestamp": "..."
            }
        """
        log_data: dict[str, Any] = {
            "event": "authorization_denied",
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "ip_address": ip_address,
            "request_id": request_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if additional_context:
            log_data["context"] = additional_context

        # Use warning level for security-relevant denied access
        logger.warning(
            f"Authorization denied: user={user_id} action={action} "
            f"resource_type={resource_type}",
            extra=log_data,
        )

    @staticmethod
    def log_authorization_success(
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID | None = None,
        request_id: str | None = None,
    ) -> None:
        """
        Log a successful authorization event (for sensitive operations).

        Use sparingly - only for highly sensitive operations where
        success logging is required for compliance.

        Args:
            user_id: ID of the authorized user
            action: Action performed
            resource_type: Type of resource accessed
            resource_id: ID of specific resource
            request_id: Request correlation ID
        """
        log_data = {
            "event": "authorization_success",
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Authorization granted: user={user_id} action={action} "
            f"resource_type={resource_type}",
            extra=log_data,
        )
