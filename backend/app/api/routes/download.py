"""
Asset Download API Routes (Story 4.1, Task 1).

Provides:
- GET /api/v1/assets/{asset_id}/download - Generate presigned download URL with file metadata

References:
- AC: #1 (permission validation)
- AC: #2 (presigned URL generation with 1-hour TTL)
- AC: #3 (response with download_url, expires_at, file metadata)
- AC: #4 (direct MinIO access without API proxying)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, TenantSessionDep
from app.core.exceptions import AssetNotFoundError
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.models import AuditAction, AuditLog
from app.repositories.asset_repository import AssetRepository
from app.schemas.download import DownloadResponse
from app.services.signed_url_service import SignedURLService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["download"])


@router.get(
    "/{asset_id}/download",
    response_model=DownloadResponse,
    summary="Download asset via presigned URL",
    description="""
    Generate a presigned URL for downloading an asset directly from MinIO.
    Returns enhanced response with file metadata (file_name, file_size, mime_type).

    **Authorization:**
    - User must own the asset, OR
    - User must be Admin/Supervisor (can access any asset)

    **URL Validity:**
    - Download URLs are valid for 1 hour (configurable)
    - URL uses HMAC-SHA256 signature

    **Direct Download:**
    - Client downloads directly from MinIO using the signed URL
    - No API proxying - reduces server load (NFR-P4, NFR-P5, NFR-P6)
    - Supports HTTP Range requests for resume capability

    **Audit Logging:**
    - Creates audit log entry with action="download" (AC: #5)

    **Returns:**
    - 200 OK with presigned URL and file metadata
    - 403 Forbidden if user lacks permission
    - 404 Not Found if asset does not exist
    - 429 Too Many Requests if rate limit exceeded
    """,
    responses={
        200: {
            "description": "Presigned download URL with file metadata",
            "model": DownloadResponse,
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "PERMISSION_DENIED",
                        "message": "You do not have permission to access this asset",
                        "details": {"asset_id": "uuid"},
                        "timestamp": "2025-12-17T10:30:00Z",
                    }
                }
            },
        },
        404: {
            "description": "Asset not found",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "ASSET_NOT_FOUND",
                        "message": "Asset not found",
                        "details": {"asset_id": "uuid"},
                        "timestamp": "2025-12-17T10:30:00Z",
                    }
                }
            },
        },
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(get_dynamic_rate_limit)
async def download_asset(
    request: Request,
    asset_id: UUID,
    session: TenantSessionDep,
    current_user: CurrentUser,
) -> DownloadResponse:
    """
    Download an asset via presigned URL.

    Returns a presigned URL for direct MinIO download along with file metadata.
    The URL is valid for 1 hour and supports HTTP Range requests.

    **Permission:** User must own the asset or be Admin/Supervisor.

    References:
    - Task 1.1: GET endpoint
    - Task 1.2: Permission validation
    - Task 1.3: Presigned URL generation
    - Task 1.4: Enhanced response with metadata
    - Task 1.5: Rate limiting
    """
    request_id = getattr(request.state, "request_id", None)
    ip_address = get_client_ip(request)

    logger.info(
        "Download request received",
        extra={
            "asset_id": str(asset_id),
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    # Generate presigned URL with permission check (Task 1.2, 1.3)
    # Service will fetch and validate asset (eliminates N+1 query)
    service = SignedURLService(
        session=session,
        current_user=current_user,
        ip_address=ip_address,
    )

    url, expires_at = service.generate_download_url(
        asset_id=asset_id,
        request_id=request_id,
    )

    # Get asset for metadata after permission check (Task 1.4)
    # Asset is guaranteed to exist and user has access at this point
    asset_repo = AssetRepository(session)
    asset = asset_repo.get_by_id(asset_id)
    if not asset:
        # This should never happen after successful generate_download_url
        raise AssetNotFoundError(asset_id=asset_id, request_id=request_id)

    # Create audit log with DOWNLOAD action (Task 4.3, AC: #5)
    # Note: Audit logging is best-effort - failures should not block downloads
    try:
        audit_log = AuditLog(
            user_id=current_user.id,
            asset_id=asset.id,
            action=AuditAction.DOWNLOAD,
            ip_address=ip_address,
            metadata_json={
                "file_name": asset.file_name,
                "file_size": asset.file_size_bytes,
                "expires_at": expires_at.isoformat(),
            },
        )
        session.add(audit_log)
        # Flush to catch constraint violations before commit
        session.flush()
        session.commit()

        logger.info(
            "Audit log created for download",
            extra={
                "user_id": str(current_user.id),
                "asset_id": str(asset.id),
                "action": AuditAction.DOWNLOAD.value,
            },
        )
    except Exception as e:
        # Rollback to clean up failed audit log transaction
        session.rollback()

        # Log the error with appropriate severity
        logger.error(
            "Failed to create audit log for download",
            extra={
                "user_id": str(current_user.id),
                "asset_id": str(asset.id),
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        # Continue with download despite audit failure (best-effort logging)

    # Return enhanced response with file metadata (Task 1.4, AC: #3)
    return DownloadResponse(
        download_url=url,
        expires_at=expires_at,
        file_name=asset.file_name,
        file_size=asset.file_size_bytes,
        mime_type=asset.mime_type,
    )
