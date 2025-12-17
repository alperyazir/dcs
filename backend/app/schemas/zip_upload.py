"""
ZIP Upload Schemas (Story 3.3, Task 6).

Request/Response schemas for ZIP archive upload operations.

References:
- AC: #10 (response with extracted count, skipped count, created assets list)
"""

from pydantic import Field
from sqlmodel import SQLModel

from app.schemas.asset import AssetResponse


class SkippedFileInfo(SQLModel):
    """Information about a file skipped during ZIP extraction."""

    file_name: str = Field(description="Name of the skipped file")
    reason: str = Field(
        description="Reason for skipping: system_file, directory, empty_file, path_traversal"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_name": ".DS_Store",
                "reason": "system_file",
            }
        }
    }


class FailedFileInfo(SQLModel):
    """Information about a file that failed validation during ZIP extraction."""

    file_name: str = Field(description="Name of the failed file")
    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_name": "virus.exe",
                "error_code": "INVALID_FILE_TYPE",
                "message": "File type 'application/x-msdownload' is not allowed",
            }
        }
    }


class ZipUploadResponse(SQLModel):
    """
    Response schema for ZIP archive upload (AC: #10).

    Returned on successful ZIP extraction with 201 Created.
    Contains counts and details of extracted, skipped, and failed files.
    """

    extracted_count: int = Field(
        description="Number of files successfully extracted and uploaded"
    )
    skipped_count: int = Field(
        description="Number of files skipped (system files, directories)"
    )
    failed_count: int = Field(description="Number of files that failed validation")
    total_size_bytes: int = Field(
        description="Total size of all extracted files in bytes"
    )

    assets: list[AssetResponse] = Field(
        description="List of created asset records for extracted files"
    )
    skipped_files: list[SkippedFileInfo] = Field(
        description="Details of files skipped during extraction"
    )
    failed_files: list[FailedFileInfo] = Field(
        description="Details of files that failed validation"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "extracted_count": 15,
                "skipped_count": 3,
                "failed_count": 1,
                "total_size_bytes": 52428800,
                "assets": [
                    {
                        "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                        "file_name": "document.pdf",
                        "file_size_bytes": 1048576,
                        "mime_type": "application/pdf",
                        "checksum": "d41d8cd98f00b204e9800998ecf8427e",
                        "object_key": "publisher/tenant-123/asset-456/document.pdf",
                        "bucket": "assets",
                        "user_id": "660e8400-e29b-41d4-a716-446655440001",
                        "tenant_id": "770e8400-e29b-41d4-a716-446655440002",
                        "is_deleted": False,
                        "created_at": "2025-12-17T10:30:00Z",
                        "updated_at": "2025-12-17T10:30:00Z",
                    }
                ],
                "skipped_files": [
                    {"file_name": ".DS_Store", "reason": "system_file"},
                    {"file_name": "__MACOSX/._document.pdf", "reason": "system_file"},
                    {"file_name": "images/", "reason": "directory"},
                ],
                "failed_files": [
                    {
                        "file_name": "malware.exe",
                        "error_code": "INVALID_FILE_TYPE",
                        "message": "File type 'application/x-msdownload' is not allowed",
                    }
                ],
            }
        }
    }
