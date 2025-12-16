"""
Rate Limiting Middleware.

Implements IP-based rate limiting using slowapi (AC: #8).

Configuration:
- Login endpoint: 5 requests per minute per IP
- Configurable via decorator on routes

Usage:
    from app.middleware.rate_limit import limiter

    @router.post("/login")
    @limiter.limit("5/minute")
    async def login(request: Request, ...):
        ...
"""

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse


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


# Create limiter instance with custom key function
limiter = Limiter(key_func=get_client_ip)


async def rate_limit_exceeded_handler(
    request: Request,  # noqa: ARG001
    exc: RateLimitExceeded,  # noqa: ARG001
) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Returns 429 Too Many Requests with Retry-After header (AC: #8).
    """
    # Extract retry-after from the exception message
    # slowapi format: "Rate limit exceeded: X per Y"
    retry_after = "60"  # Default 60 seconds

    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
        },
        headers={"Retry-After": retry_after},
    )
