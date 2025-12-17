"""
Upload API Routes (Story 3.1, Task 6).

Provides:
- POST /api/v1/assets/upload - Single file upload endpoint

References:
- AC: #1 (validate file type and size)
- AC: #6 (return 201 Created with asset metadata)
- AC: #9 (file immediately accessible)
"""

import logging

from fastapi import APIRouter, File, Request, UploadFile

from app.api.deps import CurrentUser, TenantSessionDep
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.schemas.asset import AssetResponse
from app.services.asset_service import AssetService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post(
    "/upload",
    response_model=AssetResponse,
    status_code=201,
    summary="Upload a single file",
    description="""
    Upload a single file to user's storage area.

    **Validation:**
    - MIME type must be in allowed whitelist (AC: #2)
    - File size must not exceed type-specific limits (AC: #1)
      - Videos: 10GB max
      - Images: 500MB max
      - Other: 5GB max

    **Process:**
    1. Validates file type and size
    2. Uploads to MinIO with streaming (no full memory buffering)
    3. Calculates MD5 checksum during upload
    4. Creates asset metadata in PostgreSQL
    5. Creates audit log entry

    **Returns:**
    - 201 Created with asset metadata on success
    - 400 Bad Request with INVALID_FILE_TYPE if MIME type not allowed
    - 400 Bad Request with FILE_TOO_LARGE if size exceeds limit
    - 401 Unauthorized if not authenticated
    - 429 Too Many Requests if rate limit exceeded
    """,
    responses={
        201: {
            "description": "File uploaded successfully",
            "model": AssetResponse,
        },
        400: {
            "description": "Validation error (invalid type or size)",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_type": {
                            "summary": "Invalid file type",
                            "value": {
                                "error_code": "INVALID_FILE_TYPE",
                                "message": "File type 'application/exe' is not allowed",
                                "details": {"mime_type": "application/exe"},
                            },
                        },
                        "file_too_large": {
                            "summary": "File too large",
                            "value": {
                                "error_code": "FILE_TOO_LARGE",
                                "message": "File size exceeds maximum",
                                "details": {"size_bytes": 600000000},
                            },
                        },
                    }
                }
            },
        },
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(get_dynamic_rate_limit)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="File to upload"),
    session: TenantSessionDep = None,  # type: ignore[assignment]
    current_user: CurrentUser = None,  # type: ignore[assignment]
) -> AssetResponse:
    """
    Upload a single file to user's storage area.

    - Validates file type and size
    - Uploads to MinIO with streaming (no full memory buffering)
    - Creates asset metadata in PostgreSQL
    - Returns asset details with checksum

    Rate limits apply based on user role:
    - Admin/Supervisor: Unlimited
    - Publisher/School: 1000/hour
    - Teacher: 500/hour
    - Student: 100/hour
    """
    # Get request ID for tracing
    request_id = getattr(request.state, "request_id", None)

    # Get client IP for audit logging
    ip_address = get_client_ip(request)

    logger.info(
        "Upload request received",
        extra={
            "file_name": file.filename,
            "content_type": file.content_type,
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    # Create asset service and process upload
    asset_service = AssetService(session=session, current_user=current_user)

    asset = await asset_service.create_asset(
        file=file,
        ip_address=ip_address,
        request_id=request_id,
    )

    logger.info(
        "Upload completed successfully",
        extra={
            "asset_id": str(asset.id),
            "file_name": asset.file_name,
            "size_bytes": asset.file_size_bytes,
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    # Return response using the model's alias for id -> asset_id
    return AssetResponse(
        id=asset.id,
        file_name=asset.file_name,
        file_size_bytes=asset.file_size_bytes,
        mime_type=asset.mime_type,
        checksum=asset.checksum,
        object_key=asset.object_key,
        bucket=asset.bucket,
        user_id=asset.user_id,
        tenant_id=asset.tenant_id,
        is_deleted=asset.is_deleted,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )
