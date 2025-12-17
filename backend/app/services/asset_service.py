"""
Asset Service (Story 3.1, Task 4; Story 3.3, Task 4).

Orchestrates file upload workflow:
1. Validate file (MIME type, size)
2. Upload to MinIO
3. Create asset metadata in PostgreSQL
4. Create audit log entry
5. Handle transactional consistency

Story 3.3 additions:
- ZIP archive upload with streaming extraction
- Batch metadata creation with transactional consistency
- Audit logging for ZIP uploads

References:
- AC: #3 (upload to MinIO)
- AC: #4 (create metadata in PostgreSQL)
- AC: #5 (checksum calculation)
- AC: #6 (return 201 with asset metadata)
- AC: #8 (audit logging)
- Story 3.3 AC: #8 (asset metadata for each extracted file)
- Story 3.3 AC: #11 (audit logs for all operations)
"""

import logging
import uuid
from typing import BinaryIO

from fastapi import UploadFile
from sqlmodel import Session

from app.core.config import settings
from app.core.exceptions import (
    DangerousFileError,
    ExecutableDetectedError,
    ExtensionMismatchError,
    FileTooLargeError,
    InvalidFilenameError,
    InvalidFileTypeError,
    UploadError,
)
from app.core.minio_client import (
    delete_object,
    ensure_bucket_exists,
    generate_object_key,
    put_object_streaming,
)
from app.models import (
    Asset,
    AssetCreate,
    AuditAction,
    AuditLog,
    User,
)
from app.repositories.asset_repository import AssetRepository
from app.services.file_validation_service import (
    get_allowed_mime_types,
    get_safe_filename,
    get_size_limit_for_mime_type,
    validate_file,
)
from app.services.zip_extraction_service import (
    InvalidZipError,
    ZipBombError,
    ZipExtractionResult,
    ZipExtractionService,
)

logger = logging.getLogger(__name__)


class AssetService:
    """
    Service for asset upload operations.

    Handles the complete upload workflow with transactional consistency.
    If metadata creation fails, the MinIO upload is rolled back.
    """

    def __init__(self, session: Session, current_user: User):
        """
        Initialize AssetService.

        Args:
            session: Database session with tenant context
            current_user: Authenticated user performing the upload
        """
        self.session = session
        self.current_user = current_user
        self.repository = AssetRepository(session)

    def _get_tenant_type(self) -> str:
        """
        Get tenant type string for object key generation.

        Returns:
            Tenant type as lowercase string (publisher, school, teacher, student)
        """
        if self.current_user.tenant:
            return self.current_user.tenant.tenant_type.value.lower()

        # Fallback based on user role
        role = self.current_user.role.value.lower()
        if role in ("publisher", "school", "teacher", "student"):
            return role
        return "publisher"  # Default for admin/supervisor

    async def create_asset(
        self,
        file: UploadFile,
        ip_address: str,
        request_id: str | None = None,
    ) -> Asset:
        """
        Create a new asset from uploaded file (AC: #1-#8).

        Workflow:
        1. Validate file (MIME type, size, filename)
        2. Generate asset ID and object key
        3. Upload to MinIO with checksum calculation
        4. Create asset metadata in PostgreSQL
        5. Create audit log entry
        6. Return created asset

        If step 4 fails, step 3 is rolled back (MinIO upload deleted).

        Args:
            file: FastAPI UploadFile object
            ip_address: Client IP address for audit logging
            request_id: Optional request ID for tracing

        Returns:
            Created Asset model instance

        Raises:
            InvalidFileTypeError: If MIME type not in whitelist (AC: #10)
            FileTooLargeError: If file exceeds size limit (AC: #11)
            UploadError: If upload fails for other reasons
        """
        # Get file metadata
        filename = file.filename or "unnamed_file"
        mime_type = file.content_type or "application/octet-stream"

        # Get file size - need to read the file to know size
        # This is a limitation of FastAPI's UploadFile
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)  # Reset for later reading

        logger.info(
            "Processing upload request",
            extra={
                "file_name": filename,
                "mime_type": mime_type,
                "size_bytes": file_size,
                "user_id": str(self.current_user.id),
                "request_id": request_id,
            },
        )

        # Step 1: Validate file (AC: #1, #2) with magic bytes check (Security)
        validation_result = validate_file(
            filename, mime_type, file_size, file_content=file_content
        )
        if not validation_result.is_valid:
            if validation_result.error_code == "INVALID_FILE_TYPE":
                raise InvalidFileTypeError(
                    mime_type=mime_type,
                    allowed_types=get_allowed_mime_types(),
                    request_id=request_id,
                )
            elif validation_result.error_code == "FILE_TOO_LARGE":
                raise FileTooLargeError(
                    size_bytes=file_size,
                    max_size_bytes=get_size_limit_for_mime_type(mime_type),
                    mime_type=mime_type,
                    request_id=request_id,
                )
            elif validation_result.error_code in (
                "INVALID_FILENAME",
                "FILENAME_TOO_LONG",
            ):
                raise InvalidFilenameError(
                    filename=filename,
                    reason=validation_result.error_message or "Invalid filename",
                    request_id=request_id,
                )
            elif validation_result.error_code == "DANGEROUS_FILENAME":
                # Story 3.4, AC: #9 - Dangerous filename patterns
                raise DangerousFileError(
                    filename=filename,
                    reason=validation_result.error_message
                    or "Dangerous filename pattern",
                    pattern_type=validation_result.details.get(
                        "pattern_type", "unknown"
                    )
                    if validation_result.details
                    else "unknown",
                    request_id=request_id,
                )
            elif validation_result.error_code == "EXTENSION_MISMATCH":
                # Story 3.4, AC: #2 - Extension-MIME mismatch
                details = validation_result.details or {}
                raise ExtensionMismatchError(
                    filename=filename,
                    extension=details.get("extension", "unknown"),
                    claimed_mime=details.get("claimed_mime", mime_type),
                    expected_mimes=details.get("expected_mimes", []),
                    request_id=request_id,
                )
            elif validation_result.error_code == "EXECUTABLE_DETECTED":
                # Story 3.4, AC: #10 - Executable format detection
                raise ExecutableDetectedError(
                    format_name=validation_result.details.get("format", "Unknown")
                    if validation_result.details
                    else "Unknown",
                    claimed_mime=mime_type,
                    request_id=request_id,
                )
            else:
                raise UploadError(
                    message=validation_result.error_message or "Validation failed",
                    details=validation_result.details,
                    request_id=request_id,
                )

        # Step 2: Generate asset ID and object key
        asset_id = uuid.uuid4()
        safe_filename = get_safe_filename(filename)
        tenant_type = self._get_tenant_type()
        tenant_id = self.current_user.tenant_id

        if not tenant_id:
            raise UploadError(
                message="User has no tenant assigned",
                details={"user_id": str(self.current_user.id)},
                request_id=request_id,
            )

        object_key = generate_object_key(
            tenant_type=tenant_type,
            tenant_id=tenant_id,
            asset_id=asset_id,
            file_name=safe_filename,
        )

        bucket = settings.MINIO_BUCKET_NAME

        # Step 3: Upload to MinIO (AC: #3, #5, #7)
        try:
            # Ensure bucket exists
            ensure_bucket_exists(bucket=bucket)

            # Upload file with checksum calculation
            from io import BytesIO

            file_stream = BytesIO(file_content)
            etag, checksum = put_object_streaming(
                bucket=bucket,
                object_key=object_key,
                data=file_stream,
                length=file_size,
                content_type=mime_type,
            )

            logger.info(
                "File uploaded to MinIO",
                extra={
                    "object_key": object_key,
                    "bucket": bucket,
                    "checksum": checksum,
                    "etag": etag,
                    "request_id": request_id,
                },
            )

        except Exception as e:
            logger.error(
                "MinIO upload failed",
                extra={
                    "object_key": object_key,
                    "error": str(e),
                    "request_id": request_id,
                },
            )
            raise UploadError(
                message="Failed to upload file to storage",
                details={"error": str(e)},
                request_id=request_id,
            )

        # Step 4: Create asset metadata in PostgreSQL (AC: #4)
        try:
            asset_data = AssetCreate(
                bucket=bucket,
                object_key=object_key,
                file_name=safe_filename,
                file_size_bytes=file_size,
                mime_type=mime_type,
                checksum=checksum,
                tenant_id=tenant_id,
            )

            asset = self.repository.create(
                data=asset_data,
                user_id=self.current_user.id,
            )

            # Override the auto-generated ID with our pre-generated one
            # This ensures consistency between MinIO path and DB record
            asset.id = asset_id
            self.session.add(asset)
            self.session.commit()
            self.session.refresh(asset)

            logger.info(
                "Asset metadata created",
                extra={
                    "asset_id": str(asset.id),
                    "object_key": object_key,
                    "request_id": request_id,
                },
            )

        except Exception as e:
            # Rollback MinIO upload on metadata creation failure (AC: #6)
            logger.error(
                "Metadata creation failed, rolling back MinIO upload",
                extra={
                    "object_key": object_key,
                    "error": str(e),
                    "request_id": request_id,
                },
            )
            try:
                delete_object(bucket=bucket, object_key=object_key)
            except Exception as delete_error:
                logger.error(
                    "Failed to rollback MinIO upload",
                    extra={
                        "object_key": object_key,
                        "error": str(delete_error),
                        "request_id": request_id,
                    },
                )

            raise UploadError(
                message="Failed to create asset metadata",
                details={"error": str(e)},
                request_id=request_id,
            )

        # Step 5: Create audit log (AC: #8)
        try:
            audit_log = AuditLog(
                user_id=self.current_user.id,
                asset_id=asset.id,
                action=AuditAction.ASSET_UPLOAD,
                ip_address=ip_address,
                metadata_json={
                    "file_name": safe_filename,
                    "mime_type": mime_type,
                    "file_size_bytes": file_size,
                    "checksum": checksum,
                    "object_key": object_key,
                    "tenant_id": str(tenant_id),
                },
            )
            self.session.add(audit_log)
            self.session.commit()

            logger.info(
                "Audit log created for upload",
                extra={
                    "asset_id": str(asset.id),
                    "action": AuditAction.ASSET_UPLOAD.value,
                    "request_id": request_id,
                },
            )

        except Exception as e:
            # Audit log failure is logged but doesn't fail the upload
            logger.error(
                "Failed to create audit log for upload",
                extra={
                    "asset_id": str(asset.id),
                    "error": str(e),
                    "request_id": request_id,
                },
            )

        return asset

    async def create_assets_from_zip(
        self,
        zip_file: BinaryIO,
        ip_address: str,
        request_id: str | None = None,
    ) -> tuple[list[Asset], ZipExtractionResult]:
        """
        Create assets from ZIP archive extraction (Story 3.3, AC: #8, #11).

        Workflow:
        1. Extract ZIP contents using ZipExtractionService (files uploaded to MinIO)
        2. Create asset metadata records in PostgreSQL (batch)
        3. Create audit log entries
        4. Handle transactional consistency (rollback on failure)

        Args:
            zip_file: Binary file-like object containing ZIP data
            ip_address: Client IP address for audit logging
            request_id: Optional request ID for tracing

        Returns:
            Tuple of (created_assets, extraction_result)

        Raises:
            InvalidZipError: If ZIP file is invalid/corrupt (AC: #13)
            ZipBombError: If ZIP bomb detected
            UploadError: If metadata creation fails
        """
        tenant_type = self._get_tenant_type()
        tenant_id = self.current_user.tenant_id

        if not tenant_id:
            raise UploadError(
                message="User has no tenant assigned",
                details={"user_id": str(self.current_user.id)},
                request_id=request_id,
            )

        logger.info(
            "Processing ZIP upload request",
            extra={
                "user_id": str(self.current_user.id),
                "tenant_id": str(tenant_id),
                "request_id": request_id,
            },
        )

        # Step 1: Extract ZIP and upload files to MinIO
        extraction_service = ZipExtractionService(
            tenant_type=tenant_type,
            tenant_id=tenant_id,
            user_id=self.current_user.id,
            bucket=settings.MINIO_BUCKET_NAME,
        )

        try:
            extraction_result = extraction_service.extract_and_upload(
                zip_file=zip_file,
                request_id=request_id,
            )
        except (InvalidZipError, ZipBombError):
            # Re-raise ZIP-specific errors
            raise
        except Exception as e:
            logger.error(
                "ZIP extraction failed",
                extra={
                    "error": str(e),
                    "request_id": request_id,
                },
            )
            raise UploadError(
                message="Failed to extract ZIP archive",
                details={"error": str(e)},
                request_id=request_id,
            )

        # Step 2: Create asset metadata records in PostgreSQL
        created_assets: list[Asset] = []

        try:
            for extracted in extraction_result.extracted_assets:
                asset_data = AssetCreate(
                    bucket=settings.MINIO_BUCKET_NAME,
                    object_key=extracted.object_key,
                    file_name=extracted.file_name,
                    file_size_bytes=extracted.file_size,
                    mime_type=extracted.mime_type,
                    checksum=extracted.checksum,
                    tenant_id=tenant_id,
                )

                asset = self.repository.create(
                    data=asset_data,
                    user_id=self.current_user.id,
                )

                # Override auto-generated ID with pre-generated one
                asset.id = extracted.asset_id
                self.session.add(asset)
                created_assets.append(asset)

            # Commit all assets in single transaction
            self.session.commit()

            # Refresh all assets to get final state
            for asset in created_assets:
                self.session.refresh(asset)

            logger.info(
                "Asset metadata created for ZIP extraction",
                extra={
                    "asset_count": len(created_assets),
                    "request_id": request_id,
                },
            )

        except Exception as e:
            # Rollback database transaction
            self.session.rollback()

            # Rollback MinIO uploads
            logger.error(
                "Metadata creation failed, rolling back MinIO uploads",
                extra={
                    "asset_count": len(extraction_result.extracted_assets),
                    "error": str(e),
                    "request_id": request_id,
                },
            )

            extraction_service.rollback_extraction(extraction_result, request_id)

            raise UploadError(
                message="Failed to create asset metadata for ZIP extraction",
                details={"error": str(e)},
                request_id=request_id,
            )

        # Step 3: Create audit logs
        try:
            # Create batch audit log for ZIP upload
            batch_audit_log = AuditLog(
                user_id=self.current_user.id,
                asset_id=None,  # No single asset for batch operation
                action=AuditAction.ASSET_ZIP_UPLOAD,
                ip_address=ip_address,
                metadata_json={
                    "extracted_count": extraction_result.extracted_count,
                    "skipped_count": extraction_result.skipped_count,
                    "failed_count": extraction_result.failed_count,
                    "total_size_bytes": extraction_result.total_size_bytes,
                    "tenant_id": str(tenant_id),
                    "asset_ids": [str(a.id) for a in created_assets],
                },
            )
            self.session.add(batch_audit_log)

            # Create individual audit logs for each extracted asset
            for asset in created_assets:
                individual_audit = AuditLog(
                    user_id=self.current_user.id,
                    asset_id=asset.id,
                    action=AuditAction.ASSET_UPLOAD,
                    ip_address=ip_address,
                    metadata_json={
                        "file_name": asset.file_name,
                        "mime_type": asset.mime_type,
                        "file_size_bytes": asset.file_size_bytes,
                        "checksum": asset.checksum,
                        "object_key": asset.object_key,
                        "tenant_id": str(tenant_id),
                        "source": "zip_extraction",
                    },
                )
                self.session.add(individual_audit)

            self.session.commit()

            logger.info(
                "Audit logs created for ZIP upload",
                extra={
                    "batch_action": AuditAction.ASSET_ZIP_UPLOAD.value,
                    "individual_count": len(created_assets),
                    "request_id": request_id,
                },
            )

        except Exception as e:
            # Audit log failure is logged but doesn't fail the upload
            logger.error(
                "Failed to create audit logs for ZIP upload",
                extra={
                    "asset_count": len(created_assets),
                    "error": str(e),
                    "request_id": request_id,
                },
            )

        return created_assets, extraction_result
