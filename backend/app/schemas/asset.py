"""
Asset Schemas (Story 3.1, Task 7).

Request/Response schemas for asset operations.

References:
- AC: #6 (AssetResponse includes asset_id, checksum, etc.)
- Task 7.3 (validation for file_name)
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from sqlmodel import SQLModel


class AssetResponse(SQLModel):
    """
    Response schema for asset operations (AC: #6).

    Returned on successful upload with 201 Created.
    """

    id: UUID = Field(alias="asset_id", description="Unique asset identifier")
    file_name: str = Field(description="Original filename (sanitized)")
    file_size_bytes: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type of the file")
    checksum: str | None = Field(description="MD5 checksum for integrity verification")
    object_key: str = Field(description="MinIO object key (storage path)")
    bucket: str = Field(description="MinIO bucket name")
    user_id: UUID = Field(description="Owner user ID")
    tenant_id: UUID = Field(description="Tenant ID")
    is_deleted: bool = Field(description="Soft delete flag")
    created_at: datetime = Field(description="Upload timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "textbook.pdf",
                "file_size_bytes": 15728640,
                "mime_type": "application/pdf",
                "checksum": "d41d8cd98f00b204e9800998ecf8427e",
                "object_key": "publisher/tenant-123/asset-456/textbook.pdf",
                "bucket": "assets",
                "user_id": "660e8400-e29b-41d4-a716-446655440001",
                "tenant_id": "770e8400-e29b-41d4-a716-446655440002",
                "is_deleted": False,
                "created_at": "2025-12-17T10:30:00Z",
                "updated_at": "2025-12-17T10:30:00Z",
            }
        },
    }


class UploadResponse(SQLModel):
    """
    Simplified upload response schema.

    Used when only upload confirmation is needed.
    """

    asset_id: UUID = Field(description="Unique asset identifier")
    file_name: str = Field(description="Original filename (sanitized)")
    file_size_bytes: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type of the file")
    checksum: str | None = Field(description="MD5 checksum")
    message: str = Field(default="Upload successful", description="Status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "lecture.mp4",
                "file_size_bytes": 104857600,
                "mime_type": "video/mp4",
                "checksum": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "message": "Upload successful",
            }
        }
    }


class AssetListResponse(SQLModel):
    """Response schema for listing assets."""

    data: list[AssetResponse] = Field(description="List of assets")
    count: int = Field(description="Total count of assets")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")


class AssetError(SQLModel):
    """Error response schema for asset operations."""

    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )
    request_id: str | None = Field(default=None, description="Request ID for tracing")
    timestamp: str = Field(description="Error timestamp in ISO format")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error_code": "INVALID_FILE_TYPE",
                "message": "File type 'application/exe' is not allowed",
                "details": {
                    "mime_type": "application/exe",
                    "allowed_types": ["application/pdf", "video/mp4"],
                },
                "request_id": "req-123-456",
                "timestamp": "2025-12-17T10:30:00Z",
            }
        }
    }
