"""
Asset Preview Response Schemas (Story 4.3).

Provides schemas for:
- Preview type enumeration (image, video, audio, pdf, document, unsupported)
- Preview response with signed URL and metadata

References:
- Task 2: Create Preview Response Schema
- AC: #1, #8, #9
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PreviewType(str, Enum):
    """
    Types of asset previews supported.

    Determines how the frontend should render the preview:
    - image: Display in <img> tag
    - video: Display in <video> tag with controls
    - audio: Display in <audio> tag with controls
    - pdf: Display in <iframe> or PDF.js viewer
    - document: Display in code/text viewer
    - unsupported: No inline preview, download only
    """

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    DOCUMENT = "document"
    UNSUPPORTED = "unsupported"


class PreviewResponse(BaseModel):
    """
    Response schema for asset preview endpoint (AC: #1, #8, #9).

    Returns a presigned URL appropriate for inline preview based on asset type.
    For unsupported types, returns null URL with file metadata only.

    Attributes:
        preview_url: Presigned URL for preview (null for unsupported types)
        preview_type: Type of preview (image, video, audio, pdf, document, unsupported)
        expires_at: URL expiration timestamp (null for unsupported types)
        mime_type: Original MIME type of the asset
        file_name: Original file name
        file_size: File size in bytes
        supports_inline: Whether the asset can be previewed inline in browser
    """

    preview_url: str | None = Field(
        default=None,
        description="Presigned URL for preview (null for unsupported types)",
        examples=["https://minio.example.com/assets/photo.jpg?signature=abc123"],
    )
    preview_type: PreviewType = Field(
        description="Type of preview: image, video, audio, pdf, document, unsupported",
        examples=[PreviewType.IMAGE],
    )
    expires_at: datetime | None = Field(
        default=None,
        description="URL expiration time (ISO-8601, null for unsupported types)",
        examples=["2025-12-18T12:00:00Z"],
    )
    mime_type: str = Field(
        description="Original MIME type of the asset",
        examples=["image/jpeg"],
    )
    file_name: str = Field(
        description="Original file name",
        examples=["photo.jpg"],
    )
    file_size: int = Field(
        description="File size in bytes",
        examples=[1234567],
        ge=0,
    )
    supports_inline: bool = Field(
        description="Whether the asset can be previewed inline in browser",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "preview_url": "https://minio.example.com/assets/photo.jpg?signature=abc123",
                    "preview_type": "image",
                    "expires_at": "2025-12-18T12:00:00Z",
                    "mime_type": "image/jpeg",
                    "file_name": "photo.jpg",
                    "file_size": 1234567,
                    "supports_inline": True,
                },
                {
                    "preview_url": None,
                    "preview_type": "unsupported",
                    "expires_at": None,
                    "mime_type": "application/zip",
                    "file_name": "archive.zip",
                    "file_size": 9876543,
                    "supports_inline": False,
                },
            ]
        }
    )
