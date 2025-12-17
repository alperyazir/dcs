"""
Batch Download Schemas (Story 4.4).

Request and response schemas for batch downloading multiple assets as ZIP.

References:
- Task 2: Create Batch Download Schemas
- AC: #4, #9, #10, #11, #12
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BatchDownloadRequest(BaseModel):
    """
    Request schema for batch download endpoint (AC: #1, #11, #12).

    Validates:
    - Non-empty asset list (min 1)
    - Maximum 100 assets per request
    - No duplicate asset IDs

    References:
        - Task 2.2: Request schema with validation
        - AC: #11 (empty list), #12 (too many assets)
    """

    asset_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
        description="List of asset IDs to include in batch download (1-100 assets)",
        examples=[
            [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002",
            ]
        ],
    )

    @field_validator("asset_ids")
    @classmethod
    def validate_unique_ids(cls, v: list[UUID]) -> list[UUID]:
        """Ensure no duplicate asset IDs (Task 2.2)."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate asset IDs are not allowed")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_ids": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002",
                    "550e8400-e29b-41d4-a716-446655440003",
                ]
            }
        }
    }


class BatchDownloadResponse(BaseModel):
    """
    Response schema for batch download endpoint (AC: #4).

    Contains:
    - Presigned download URL for the generated ZIP
    - Expiration time (1 hour, AC: #5, #8)
    - File metadata (count, sizes)

    References:
        - Task 2.3: Response schema
        - AC: #4 (download URL), #5 (expiry)
    """

    download_url: str = Field(
        description="Presigned URL to download the generated ZIP file"
    )
    expires_at: datetime = Field(
        description="URL and ZIP file expiration time (1 hour from creation)"
    )
    file_name: str = Field(description="Generated ZIP file name")
    file_count: int = Field(ge=1, description="Number of files included in the ZIP")
    total_size_bytes: int = Field(
        ge=0, description="Total size of all files before compression"
    )
    compressed_size_bytes: int = Field(ge=0, description="Size of the ZIP file")

    model_config = {
        "json_schema_extra": {
            "example": {
                "download_url": "https://minio.example.com/assets/temp/batch-downloads/batch-download-20251217-100000-abc123.zip?...",
                "expires_at": "2025-12-17T12:00:00Z",
                "file_name": "batch-download-20251217-100000-abc123.zip",
                "file_count": 3,
                "total_size_bytes": 52428800,
                "compressed_size_bytes": 41943040,
            }
        }
    }
