import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Response
from sqlalchemy import text
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.core.minio_client import get_minio_client
from app.schemas.health import HealthCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

HEALTH_CHECK_TIMEOUT_SECONDS = 5


def check_database_health() -> Literal["ok", "error"]:
    """Check database connectivity by executing SELECT 1."""
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        logger.warning("Database health check failed: %s", e)
        return "error"


def check_minio_health() -> Literal["ok", "error"]:
    """Check MinIO connectivity by checking bucket existence."""
    try:
        client = get_minio_client()
        client.bucket_exists(settings.MINIO_BUCKET_NAME)
        return "ok"
    except Exception as e:
        logger.warning("MinIO health check failed: %s", e)
        return "error"


async def check_with_timeout(
    func: Callable[[], Literal["ok", "error"]],
    timeout: float,
) -> Literal["ok", "error"]:
    """Run a sync function in executor with timeout."""
    loop = asyncio.get_running_loop()
    try:
        result: Literal["ok", "error"] = await asyncio.wait_for(
            loop.run_in_executor(None, func),
            timeout=timeout,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("Health check timed out after %s seconds", timeout)
        return "error"


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    responses={
        200: {"description": "All systems healthy"},
        503: {"description": "One or more systems unhealthy"},
    },
)
async def health_check(response: Response) -> HealthCheckResponse:
    """
    Health check endpoint for monitoring systems.

    Checks PostgreSQL and MinIO connectivity with timeout handling.
    Returns 200 if all healthy, 503 if any component unhealthy.
    """
    # Run checks concurrently with timeout for performance (<100ms target)
    db_status, minio_status = await asyncio.gather(
        check_with_timeout(check_database_health, HEALTH_CHECK_TIMEOUT_SECONDS),
        check_with_timeout(check_minio_health, HEALTH_CHECK_TIMEOUT_SECONDS),
    )

    # Determine overall health
    is_healthy = db_status == "ok" and minio_status == "ok"
    overall_status: Literal["healthy", "unhealthy"] = (
        "healthy" if is_healthy else "unhealthy"
    )

    # Set HTTP status code
    if not is_healthy:
        response.status_code = 503

    return HealthCheckResponse(
        status=overall_status,
        database=db_status,
        minio=minio_status,
        timestamp=datetime.now(timezone.utc),
    )
