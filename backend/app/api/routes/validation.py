"""
Validation Rules API Routes (Story 3.4, AC: #8).

Provides:
- GET /api/v1/upload/validation-rules - Returns validation rules for frontend

This endpoint does NOT require authentication - allows frontend to pre-validate
files before upload attempt.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.validation_rules import (
    ExtensionMapping,
    SizeLimitInfo,
    ValidationRulesResponse,
)
from app.services.file_validation_service import get_extension_mime_map

router = APIRouter(prefix="/upload", tags=["validation"])

# Dangerous extensions that are always blocked (for frontend display)
DANGEROUS_EXTENSIONS = [
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".msi",
    ".scr",
    ".pif",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".ws",
    ".wsf",
    ".wsc",
    ".wsh",
    ".php",
    ".jsp",
    ".asp",
    ".aspx",
]


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            # Remove decimal for whole numbers
            if size == int(size):
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


@router.get(
    "/validation-rules",
    response_model=ValidationRulesResponse,
    summary="Get file validation rules",
    description="""
    Returns the current file validation rules for client-side pre-validation.

    **Use this endpoint to:**
    - Show allowed file types in upload UI
    - Validate files before upload attempt (reduce failed uploads)
    - Display size limits to users
    - Build file type filters for file picker dialogs
    - Show blocked file extensions

    **This endpoint does NOT require authentication** - validation rules
    are public information needed by the frontend.

    **Response includes:**
    - `allowed_mime_types`: List of MIME types accepted by the server
    - `size_limits`: Maximum file size per category (video, image, audio, default)
    - `extension_mappings`: Which extensions map to which MIME types
    - `max_filename_length`: Maximum allowed filename length
    - `dangerous_extensions`: Extensions that are always blocked for security
    """,
    responses={
        200: {
            "description": "Validation rules returned successfully",
            "model": ValidationRulesResponse,
        },
    },
)
async def get_validation_rules() -> ValidationRulesResponse:
    """
    Return current file validation rules for frontend pre-validation.

    No authentication required - rules are public information.
    """
    # Build size limits list
    size_limits = [
        SizeLimitInfo(
            category="video",
            max_size_bytes=settings.MAX_FILE_SIZE_VIDEO,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_VIDEO),
        ),
        SizeLimitInfo(
            category="image",
            max_size_bytes=settings.MAX_FILE_SIZE_IMAGE,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_IMAGE),
        ),
        SizeLimitInfo(
            category="audio",
            max_size_bytes=settings.MAX_FILE_SIZE_AUDIO,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_AUDIO),
        ),
        SizeLimitInfo(
            category="default",
            max_size_bytes=settings.MAX_FILE_SIZE_DEFAULT,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_DEFAULT),
        ),
    ]

    # Build extension mappings from service
    extension_map = get_extension_mime_map()
    extension_mappings = [
        ExtensionMapping(extension=ext, mime_types=mimes)
        for ext, mimes in sorted(extension_map.items())
    ]

    return ValidationRulesResponse(
        allowed_mime_types=settings.ALLOWED_MIME_TYPES,
        size_limits=size_limits,
        extension_mappings=extension_mappings,
        max_filename_length=255,
        dangerous_extensions=DANGEROUS_EXTENSIONS,
    )
