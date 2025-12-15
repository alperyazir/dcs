from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: Literal["healthy", "unhealthy"]
    database: Literal["ok", "error"]
    minio: Literal["ok", "error"]
    timestamp: datetime
