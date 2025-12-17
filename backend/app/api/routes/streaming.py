"""
Asset Streaming API Routes (Story 4.2, Task 1).

Provides endpoints for:
- Streaming video/audio files with HTTP Range support
- MIME type validation (video/* and audio/* only)
- Permission-validated presigned URLs

References:
- Task 1: Create streaming endpoint
- AC: #1, #2, #6, #9, #10
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, SessionDep
from app.core.exceptions import AssetNotFoundError, InvalidAssetTypeError
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.repositories.asset_repository import AssetRepository
from app.schemas.streaming import StreamingURLResponse
from app.services.signed_url_service import SignedURLService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["streaming"])

# Supported MIME types for streaming (Task 3)
STREAMABLE_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
}
STREAMABLE_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/webm",
    "audio/aac",
}
STREAMABLE_MIME_TYPES = STREAMABLE_VIDEO_TYPES | STREAMABLE_AUDIO_TYPES


def is_streamable_mime_type(mime_type: str) -> bool:
    """
    Check if MIME type is streamable (video or audio).

    Args:
        mime_type: MIME type to check

    Returns:
        True if mime_type is in STREAMABLE_MIME_TYPES
    """
    return mime_type in STREAMABLE_MIME_TYPES


@router.get(
    "/{asset_id}/stream",
    response_model=StreamingURLResponse,
    summary="Stream video or audio asset",
    description="""
    Stream a video or audio asset via presigned URL with HTTP Range support.

    The returned URL supports HTTP Range requests for seeking and progressive playback.
    URL is valid for 1 hour.

    **Supported formats:**
    - Video: MP4, WebM, OGG, QuickTime
    - Audio: MP3, WAV, OGG, WebM, AAC

    **HTTP Range Support:**
    The returned URL supports Range headers for seeking:
    - Request: `Range: bytes=1000000-2000000`
    - Response: `206 Partial Content` with requested bytes

    **Permission:** User must own the asset or be Admin/Supervisor.

    **Error codes:**
    - 400 INVALID_ASSET_TYPE: Asset is not video/audio
    - 403 PERMISSION_DENIED: User lacks permission
    - 404 ASSET_NOT_FOUND: Asset does not exist
    """,
)
@limiter.limit(get_dynamic_rate_limit)
async def stream_asset(
    request: Request,
    asset_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> StreamingURLResponse:
    """
    Stream a video or audio asset via presigned URL (AC: #1, #2, #6, #9, #10).

    Args:
        request: FastAPI request object (for rate limiting)
        asset_id: UUID of the asset to stream
        session: Database session with tenant context
        current_user: Authenticated user making the request

    Returns:
        StreamingURLResponse with presigned URL and metadata

    Raises:
        AssetNotFoundError: Asset does not exist (404)
        InvalidAssetTypeError: Asset is not video/audio (400, AC: #9)
        AssetAccessDeniedError: User lacks permission (403, AC: #10)
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

    # Validate streamable type (AC: #9, Task 3)
    if not is_streamable_mime_type(asset.mime_type):
        logger.warning(
            "Streaming rejected for non-streamable asset",
            extra={
                "asset_id": str(asset_id),
                "mime_type": asset.mime_type,
                "user_id": str(current_user.id),
            },
        )
        raise InvalidAssetTypeError(
            message=f"Asset type '{asset.mime_type}' is not streamable. "
            f"Only video and audio files can be streamed.",
            details={
                "asset_id": str(asset_id),
                "mime_type": asset.mime_type,
                "supported_video_types": list(STREAMABLE_VIDEO_TYPES),
                "supported_audio_types": list(STREAMABLE_AUDIO_TYPES),
            },
        )

    # Generate stream URL (includes permission check, AC: #1, #10)
    service = SignedURLService(
        session=session,
        current_user=current_user,
        ip_address=client_ip,
    )
    url, expires_at = service.generate_stream_url(asset_id)

    logger.info(
        "Streaming URL generated successfully",
        extra={
            "asset_id": str(asset_id),
            "user_id": str(current_user.id),
            "mime_type": asset.mime_type,
            "file_size": asset.file_size_bytes,
        },
    )

    # Return response with metadata (AC: #2, #6)
    return StreamingURLResponse(
        stream_url=url,
        expires_at=expires_at,
        mime_type=asset.mime_type,
        file_size=asset.file_size_bytes,
        file_name=asset.file_name,
        duration_seconds=None,  # Future: extract from media metadata
    )
