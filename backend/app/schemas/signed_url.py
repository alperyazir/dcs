"""
Signed URL Schemas (Story 3.2, Task 5).

Request/Response schemas for presigned URL operations.

References:
- AC: #9 (Response includes signed URL and expiration timestamp in ISO-8601)
- AC: #2, #3 (TTL values for upload/download)
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.file_validation_service import (
    get_allowed_mime_types,
    validate_filename,
)


class SignedURLResponse(BaseModel):
    """
    Response schema for signed URL generation (AC: #9).

    Returned when a presigned URL is successfully generated.
    """

    url: str = Field(description="Presigned URL for direct MinIO access")
    expires_at: datetime = Field(description="URL expiration time (ISO-8601)")
    type: Literal["download", "upload", "stream"] = Field(
        description="Type of signed URL operation"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "http://minio:9000/assets/publisher/tenant-id/asset-id/file.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
                "expires_at": "2025-12-17T12:00:00Z",
                "type": "download",
            }
        }
    }


class UploadURLRequest(BaseModel):
    """
    Request schema for presigned upload URL generation.

    Validates file_name and mime_type before generating upload URL.
    """

    file_name: str = Field(
        max_length=255,
        description="Name of the file to upload",
    )
    mime_type: str = Field(
        max_length=127,
        description="MIME type of the file",
    )
    file_size: int = Field(
        gt=0,
        description="Size of the file in bytes",
    )

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        """Validate and sanitize filename."""
        result = validate_filename(v)
        if not result.is_valid:
            raise ValueError(result.error_message or "Invalid filename")
        return v

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Validate MIME type is in allowed list."""
        allowed_types = get_allowed_mime_types()
        if v not in allowed_types:
            raise ValueError(
                f"MIME type '{v}' is not allowed. "
                f"Allowed types: {', '.join(sorted(allowed_types)[:5])}..."
            )
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_name": "textbook.pdf",
                "mime_type": "application/pdf",
                "file_size": 15728640,
            }
        }
    }


class UploadURLResponse(BaseModel):
    """
    Response schema for presigned upload URL generation.

    Includes the upload URL, expiration, and the asset_id for the new asset.
    """

    url: str = Field(description="Presigned URL for direct MinIO upload")
    expires_at: datetime = Field(description="URL expiration time (ISO-8601)")
    type: Literal["upload"] = Field(default="upload", description="URL type")
    asset_id: UUID = Field(description="Pre-generated asset ID for the upload")
    object_key: str = Field(description="MinIO object key where file will be stored")

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "http://minio:9000/assets/publisher/tenant-id/asset-id/file.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
                "expires_at": "2025-12-17T10:15:00Z",
                "type": "upload",
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "object_key": "publisher/tenant-id/asset-id/file.pdf",
            }
        }
    }
