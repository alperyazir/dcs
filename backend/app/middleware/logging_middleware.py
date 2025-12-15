"""Request/Response logging middleware.

Logs all incoming requests and outgoing responses with timing information,
request IDs, and user context when available.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.logging_config import get_logger

# Get the application logger
logger = get_logger("app.middleware.logging")

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs HTTP requests and responses.

    Logs:
    - Incoming requests: method, path, request_id, user_id (if authenticated)
    - Outgoing responses: status_code, duration_ms, request_id

    Security notes:
    - Does NOT log request/response bodies (may contain sensitive data)
    - Does NOT log authentication headers
    - User ID is extracted from JWT claims when available
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and log request/response details."""
        # Get request ID from state (set by RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", None)

        # Extract user_id from request if available (set by auth middleware)
        user_id = self._get_user_id(request)

        # Record start time
        start_time = time.perf_counter()

        # Log incoming request
        self._log_request(request, request_id, user_id)

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log outgoing response
        self._log_response(request, response, request_id, duration_ms)

        return response

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request if available.

        User ID may be set by authentication middleware or extracted from JWT.
        """
        # Check if auth middleware set user_id in state
        if hasattr(request.state, "user_id"):
            return str(request.state.user_id)

        # Check if current_user is set (FastAPI dependency pattern)
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "id"):
                return str(user.id)

        return None

    def _log_request(
        self, request: Request, request_id: str | None, user_id: str | None
    ) -> None:
        """Log incoming request details."""
        context: dict[str, Any] = {
            "method": request.method,
            "path": request.url.path,
        }

        # Add query string if present (but not sensitive params)
        if request.url.query:
            # Filter out potentially sensitive params
            context["query"] = self._sanitize_query(str(request.url.query))

        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "context": context,
            },
        )

    def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str | None,
        duration_ms: float,
    ) -> None:
        """Log outgoing response details."""
        context: dict[str, Any] = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Use appropriate log level based on status code
        if response.status_code >= 500:
            logger.error(
                "Request completed",
                extra={"request_id": request_id, "context": context},
            )
        elif response.status_code >= 400:
            logger.warning(
                "Request completed",
                extra={"request_id": request_id, "context": context},
            )
        else:
            logger.info(
                "Request completed",
                extra={"request_id": request_id, "context": context},
            )

    def _sanitize_query(self, query: str) -> str:
        """Remove potentially sensitive query parameters.

        Filters out common sensitive parameter names like password, token, etc.
        """
        sensitive_params = {"password", "token", "secret", "key", "auth", "credential"}
        parts = query.split("&")
        sanitized = []

        for part in parts:
            if "=" in part:
                key = part.split("=")[0].lower()
                if any(s in key for s in sensitive_params):
                    sanitized.append(f"{part.split('=')[0]}=[REDACTED]")
                else:
                    sanitized.append(part)
            else:
                sanitized.append(part)

        return "&".join(sanitized)
