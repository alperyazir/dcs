"""
Tenant Context Middleware (Story 2.2, Task 4).

Extracts tenant context from JWT and injects into request.state:
- user_id: UUID of authenticated user
- tenant_id: UUID of user's tenant
- role: User's role string
- bypass_tenant_filter: True for Admin/Supervisor (AC: #2)

References:
- AC: #1 (extract role and tenant_id from JWT)
- AC: #2 (Admin/Supervisor bypass tenant filtering)
"""

import logging

import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core import security
from app.core.config import settings

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant context from JWT and sets request.state.

    Sets the following on request.state:
    - user_id: str (from JWT sub claim)
    - tenant_id: str (from JWT tenant_id claim)
    - role: str (from JWT role claim)
    - bypass_tenant_filter: bool (True for admin/supervisor)

    If no valid token is present, these values remain unset.
    Route-level authentication will handle 401 errors.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and inject tenant context."""
        # Initialize state values to None
        request.state.user_id = None
        request.state.tenant_id = None
        request.state.role = None
        request.state.bypass_tenant_filter = False

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Decode and validate JWT
                payload = jwt.decode(
                    token,
                    settings.JWT_PUBLIC_KEY,
                    algorithms=[security.ALGORITHM],
                )

                # Only process access tokens
                if payload.get("type") == "access":
                    # Set request state from JWT claims
                    request.state.user_id = payload.get("sub")
                    request.state.tenant_id = payload.get("tenant_id")
                    request.state.role = payload.get("role")

                    # Admin/Supervisor bypass tenant filtering (AC: #2)
                    role = payload.get("role", "")
                    if role in ["admin", "supervisor"]:
                        request.state.bypass_tenant_filter = True
                    else:
                        request.state.bypass_tenant_filter = False

                    logger.debug(
                        "Tenant context set",
                        extra={
                            "user_id": request.state.user_id,
                            "tenant_id": request.state.tenant_id,
                            "role": request.state.role,
                            "bypass": request.state.bypass_tenant_filter,
                        },
                    )

            except jwt.ExpiredSignatureError:
                # Token expired - let route-level auth handle 401
                logger.debug("Expired token in tenant context middleware")
            except jwt.PyJWTError as e:
                # Invalid token - let route-level auth handle 401
                logger.debug(f"Invalid token in tenant context middleware: {e}")

        # Continue processing request
        response = await call_next(request)
        return response
