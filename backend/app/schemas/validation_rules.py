"""
Validation Rules Response Schemas (Story 3.4, AC: #8).

Provides validation rules to frontend for pre-flight validation:
- Allowed MIME types
- Size limits per category
- Extension-to-MIME mappings
"""

from pydantic import Field
from sqlmodel import SQLModel


class SizeLimitInfo(SQLModel):
    """Size limit information for a file category."""

    category: str = Field(description="File category (video, image, audio, default)")
    max_size_bytes: int = Field(description="Maximum file size in bytes")
    max_size_human: str = Field(description="Human-readable size limit (e.g., '10 GB')")


class ExtensionMapping(SQLModel):
    """Extension to MIME type mapping."""

    extension: str = Field(description="File extension (e.g., '.pdf')")
    mime_types: list[str] = Field(description="Allowed MIME types for this extension")


class ValidationRulesResponse(SQLModel):
    """
    Response containing all file validation rules (Story 3.4, AC: #8).

    Use this to:
    - Show allowed file types in upload UI
    - Validate files before upload attempt
    - Display size limits to users
    - Build file type filters for file picker
    """

    allowed_mime_types: list[str] = Field(description="List of allowed MIME types")
    size_limits: list[SizeLimitInfo] = Field(
        description="Size limits per file category"
    )
    extension_mappings: list[ExtensionMapping] = Field(
        description="Extension to MIME type mappings"
    )
    max_filename_length: int = Field(description="Maximum allowed filename length")
    dangerous_extensions: list[str] = Field(
        description="Extensions that are always blocked"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "allowed_mime_types": [
                    "application/pdf",
                    "video/mp4",
                    "image/jpeg",
                    "audio/mpeg",
                ],
                "size_limits": [
                    {
                        "category": "video",
                        "max_size_bytes": 10737418240,
                        "max_size_human": "10 GB",
                    },
                    {
                        "category": "image",
                        "max_size_bytes": 524288000,
                        "max_size_human": "500 MB",
                    },
                    {
                        "category": "audio",
                        "max_size_bytes": 104857600,
                        "max_size_human": "100 MB",
                    },
                    {
                        "category": "default",
                        "max_size_bytes": 5368709120,
                        "max_size_human": "5 GB",
                    },
                ],
                "extension_mappings": [
                    {"extension": ".pdf", "mime_types": ["application/pdf"]},
                    {"extension": ".mp4", "mime_types": ["video/mp4"]},
                    {"extension": ".jpg", "mime_types": ["image/jpeg"]},
                ],
                "max_filename_length": 255,
                "dangerous_extensions": [".exe", ".bat", ".cmd", ".com", ".msi"],
            }
        }
    }
