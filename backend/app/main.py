import logging
from datetime import datetime, timezone

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.tenant_context import TenantContextMiddleware

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


def get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Rate limiting state (AC: #8)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware registration order (LIFO - last added runs first on request)
# 1. LoggingMiddleware - logs request/response with timing
# 2. TenantContextMiddleware - extracts tenant context from JWT (Story 2.2)
# 3. RequestIDMiddleware - generates unique request ID
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RequestIDMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check at root level (no authentication required for monitoring)
app.include_router(health_router)


# Exception handlers that include request_id for debugging
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with request_id in response."""
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc.detail),  # Backwards compatibility with FastAPI default
            "error_code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "details": None,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with request_id in response."""
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),  # Backwards compatibility with FastAPI default
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": exc.errors()},
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with request_id and logging."""
    request_id = get_request_id(request)

    # Log the full exception with stack trace
    logger.exception(
        "Unhandled exception",
        extra={"request_id": request_id, "exception": str(exc)},
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred",  # Backwards compatibility
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": None,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
