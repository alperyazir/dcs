"""
Rate Limiting Middleware (Story 2.4).

Implements role-based rate limiting using slowapi.

Configuration (AC: #1-#4):
- Publisher/School: 1000 requests per hour
- Teacher: 500 requests per hour
- Student: 100 requests per hour
- Admin/Supervisor: Unlimited
- Unauthenticated: IP-based fallback (100/hour)

Usage:
    from app.middleware.rate_limit import limiter, get_dynamic_rate_limit

    @router.get("/assets")
    @limiter.limit(get_dynamic_rate_limit)
    async def list_assets(request: Request, ...):
        ...

    # For login endpoint (keep IP-based)
    @router.post("/login")
    @limiter.limit("5/minute")
    async def login(request: Request, ...):
        ...
"""

import logging
from datetime import datetime, timezone

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.config import settings
from app.models import UserRole

logger = logging.getLogger(__name__)


def get_rate_limits() -> dict[UserRole, str | None]:
    """
    Get rate limits from configuration (Story 2.4).

    Limits are configurable via environment variables:
    - RATE_LIMIT_PUBLISHER: Publisher/School limit (default: 1000/hour)
    - RATE_LIMIT_TEACHER: Teacher limit (default: 500/hour)
    - RATE_LIMIT_STUDENT: Student limit (default: 100/hour)
    - Admin/Supervisor always have unlimited access

    Returns:
        Dictionary mapping UserRole to limit string (or None for unlimited)
    """
    return {
        UserRole.ADMIN: None,  # Unlimited (AC: #4)
        UserRole.SUPERVISOR: None,  # Unlimited (AC: #4)
        UserRole.PUBLISHER: settings.RATE_LIMIT_PUBLISHER,  # AC: #1
        UserRole.SCHOOL: settings.RATE_LIMIT_SCHOOL,  # Same as publisher
        UserRole.TEACHER: settings.RATE_LIMIT_TEACHER,  # AC: #2
        UserRole.STUDENT: settings.RATE_LIMIT_STUDENT,  # AC: #3
    }


# Rate limit constants per role (AC: #1-#4)
# Loaded from settings for configurability
RATE_LIMITS: dict[UserRole, str | None] = get_rate_limits()

# Default limit for unauthenticated requests (configurable)
DEFAULT_UNAUTHENTICATED_LIMIT = settings.RATE_LIMIT_DEFAULT


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles X-Forwarded-For header for reverse proxy setups (Traefik).
    Falls back to direct client IP if header not present.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    # Fall back to slowapi's default method
    return get_remote_address(request)


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on authenticated user or IP (AC: #5, #10).

    Authenticated users: "{user_id}:{role}" - ensures per-user + role isolation
    Unauthenticated: IP address - fallback for public endpoints

    Args:
        request: FastAPI request with state from TenantContextMiddleware

    Returns:
        Rate limit key string for bucket identification
    """
    current_user = getattr(request.state, "current_user", None)

    if current_user and hasattr(current_user, "user_id") and current_user.user_id:
        # Use user_id:role for authenticated requests (AC: #5)
        user_id = current_user.user_id
        role = getattr(current_user, "role", "unknown")
        return f"{user_id}:{role}"

    # Fallback to IP for unauthenticated requests (AC: #10)
    return get_client_ip(request)


def get_rate_limit_for_request(request: Request) -> str | None:
    """
    Get rate limit string for the current request based on user role (AC: #1-#4).

    Returns None for Admin/Supervisor (unlimited access).

    Args:
        request: FastAPI request with state from TenantContextMiddleware

    Returns:
        Rate limit string (e.g., "1000/hour") or None for unlimited
    """
    current_user = getattr(request.state, "current_user", None)

    if not current_user or not hasattr(current_user, "role") or not current_user.role:
        # Unauthenticated: apply default IP-based limit (AC: #10)
        return DEFAULT_UNAUTHENTICATED_LIMIT

    role_str = current_user.role
    try:
        role = UserRole(role_str) if isinstance(role_str, str) else role_str
        return RATE_LIMITS.get(role, DEFAULT_UNAUTHENTICATED_LIMIT)
    except ValueError:
        # Unknown role, apply default limit
        return DEFAULT_UNAUTHENTICATED_LIMIT


def get_dynamic_rate_limit(request: Request | None = None) -> str:
    """
    Dynamic rate limit callable for use with @limiter.limit decorator.

    Returns a very high limit for Admin/Supervisor (effectively unlimited)
    since slowapi doesn't support skipping rate limits directly.

    Args:
        request: FastAPI request with state from TenantContextMiddleware.
                 Can be None when slowapi calls for initial limit check.

    Returns:
        Rate limit string for slowapi
    """
    if request is None:
        # Called by slowapi during initialization - return default limit
        return DEFAULT_UNAUTHENTICATED_LIMIT

    limit = get_rate_limit_for_request(request)
    if limit is None:
        # Admin/Supervisor: use very high limit (effectively unlimited)
        return "1000000/second"
    return limit


# Create limiter instance with role-based key function (AC: #5, #6)
limiter = Limiter(key_func=get_rate_limit_key)


def _parse_retry_after(exc: RateLimitExceeded) -> int:
    """
    Parse retry-after seconds from slowapi exception (AC: #8).

    Args:
        exc: RateLimitExceeded exception from slowapi

    Returns:
        Number of seconds until rate limit resets
    """
    if hasattr(exc, "retry_after") and exc.retry_after is not None:
        return int(exc.retry_after)
    return 60  # Default fallback


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> Response:
    """
    Handle rate limit exceeded with logging and standardized response (AC: #7-#9).

    Returns 429 Too Many Requests with:
    - error_code: "RATE_LIMIT_EXCEEDED"
    - message: User-friendly message
    - details: user_id, role, retry_after_seconds
    - request_id: For debugging
    - timestamp: ISO format
    - Retry-After header: Seconds until limit resets

    Logs violation for abuse detection with structured fields.
    """
    request_id = getattr(request.state, "request_id", None)
    current_user = getattr(request.state, "current_user", None)

    user_id: str | None = None
    role: str | None = None

    if current_user:
        user_id = (
            str(current_user.user_id)
            if hasattr(current_user, "user_id") and current_user.user_id
            else None
        )
        role = current_user.role if hasattr(current_user, "role") else None

    # Log violation for abuse detection (AC: #9)
    logger.warning(
        "Rate limit exceeded",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "role": role,
            "endpoint": request.url.path,
            "method": request.method,
            "client_ip": get_client_ip(request),
            "limit_detail": str(exc.detail),
        },
    )

    # Parse retry-after from exception (AC: #8)
    retry_after = _parse_retry_after(exc)

    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
            "details": {
                "user_id": user_id,
                "role": role,
                "retry_after_seconds": retry_after,
            },
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        headers={"Retry-After": str(retry_after)},
    )
