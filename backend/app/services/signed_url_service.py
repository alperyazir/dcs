"""
Signed URL Service (Story 3.2, Task 3).

Provides:
- Presigned URL generation for download/upload/stream operations
- Permission validation before URL generation (AC: #8)
- Audit logging for signed URL operations
- Tenant isolation enforcement

References:
- AC: #1 (generate presigned URLs using MinIO SDK)
- AC: #8 (validate user permission before generating URL)
- AC: #9 (return URL with ISO-8601 expiration)
"""

import logging
import uuid
from datetime import datetime
from uuid import UUID

from sqlmodel import Session

from app.core.config import settings
from app.core.exceptions import AssetAccessDeniedError, AssetNotFoundError
from app.core.minio_client import (
    generate_object_key,
    generate_presigned_download_url,
    generate_presigned_upload_url,
)
from app.models import Asset, AuditAction, AuditLog, User, UserRole
from app.repositories.asset_repository import AssetRepository
from app.services.file_validation_service import get_safe_filename

logger = logging.getLogger(__name__)


class SignedURLService:
    """
    Service for generating signed URLs with permission validation.

    Handles the complete URL generation workflow:
    1. Validate asset exists
    2. Check user permission (ownership or admin bypass)
    3. Generate presigned URL via MinIO client
    4. Create audit log entry
    5. Return URL with expiration timestamp
    """

    def __init__(
        self,
        session: Session,
        current_user: User,
        ip_address: str | None = None,
    ):
        """
        Initialize SignedURLService.

        Args:
            session: Database session with tenant context
            current_user: Authenticated user requesting the URL
            ip_address: Client IP address for audit logging
        """
        self.session = session
        self.current_user = current_user
        self.ip_address = ip_address or "unknown"
        self.asset_repo = AssetRepository(session)

    def _check_asset_access(
        self,
        asset: Asset,
        request_id: str | None = None,
    ) -> None:
        """
        Check if current user can access the asset (AC: #8, Task 7).

        Permission hierarchy:
        1. Admin/Supervisor can access all assets
        2. Asset owner can access their own assets
        3. Same-tenant users can access if granted (future: asset_permissions)

        Args:
            asset: Asset to check access for
            request_id: Optional request ID for error responses

        Raises:
            AssetAccessDeniedError: If user lacks permission
        """
        # Admin/Supervisor bypass - can access all assets (Task 7.2)
        if self.current_user.role in (UserRole.ADMIN, UserRole.SUPERVISOR):
            logger.debug(
                "Admin/Supervisor bypass for asset access",
                extra={
                    "user_id": str(self.current_user.id),
                    "asset_id": str(asset.id),
                    "role": self.current_user.role.value,
                },
            )
            return

        # Tenant isolation check (Task 7.3)
        if asset.tenant_id != self.current_user.tenant_id:
            raise AssetAccessDeniedError(
                asset_id=asset.id,
                user_id=self.current_user.id,
                reason="Cross-tenant access is not permitted",
                request_id=request_id,
            )

        # Ownership check (Task 7.1)
        if asset.user_id != self.current_user.id:
            # TODO: Check asset_permissions table for granted access (Story 7.3)
            # For now, only asset owners can access
            raise AssetAccessDeniedError(
                asset_id=asset.id,
                user_id=self.current_user.id,
                reason="You do not have permission to access this asset",
                request_id=request_id,
            )

    def _create_audit_log(
        self,
        asset_id: UUID,
        action: AuditAction,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """
        Create audit log entry for signed URL generation.

        Args:
            asset_id: Asset ID the URL was generated for
            action: Audit action type
            metadata: Additional metadata to log
        """
        try:
            audit_log = AuditLog(
                user_id=self.current_user.id,
                asset_id=asset_id,
                action=action,
                ip_address=self.ip_address,
                metadata_json=metadata or {},
            )
            self.session.add(audit_log)
            self.session.commit()

            logger.info(
                "Audit log created for signed URL generation",
                extra={
                    "user_id": str(self.current_user.id),
                    "asset_id": str(asset_id),
                    "action": action.value,
                },
            )
        except Exception as e:
            # Audit log failure should not fail the URL generation
            logger.error(
                "Failed to create audit log for signed URL",
                extra={
                    "user_id": str(self.current_user.id),
                    "asset_id": str(asset_id),
                    "action": action.value,
                    "error": str(e),
                },
            )

    def generate_download_url(
        self,
        asset_id: UUID,
        request_id: str | None = None,
    ) -> tuple[str, datetime]:
        """
        Generate presigned download URL for an asset (AC: #1, #3, #8, #9).

        Args:
            asset_id: ID of the asset to generate download URL for
            request_id: Optional request ID for error responses

        Returns:
            Tuple of (presigned_url, expiration_datetime)

        Raises:
            AssetNotFoundError: If asset does not exist (Task 7.5)
            AssetAccessDeniedError: If user lacks permission (Task 7.4)
        """
        import time

        start_time = time.perf_counter()

        # Get asset (Task 7.5 - returns 404 if not found)
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(asset_id=asset_id, request_id=request_id)

        # Check if asset is soft-deleted (Story 4.1 Code Review Fix #5)
        if asset.is_deleted:
            raise AssetNotFoundError(asset_id=asset_id, request_id=request_id)

        # Check permission (AC: #8)
        self._check_asset_access(asset, request_id)

        # Generate presigned URL (AC: #1, #3)
        url, expires_at = generate_presigned_download_url(
            bucket=asset.bucket,
            object_key=asset.object_key,
        )

        # Audit log
        self._create_audit_log(
            asset_id=asset.id,
            action=AuditAction.SIGNED_URL_DOWNLOAD,
            metadata={
                "url_type": "download",
                "expires_at": expires_at.isoformat(),
            },
        )

        # Calculate timing (Story 4.1, Task 3.4 - NFR-P2: <100ms requirement)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Validate NFR-P2 performance requirement (Story 4.1 Code Review Fix #6)
        if elapsed_ms > 100:
            logger.warning(
                "Download URL generation exceeded NFR-P2 (<100ms)",
                extra={
                    "asset_id": str(asset_id),
                    "user_id": str(self.current_user.id),
                    "generation_time_ms": round(elapsed_ms, 2),
                    "nfr_threshold_ms": 100,
                    "exceeded_by_ms": round(elapsed_ms - 100, 2),
                },
            )

        logger.info(
            "Download URL generated",
            extra={
                "asset_id": str(asset_id),
                "user_id": str(self.current_user.id),
                "expires_at": expires_at.isoformat(),
                "generation_time_ms": round(elapsed_ms, 2),
            },
        )

        return url, expires_at

    def generate_stream_url(
        self,
        asset_id: UUID,
        request_id: str | None = None,
    ) -> tuple[str, datetime]:
        """
        Generate presigned stream URL for video/audio assets.

        Uses stream-specific expiration time (same as download by default).
        Supports HTTP Range requests for seeking in video/audio players.

        Args:
            asset_id: ID of the asset to generate stream URL for
            request_id: Optional request ID for error responses

        Returns:
            Tuple of (presigned_url, expiration_datetime)

        Raises:
            AssetNotFoundError: If asset does not exist
            AssetAccessDeniedError: If user lacks permission
        """
        # Get asset
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(asset_id=asset_id, request_id=request_id)

        # Check permission
        self._check_asset_access(asset, request_id)

        # Generate presigned URL with stream expiration
        url, expires_at = generate_presigned_download_url(
            bucket=asset.bucket,
            object_key=asset.object_key,
            expires_seconds=settings.PRESIGNED_URL_STREAM_EXPIRES_SECONDS,
        )

        # Audit log (Story 4.2, Task 4: Use dedicated STREAM action)
        self._create_audit_log(
            asset_id=asset.id,
            action=AuditAction.STREAM,
            metadata={
                "url_type": "stream",
                "mime_type": asset.mime_type,
                "expires_at": expires_at.isoformat(),
            },
        )

        logger.info(
            "Stream URL generated",
            extra={
                "asset_id": str(asset_id),
                "user_id": str(self.current_user.id),
                "mime_type": asset.mime_type,
                "expires_at": expires_at.isoformat(),
            },
        )

        return url, expires_at

    def generate_upload_url(
        self,
        file_name: str,
        mime_type: str,
        file_size: int,
        request_id: str | None = None,
    ) -> tuple[str, datetime, UUID, str]:
        """
        Generate presigned upload URL for a new asset (AC: #1, #2, #10).

        Pre-generates asset ID and object key so client can upload directly
        to the correct tenant-isolated path in MinIO.

        Args:
            file_name: Original filename
            mime_type: MIME type of the file
            file_size: Size of the file in bytes
            request_id: Optional request ID for error responses

        Returns:
            Tuple of (presigned_url, expiration_datetime, asset_id, object_key)

        Raises:
            UploadError: If tenant not assigned to user
        """
        from app.core.exceptions import UploadError

        # Validate user has a tenant
        if not self.current_user.tenant_id:
            raise UploadError(
                message="User has no tenant assigned",
                details={"user_id": str(self.current_user.id)},
                request_id=request_id,
            )

        # Get tenant type for object key
        tenant_type = self._get_tenant_type()

        # Pre-generate asset ID
        asset_id = uuid.uuid4()

        # Sanitize filename
        safe_filename = get_safe_filename(file_name)

        # Generate object key with tenant isolation (AC: #10)
        object_key = generate_object_key(
            tenant_type=tenant_type,
            tenant_id=self.current_user.tenant_id,
            asset_id=asset_id,
            file_name=safe_filename,
        )

        # Generate presigned upload URL (AC: #1, #2)
        url, expires_at = generate_presigned_upload_url(
            bucket=settings.MINIO_BUCKET_NAME,
            object_key=object_key,
        )

        # Audit log
        audit_log = AuditLog(
            user_id=self.current_user.id,
            asset_id=None,  # Asset not created yet
            action=AuditAction.SIGNED_URL_UPLOAD,
            ip_address=self.ip_address,
            metadata_json={
                "url_type": "upload",
                "file_name": safe_filename,
                "mime_type": mime_type,
                "file_size": file_size,
                "object_key": object_key,
                "pre_generated_asset_id": str(asset_id),
                "expires_at": expires_at.isoformat(),
            },
        )
        self.session.add(audit_log)
        self.session.commit()

        logger.info(
            "Upload URL generated",
            extra={
                "asset_id": str(asset_id),
                "user_id": str(self.current_user.id),
                "file_name": safe_filename,
                "mime_type": mime_type,
                "file_size": file_size,
                "object_key": object_key,
                "expires_at": expires_at.isoformat(),
            },
        )

        return url, expires_at, asset_id, object_key

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
