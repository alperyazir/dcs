"""
Asset Preview API Routes (Story 4.3, Task 1).

Provides endpoints for:
- Generating preview URLs for different asset types
- Supporting inline browser rendering (images, videos, audio, PDFs, documents)
- Returning metadata for unsupported types

References:
- Task 1: Create Preview Endpoint
- AC: #1, #2, #3, #4, #5, #6, #7, #8, #9, #10
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, SessionDep
from app.core.exceptions import AssetNotFoundError
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.models import AuditAction
from app.repositories.asset_repository import AssetRepository
from app.schemas.preview import PreviewResponse, PreviewType
from app.services.signed_url_service import SignedURLService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["preview"])

# Supported MIME types for each preview type (Task 3)
IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/bmp",
}

VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
}

AUDIO_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/webm",
    "audio/aac",
}

PDF_MIME_TYPES = {
    "application/pdf",
}

DOCUMENT_MIME_TYPES = {
    "application/json",
    "text/plain",
    "text/html",
    "text/css",
    "text/javascript",
}


def get_preview_type(mime_type: str) -> PreviewType:
    """
    Determine preview type from MIME type (Task 3).

    Args:
        mime_type: MIME type of the asset

    Returns:
        PreviewType enum value indicating how to preview the asset

    References:
        - Task 3: Implement Preview Type Detection
        - AC: #1, #3, #5, #7, #9
    """
    if mime_type in IMAGE_MIME_TYPES:
        return PreviewType.IMAGE
    elif mime_type in VIDEO_MIME_TYPES:
        return PreviewType.VIDEO
    elif mime_type in AUDIO_MIME_TYPES:
        return PreviewType.AUDIO
    elif mime_type in PDF_MIME_TYPES:
        return PreviewType.PDF
    elif mime_type in DOCUMENT_MIME_TYPES:
        return PreviewType.DOCUMENT
    else:
        return PreviewType.UNSUPPORTED


@router.get(
    "/{asset_id}/preview",
    response_model=PreviewResponse,
    summary="Get asset preview URL",
    description="""
    Get a preview URL for an asset based on its type.

    Returns a presigned URL appropriate for inline preview:
    - **Images** (JPEG, PNG, GIF, WebP, SVG): Direct URL for `<img>` tag
    - **Videos** (MP4, WebM, OGG, QuickTime): URL for `<video>` tag with controls
    - **Audio** (MP3, WAV, OGG, AAC): URL for `<audio>` tag with controls
    - **PDFs**: URL for iframe or PDF.js viewer
    - **Documents** (JSON, Plain Text, HTML, CSS, JS): URL for code/text viewer
    - **Unsupported**: Returns null URL with file metadata only

    **Preview URLs:**
    - Valid for 1 hour (AC: #8)
    - Browser renders content directly from MinIO (zero-proxy architecture)
    - HTTP Range support for video/audio seeking

    **Permission:** User must own the asset or be Admin/Supervisor (AC: #10).

    **Error codes:**
    - 403 PERMISSION_DENIED: User lacks permission
    - 404 ASSET_NOT_FOUND: Asset does not exist
    """,
)
@limiter.limit(get_dynamic_rate_limit)
async def preview_asset(
    request: Request,
    asset_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> PreviewResponse:
    """
    Get preview URL for an asset (AC: #1-#10).

    Args:
        request: FastAPI request object (for rate limiting)
        asset_id: UUID of the asset to preview
        session: Database session with tenant context
        current_user: Authenticated user making the request

    Returns:
        PreviewResponse with URL and metadata

    Raises:
        AssetNotFoundError: Asset does not exist (404)
        AssetAccessDeniedError: User lacks permission (403, AC: #10)

    References:
        - Task 1: Create Preview Endpoint
        - Task 4: Implement Preview URL Generation
        - AC: #1-#10
    """
    # Get client IP for audit logging
    client_ip = get_client_ip(request)

    # Get asset (validates existence)
    asset_repo = AssetRepository(session)
    asset = asset_repo.get_by_id(asset_id)

    if not asset:
        raise AssetNotFoundError(asset_id=asset_id)

    # Check if asset is soft-deleted
    if asset.is_deleted:
        raise AssetNotFoundError(asset_id=asset_id)

    # Determine preview type from MIME type (Task 3, AC: #1, #3, #5, #7, #9)
    preview_type = get_preview_type(asset.mime_type)
    supports_inline = preview_type != PreviewType.UNSUPPORTED

    preview_url = None
    expires_at = None

    # Generate preview URL for supported types (Task 4, AC: #1-#8)
    if supports_inline:
        service = SignedURLService(
            session=session,
            current_user=current_user,
            ip_address=client_ip,
        )

        # All preview types use download URL - browser handles rendering
        # For images/PDFs: Direct display
        # For video/audio: HTML5 players handle streaming automatically
        # For documents: Text/code viewers
        preview_url, expires_at = service.generate_download_url(asset_id)

        # Create preview audit log (Task 5.3, AC: #8)
        service._create_audit_log(
            asset_id=asset.id,
            action=AuditAction.PREVIEW,
            metadata={
                "preview_type": preview_type.value,
                "mime_type": asset.mime_type,
                "expires_at": expires_at.isoformat() if expires_at else "",
            },
        )

        logger.info(
            "Preview URL generated successfully",
            extra={
                "asset_id": str(asset_id),
                "user_id": str(current_user.id),
                "preview_type": preview_type.value,
                "mime_type": asset.mime_type,
            },
        )
    else:
        logger.info(
            "Preview not supported for asset type",
            extra={
                "asset_id": str(asset_id),
                "user_id": str(current_user.id),
                "mime_type": asset.mime_type,
            },
        )

    # Return response with metadata (AC: #1, #2, #8, #9)
    return PreviewResponse(
        preview_url=preview_url,
        preview_type=preview_type,
        expires_at=expires_at,
        mime_type=asset.mime_type,
        file_name=asset.file_name,
        file_size=asset.file_size_bytes,
        supports_inline=supports_inline,
    )
