"""
Upload API Routes (Story 3.1, Task 6; Story 3.3, Task 5).

Provides:
- POST /api/v1/assets/upload - Single file upload endpoint
- POST /api/v1/assets/upload-zip - ZIP archive upload with streaming extraction

References:
- Story 3.1 AC: #1 (validate file type and size)
- Story 3.1 AC: #6 (return 201 Created with asset metadata)
- Story 3.1 AC: #9 (file immediately accessible)
- Story 3.3 AC: #1 (POST /api/v1/assets/upload-zip accepts ZIP archives)
- Story 3.3 AC: #2 (publisher/teacher authentication required)
- Story 3.3 AC: #10 (return extraction results with counts and created assets)
"""

import logging
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.api.deps import CurrentUser, TenantSessionDep
from app.core.config import settings
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.models import UserRole
from app.schemas.asset import AssetResponse
from app.schemas.zip_upload import (
    FailedFileInfo,
    SkippedFileInfo,
    ZipUploadResponse,
)
from app.services.asset_service import AssetService
from app.services.zip_extraction_service import InvalidZipError, ZipBombError

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


@router.post(
    "/upload-zip",
    response_model=ZipUploadResponse,
    status_code=201,
    summary="Upload and extract a ZIP archive",
    description="""
    Upload a ZIP archive and extract its contents to user's storage area.

    **Authorization:** Only publishers and teachers can upload ZIP archives (AC: #2).

    **Process:**
    1. Validates user role (publisher/teacher only)
    2. Validates ZIP file format and size
    3. Extracts contents with streaming (no full memory buffering)
    4. Filters system files (.DS_Store, __MACOSX/, etc.) (AC: #4)
    5. Validates each extracted file (MIME type, size)
    6. Uploads valid files to MinIO preserving folder structure (AC: #7)
    7. Creates asset metadata for each extracted file (AC: #8)
    8. Creates audit log entries (AC: #11)

    **ZIP Limits:**
    - Maximum ZIP file size: 10GB
    - Maximum extracted files: 1000
    - Maximum total extracted size: 50GB

    **Returns:**
    - 201 Created with extraction results on success
    - 400 Bad Request with INVALID_ZIP_FILE if ZIP is corrupt (AC: #13)
    - 400 Bad Request with ZIP_BOMB_DETECTED if zip bomb suspected
    - 401 Unauthorized if not authenticated
    - 403 Forbidden if user role not authorized (AC: #14)
    - 413 Request Entity Too Large if ZIP exceeds size limit
    - 429 Too Many Requests if rate limit exceeded
    """,
    responses={
        201: {
            "description": "ZIP extracted successfully",
            "model": ZipUploadResponse,
        },
        400: {
            "description": "Invalid ZIP file or zip bomb detected",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_zip": {
                            "summary": "Invalid ZIP file",
                            "value": {
                                "error_code": "INVALID_ZIP_FILE",
                                "message": "Invalid or corrupt ZIP file",
                            },
                        },
                        "zip_bomb": {
                            "summary": "ZIP bomb detected",
                            "value": {
                                "error_code": "ZIP_BOMB_DETECTED",
                                "message": "Possible zip bomb detected",
                            },
                        },
                    }
                }
            },
        },
        401: {"description": "Not authenticated"},
        403: {"description": "User role not authorized for ZIP uploads"},
        413: {"description": "ZIP file too large"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(get_dynamic_rate_limit)
async def upload_zip(
    request: Request,
    file: UploadFile = File(..., description="ZIP archive to upload and extract"),
    session: TenantSessionDep = None,  # type: ignore[assignment]
    current_user: CurrentUser = None,  # type: ignore[assignment]
) -> ZipUploadResponse:
    """
    Upload a ZIP archive and extract its contents.

    - Only publishers and teachers can upload ZIP archives
    - Extracts contents with streaming (no full memory buffering)
    - Filters system files automatically
    - Preserves folder structure as MinIO prefixes
    - Creates asset metadata for each extracted file

    Rate limits apply based on user role.
    """
    # Get request ID for tracing
    request_id = getattr(request.state, "request_id", None)

    # Get client IP for audit logging
    ip_address = get_client_ip(request)

    # AC: #2, #14 - Validate user role (only publisher/teacher can upload ZIP)
    allowed_roles = {
        UserRole.ADMIN,
        UserRole.SUPERVISOR,
        UserRole.PUBLISHER,
        UserRole.TEACHER,
    }
    if current_user.role not in allowed_roles:
        logger.warning(
            "ZIP upload rejected - unauthorized role",
            extra={
                "user_id": str(current_user.id),
                "user_role": current_user.role.value,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "UNAUTHORIZED_ROLE",
                "message": "Only publishers and teachers can upload ZIP archives",
            },
        )

    # Validate content type
    content_type = file.content_type or ""
    if content_type not in ("application/zip", "application/x-zip-compressed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_FILE_TYPE",
                "message": f"Expected ZIP file, got '{content_type}'",
            },
        )

    logger.info(
        "ZIP upload request received",
        extra={
            "file_name": file.filename,
            "content_type": file.content_type,
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    # Read ZIP file content
    zip_content = await file.read()
    zip_size = len(zip_content)

    # Validate ZIP size
    if zip_size > settings.MAX_ZIP_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "ZIP_FILE_TOO_LARGE",
                "message": f"ZIP file size ({zip_size} bytes) exceeds maximum "
                f"({settings.MAX_ZIP_FILE_SIZE} bytes)",
            },
        )

    # Create asset service and process ZIP upload
    asset_service = AssetService(session=session, current_user=current_user)

    try:
        # Create BytesIO from content for streaming
        zip_stream = BytesIO(zip_content)

        created_assets, extraction_result = await asset_service.create_assets_from_zip(
            zip_file=zip_stream,
            ip_address=ip_address,
            request_id=request_id,
        )

    except InvalidZipError as e:
        logger.warning(
            "Invalid ZIP file",
            extra={
                "error": str(e),
                "user_id": str(current_user.id),
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": e.error_code,
                "message": e.message,
            },
        )
    except ZipBombError as e:
        logger.warning(
            "Zip bomb detected",
            extra={
                "entry_name": e.entry_name,
                "compression_ratio": e.compression_ratio,
                "user_id": str(current_user.id),
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": e.error_code,
                "message": e.message,
            },
        )

    logger.info(
        "ZIP upload completed successfully",
        extra={
            "extracted_count": extraction_result.extracted_count,
            "skipped_count": extraction_result.skipped_count,
            "failed_count": extraction_result.failed_count,
            "total_size_bytes": extraction_result.total_size_bytes,
            "user_id": str(current_user.id),
            "request_id": request_id,
        },
    )

    # Build response
    asset_responses = [
        AssetResponse(
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
        for asset in created_assets
    ]

    skipped_files = [
        SkippedFileInfo(file_name=s.file_name, reason=s.reason)
        for s in extraction_result.skipped_files
    ]

    failed_files = [
        FailedFileInfo(
            file_name=f.file_name,
            error_code=f.error_code,
            message=f.message,
        )
        for f in extraction_result.failed_files
    ]

    return ZipUploadResponse(
        extracted_count=extraction_result.extracted_count,
        skipped_count=extraction_result.skipped_count,
        failed_count=extraction_result.failed_count,
        total_size_bytes=extraction_result.total_size_bytes,
        assets=asset_responses,
        skipped_files=skipped_files,
        failed_files=failed_files,
    )
