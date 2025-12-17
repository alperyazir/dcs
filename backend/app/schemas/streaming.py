"""
Streaming Response Schemas (Story 4.2, Task 2).

Defines response models for video/audio streaming endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class StreamingURLResponse(BaseModel):
    """
    Response schema for streaming endpoint.

    Returns presigned URL for video/audio streaming with HTTP Range support.
    URL is valid for 1 hour (PRESIGNED_URL_STREAM_EXPIRES_SECONDS).

    References:
    - Task 2: Streaming response schema
    - AC: #2, #6 (stream URL with expiration and metadata)
    """

    stream_url: str = Field(
        description="Presigned URL for MinIO streaming (supports HTTP Range requests)"
    )
    expires_at: datetime = Field(description="URL expiration time (ISO-8601)")
    mime_type: str = Field(description="Content MIME type (video/* or audio/*)")
    file_size: int = Field(description="Total file size in bytes")
    file_name: str = Field(description="Original file name")
    duration_seconds: int | None = Field(
        default=None,
        description="Media duration in seconds (if available in metadata)",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "stream_url": "https://minio.example.com/assets/lesson-01.mp4?X-Amz-Algorithm=...",
                "expires_at": "2025-12-18T12:00:00Z",
                "mime_type": "video/mp4",
                "file_size": 52428800,
                "file_name": "lesson-01.mp4",
                "duration_seconds": 3600,
            }
        }
