"""
Download Response Schemas (Story 4.1, Task 2).

Provides response schemas for asset download endpoints.

References:
- AC: #3 (response includes download_url, expires_at, file_name, file_size, mime_type)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DownloadResponse(BaseModel):
    """Response schema for asset download endpoint.

    Returns presigned download URL with complete file metadata.

    References:
    - AC: #3 (enhanced download response)
    - Task 2.2 (schema fields)
    """

    download_url: str = Field(
        description="Presigned URL for direct MinIO download (1-hour TTL)",
        json_schema_extra={
            "example": "https://minio.example.com/assets/...?X-Amz-Signature=..."
        },
    )
    expires_at: datetime = Field(
        description="URL expiration time in ISO-8601 format",
        json_schema_extra={"example": "2025-12-17T12:00:00Z"},
    )
    file_name: str = Field(
        description="Original file name",
        json_schema_extra={"example": "document.pdf"},
    )
    file_size: int = Field(
        description="File size in bytes",
        json_schema_extra={"example": 1234567},
    )
    mime_type: str = Field(
        description="MIME type of the file",
        json_schema_extra={"example": "application/pdf"},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "download_url": "https://minio.example.com/assets/uuid/file.pdf?X-Amz-Algorithm=...",
                "expires_at": "2025-12-17T12:00:00Z",
                "file_name": "document.pdf",
                "file_size": 1234567,
                "mime_type": "application/pdf",
            }
        }
    )
