"""
Signed URL API Routes (Story 3.2, Task 4).

Provides:
- GET /api/v1/assets/{asset_id}/download-url - Generate presigned download URL
- GET /api/v1/assets/{asset_id}/stream-url - Generate presigned stream URL
- POST /api/v1/assets/upload-url - Generate presigned upload URL

References:
- AC: #5 (clients use signed URL to download/upload directly to MinIO)
- AC: #8 (validate user permission before generating URL)
- AC: #9 (response includes URL and expiration timestamp in ISO-8601)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, TenantSessionDep
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.schemas.signed_url import (
    SignedURLResponse,
    UploadURLRequest,
    UploadURLResponse,
)
from app.services.signed_url_service import SignedURLService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["signed-urls"])


@router.get(
    "/{asset_id}/download-url",
    response_model=SignedURLResponse,
    summary="Generate presigned download URL",
    description="""
    Generate a presigned URL for downloading an asset directly from MinIO.

    **Authorization:**
    - User must own the asset, OR
    - User must be Admin/Supervisor (can access any asset)

    **URL Validity:**
    - Download URLs are valid for 1 hour (configurable)
    - URL uses HMAC-SHA256 signature

    **Direct Download:**
    - Client downloads directly from MinIO using the signed URL
    - No API proxying - reduces server load (NFR-P4, NFR-P5, NFR-P6)

    **Returns:**
    - 200 OK with presigned URL and expiration timestamp
    - 403 Forbidden if user lacks permission
    - 404 Not Found if asset does not exist
    - 429 Too Many Requests if rate limit exceeded
    """,
    responses={
        200: {
            "description": "Presigned URL generated successfully",
            "model": SignedURLResponse,
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
async def get_download_url(
    request: Request,
    asset_id: UUID,
    session: TenantSessionDep,
    current_user: CurrentUser,
) -> SignedURLResponse:
    """
    Generate a presigned URL for downloading an asset.

    The URL is valid for 1 hour (configurable).
    Clients should use this URL to download directly from MinIO.
    """
    request_id = getattr(request.state, "request_id", None)
    ip_address = get_client_ip(request)

    logger.info(
        "Download URL request received",
        extra={
            "asset_id": str(asset_id),
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    service = SignedURLService(
        session=session,
        current_user=current_user,
        ip_address=ip_address,
    )

    url, expires_at = service.generate_download_url(
        asset_id=asset_id,
        request_id=request_id,
    )

    return SignedURLResponse(
        url=url,
        expires_at=expires_at,
        type="download",
    )


@router.get(
    "/{asset_id}/stream-url",
    response_model=SignedURLResponse,
    summary="Generate presigned stream URL",
    description="""
    Generate a presigned URL for streaming video/audio assets directly from MinIO.

    **Use Case:**
    - Video players with seek support (HTTP Range requests)
    - Audio streaming
    - Progressive download for large media files

    **Authorization:**
    - User must own the asset, OR
    - User must be Admin/Supervisor (can access any asset)

    **URL Validity:**
    - Stream URLs are valid for 1 hour (configurable)
    - URL supports HTTP Range requests for seeking

    **Returns:**
    - 200 OK with presigned URL and expiration timestamp
    - 403 Forbidden if user lacks permission
    - 404 Not Found if asset does not exist
    """,
    responses={
        200: {
            "description": "Presigned stream URL generated successfully",
            "model": SignedURLResponse,
        },
        403: {"description": "Permission denied"},
        404: {"description": "Asset not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(get_dynamic_rate_limit)
async def get_stream_url(
    request: Request,
    asset_id: UUID,
    session: TenantSessionDep,
    current_user: CurrentUser,
) -> SignedURLResponse:
    """
    Generate a presigned URL for streaming video/audio assets.

    The URL supports HTTP Range requests for seeking.
    Valid for 1 hour (configurable).
    """
    request_id = getattr(request.state, "request_id", None)
    ip_address = get_client_ip(request)

    logger.info(
        "Stream URL request received",
        extra={
            "asset_id": str(asset_id),
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    service = SignedURLService(
        session=session,
        current_user=current_user,
        ip_address=ip_address,
    )

    url, expires_at = service.generate_stream_url(
        asset_id=asset_id,
        request_id=request_id,
    )

    return SignedURLResponse(
        url=url,
        expires_at=expires_at,
        type="stream",
    )


@router.post(
    "/upload-url",
    response_model=UploadURLResponse,
    summary="Generate presigned upload URL",
    description="""
    Generate a presigned URL for uploading a new asset directly to MinIO.

    **Workflow:**
    1. Client requests upload URL with file metadata
    2. Server validates file type and generates presigned PUT URL
    3. Server pre-generates asset ID and object key
    4. Client uploads directly to MinIO using the signed URL
    5. (Future) Client confirms upload to create asset metadata

    **Validation:**
    - MIME type must be in allowed whitelist
    - File name must be valid (no path traversal)

    **URL Validity:**
    - Upload URLs are valid for 15 minutes (short for security)
    - URL allows single PUT request

    **Returns:**
    - 200 OK with presigned URL, expiration, asset_id, and object_key
    - 400 Bad Request if file type not allowed or filename invalid
    - 429 Too Many Requests if rate limit exceeded
    """,
    responses={
        200: {
            "description": "Presigned upload URL generated successfully",
            "model": UploadURLResponse,
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_type": {
                            "summary": "Invalid file type",
                            "value": {
                                "error_code": "INVALID_FILE_TYPE",
                                "message": "MIME type 'application/exe' is not allowed",
                            },
                        },
                        "invalid_filename": {
                            "summary": "Invalid filename",
                            "value": {
                                "error_code": "INVALID_FILENAME",
                                "message": "Filename contains invalid characters",
                            },
                        },
                    }
                }
            },
        },
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(get_dynamic_rate_limit)
async def get_upload_url(
    request: Request,
    body: UploadURLRequest,
    session: TenantSessionDep,
    current_user: CurrentUser,
) -> UploadURLResponse:
    """
    Generate a presigned URL for uploading a new asset.

    The URL is valid for 15 minutes (configurable).
    Clients should use this URL to upload directly to MinIO.
    """
    request_id = getattr(request.state, "request_id", None)
    ip_address = get_client_ip(request)

    logger.info(
        "Upload URL request received",
        extra={
            "file_name": body.file_name,
            "mime_type": body.mime_type,
            "file_size": body.file_size,
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    service = SignedURLService(
        session=session,
        current_user=current_user,
        ip_address=ip_address,
    )

    url, expires_at, asset_id, object_key = service.generate_upload_url(
        file_name=body.file_name,
        mime_type=body.mime_type,
        file_size=body.file_size,
        request_id=request_id,
    )

    return UploadURLResponse(
        url=url,
        expires_at=expires_at,
        type="upload",
        asset_id=asset_id,
        object_key=object_key,
    )
