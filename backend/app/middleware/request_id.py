"""Request ID middleware for request tracing.

Generates a unique UUID v4 for each request and stores it in request.state.
The request ID is also added to response headers for debugging.
"""

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that generates and propagates a unique request ID.

    If the client provides an X-Request-ID header, it is preserved.
    Otherwise, a new UUID v4 is generated.

    The request ID is:
    - Stored in request.state.request_id for use in the application
    - Added to response headers as X-Request-ID for debugging
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and add request ID."""
        # Use client-provided request ID or generate new one
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for use by routes and other middleware
        request.state.request_id = request_id

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id(request: Request) -> str | None:
    """Helper function to get request ID from request state.

    Args:
        request: The current request object

    Returns:
        The request ID if available, None otherwise
    """
    return getattr(request.state, "request_id", None)
