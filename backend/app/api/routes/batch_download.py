"""
Batch Download API Routes (Story 4.4).

Provides endpoint for downloading multiple assets as a single ZIP file.

Features:
- Validates user permissions for all requested assets
- Generates ZIP file with streaming (no memory buffering)
- Stores ZIP temporarily in MinIO (1-hour expiry)
- Returns presigned download URL for direct access
- Comprehensive error handling for missing/inaccessible assets

References:
- Task 1: Create Batch Download Endpoint
- AC: #1, #4, #7, #11, #12
"""

import logging

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, SessionDep
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.models import AuditAction
from app.schemas.batch_download import BatchDownloadRequest, BatchDownloadResponse
from app.services.batch_download_service import BatchDownloadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["batch-download"])


@router.post(
    "/batch-download",
    response_model=BatchDownloadResponse,
    summary="Download multiple assets as ZIP",
    description="""
    Download multiple assets as a single ZIP file.

    **Process:**
    1. Validates user has permission for all requested assets (AC: #1)
    2. Generates a ZIP file containing all assets (AC: #2)
    3. Uses streaming to avoid memory buffering (AC: #3)
    4. Uploads ZIP to temporary storage with 1-hour expiry (AC: #5, #8)
    5. Returns presigned download URL (AC: #4, #7)
    6. Creates audit log entry (AC: #6)

    **Request Validation:**
    - Minimum 1 asset required (AC: #11)
    - Maximum 100 assets per request (AC: #12)
    - No duplicate asset IDs allowed
    - All assets must exist (AC: #10)
    - User must have permission for all assets (AC: #9)

    **ZIP File Details:**
    - Files retain original names
    - ZIP uses DEFLATE compression
    - Stored at: `temp/batch-downloads/{timestamp}-{uuid}.zip`
    - Automatically deleted after 1 hour

    **Permissions:**
    - Owner can download their own assets
    - Admin and Supervisor can download any assets

    **Error Codes:**
    - 400 BAD_REQUEST: Empty list or >100 assets (AC: #11, #12)
    - 403 PERMISSION_DENIED: Lacks permission for one or more assets (AC: #9)
    - 404 ASSET_NOT_FOUND: One or more assets don't exist (AC: #10)
    - 429 TOO_MANY_REQUESTS: Rate limit exceeded

    **Example Request:**
    ```json
    {
      "asset_ids": [
        "550e8400-e29b-41d4-a716-446655440001",
        "550e8400-e29b-41d4-a716-446655440002",
        "550e8400-e29b-41d4-a716-446655440003"
      ]
    }
    ```

    **Example Response:**
    ```json
    {
      "download_url": "https://minio.example.com/assets/temp/batch-downloads/...",
      "expires_at": "2025-12-18T12:00:00Z",
      "file_name": "batch-download-20251218-100000-abc123.zip",
      "file_count": 3,
      "total_size_bytes": 10485760,
      "compressed_size_bytes": 8388608
    }
    ```
    """,
)
@limiter.limit(get_dynamic_rate_limit)
async def batch_download_assets(
    request: Request,
    body: BatchDownloadRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> BatchDownloadResponse:
    """
    Download multiple assets as ZIP (AC: #1-#12).

    Args:
        request: FastAPI request object (for rate limiting and IP extraction)
        body: Batch download request with asset IDs
        session: Database session with tenant context
        current_user: Authenticated user making the request

    Returns:
        BatchDownloadResponse with download URL and metadata

    Raises:
        ValidationError: Invalid request (empty list, >100 assets, duplicates) (422)
        AssetNotFoundError: One or more assets don't exist (404, AC: #10)
        AssetAccessDeniedError: User lacks permission for one or more assets (403, AC: #9)

    References:
        - Task 1: Batch Download Endpoint
        - AC: #1-#12
    """
    # Get client IP for audit logging
    client_ip = get_client_ip(request)

    # Initialize service
    service = BatchDownloadService(
        session=session,
        current_user=current_user,
        ip_address=client_ip,
    )

    # Validate access to all assets (AC: #1, #9, #10)
    # Raises AssetNotFoundError if any asset missing (AC: #10)
    # Raises AssetAccessDeniedError if any asset inaccessible (AC: #9)
    assets = service.validate_assets_access(body.asset_ids)

    logger.info(
        "Starting batch download",
        extra={
            "user_id": str(current_user.id),
            "asset_count": len(assets),
            "asset_ids": [str(id) for id in body.asset_ids],
        },
    )

    # Create ZIP file (AC: #2, #3, #5)
    object_key, total_size, compressed_size = service.create_batch_zip(assets)

    # Generate download URL (AC: #4, #7, #8)
    download_url, expires_at = service.generate_download_url(object_key)

    # Create audit log (AC: #6)
    service._create_audit_log(
        action=AuditAction.BATCH_DOWNLOAD,
        metadata={
            "asset_ids": [str(id) for id in body.asset_ids],
            "file_count": len(assets),
            "total_size_bytes": total_size,
            "compressed_size_bytes": compressed_size,
            "object_key": object_key,
        },
    )

    logger.info(
        "Batch download completed successfully",
        extra={
            "user_id": str(current_user.id),
            "file_count": len(assets),
            "total_size_bytes": total_size,
            "compressed_size_bytes": compressed_size,
            "download_url": download_url,
        },
    )

    # Return response (AC: #4)
    return BatchDownloadResponse(
        download_url=download_url,
        expires_at=expires_at,
        file_name=object_key.split("/")[-1],
        file_count=len(assets),
        total_size_bytes=total_size,
        compressed_size_bytes=compressed_size,
    )
