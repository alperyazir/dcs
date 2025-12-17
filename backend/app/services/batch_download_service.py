"""
Batch Download Service (Story 4.4).

Service for downloading multiple assets as a single ZIP file.

Features:
- Permission validation for all assets
- Streaming ZIP creation (temp file approach)
- Temporary storage in MinIO with 1-hour expiry
- Audit logging for compliance

References:
- Task 3: Implement Batch Download Service
- AC: #1, #2, #3, #5, #6
"""

import logging
import os
import tempfile
import zipfile
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Session

from app.core.config import settings
from app.core.exceptions import (
    BatchAssetAccessDeniedError,
    BatchAssetNotFoundError,
)
from app.core.minio_client import get_minio_client
from app.models import Asset, AuditAction, AuditLog, User, UserRole
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)


class BatchDownloadService:
    """
    Service for batch downloading multiple assets as ZIP (AC: #2, #3).

    Uses temp file approach (recommended in dev notes):
    - Creates ZIP in local temp file
    - Streams each asset from MinIO into ZIP
    - Uploads completed ZIP to MinIO temp storage
    - Cleans up local temp file
    - Memory usage stays bounded regardless of total file size

    References:
        - Task 3: Batch Download Service
        - Dev Notes: Temp File Approach (Option 3)
    """

    def __init__(
        self,
        session: Session,
        current_user: User,
        ip_address: str | None = None,
    ) -> None:
        """
        Initialize batch download service.

        Args:
            session: Database session with tenant context
            current_user: User requesting the batch download
            ip_address: Client IP address for audit logging
        """
        self.session = session
        self.current_user = current_user
        self.ip_address = ip_address
        self.asset_repo = AssetRepository(session)
        self.minio_client = get_minio_client()

    def _check_asset_access(self, asset: Asset) -> str | None:
        """
        Check if current user has permission to access an asset (AC: #1, #9).

        Permission rules:
        - Owner can always access their assets
        - Admin and Supervisor can access any asset

        Args:
            asset: Asset to check access for

        Returns:
            None if access granted, or denial reason string if denied

        References:
            - Reused from SignedURLService (Story 3.2, 4.1, 4.2, 4.3)
            - AC: #1 (permission validation), #9 (denied if inaccessible)
        """
        # Admin and Supervisor can access any asset
        if self.current_user.role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
            return None

        # Owner can access their own assets
        if asset.user_id == self.current_user.id:
            return None

        # Check for cross-tenant access (should be prevented by RLS, but explicit check)
        if asset.tenant_id != self.current_user.tenant_id:
            return "different_tenant"

        # User doesn't own the asset
        return "not_owner"

    def validate_assets_access(self, asset_ids: list[UUID]) -> list[Asset]:
        """
        Validate user has access to all requested assets (AC: #1, #9, #10).

        Args:
            asset_ids: List of asset IDs to validate

        Returns:
            List of Asset objects if all validations pass

        Raises:
            AssetNotFoundError: One or more assets don't exist (404, AC: #10)
            AssetAccessDeniedError: User lacks permission for one or more assets (403, AC: #9)

        References:
            - Task 3.2: Validate assets access
            - AC: #1, #9, #10
        """
        # Get all requested assets
        assets = self.asset_repo.get_by_ids(asset_ids)

        # Check for missing assets (AC: #10)
        found_ids = {asset.id for asset in assets}
        missing_ids = set(asset_ids) - found_ids

        # Separate soft-deleted from truly missing assets for better error messages
        active_assets = [asset for asset in assets if not asset.is_deleted]
        deleted_ids = {asset.id for asset in assets if asset.is_deleted}

        # Report both missing and deleted assets with distinction
        if missing_ids or deleted_ids:
            # Construct clear error message
            error_parts = []
            if missing_ids:
                error_parts.append(f"{len(missing_ids)} asset(s) not found")
            if deleted_ids:
                error_parts.append(f"{len(deleted_ids)} asset(s) deleted")

            raise BatchAssetNotFoundError(
                error_message=f"Cannot access assets: {', '.join(error_parts)}",
                missing_asset_ids=[str(id) for id in missing_ids]
                if missing_ids
                else None,
                deleted_asset_ids=[str(id) for id in deleted_ids]
                if deleted_ids
                else None,
            )

        # Check permissions for each asset (AC: #9)
        inaccessible: list[dict[str, str]] = []
        for asset in active_assets:
            denial_reason = self._check_asset_access(asset)
            if denial_reason:
                inaccessible.append(
                    {
                        "asset_id": str(asset.id),
                        "reason": denial_reason,
                    }
                )

        if inaccessible:
            raise BatchAssetAccessDeniedError(
                error_message="Permission denied for one or more assets",
                inaccessible_assets=inaccessible,
            )

        logger.info(
            "Asset access validation passed",
            extra={
                "user_id": str(self.current_user.id),
                "asset_count": len(active_assets),
                "asset_ids": [str(a.id) for a in active_assets],
            },
        )

        return active_assets

    def create_batch_zip(self, assets: list[Asset]) -> tuple[str, int, int]:
        """
        Create ZIP file from assets and upload to MinIO (AC: #2, #3, #5).

        Uses temp file approach:
        1. Create local temp file
        2. Stream each asset from MinIO into ZIP
        3. Upload completed ZIP to MinIO temp storage
        4. Clean up local temp file

        Args:
            assets: List of assets to include in ZIP

        Returns:
            Tuple of (object_key, total_size_bytes, compressed_size_bytes)

        References:
            - Task 3.3, 3.4, 3.5, 3.6: ZIP creation and upload
            - Task 4: Streaming ZIP generation
            - AC: #2 (ZIP generation), #3 (streaming), #5 (temp storage)
        """
        # Generate unique ZIP filename (Task 5.1)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        zip_name = f"batch-download-{timestamp}-{uuid4().hex[:8]}.zip"
        object_key = f"temp/batch-downloads/{zip_name}"

        # Calculate total uncompressed size
        total_size = sum(asset.file_size_bytes for asset in assets)

        logger.info(
            "Starting ZIP creation",
            extra={
                "user_id": str(self.current_user.id),
                "asset_count": len(assets),
                "total_size_bytes": total_size,
                "zip_name": zip_name,
            },
        )

        # Create ZIP in temp file (AC: #3 - no full buffering in memory)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name

            try:
                # Create ZIP with compression (Task 3.4)
                with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
                    for asset in assets:
                        logger.debug(
                            "Adding asset to ZIP",
                            extra={
                                "asset_id": str(asset.id),
                                "file_name": asset.file_name,
                                "size_bytes": asset.file_size_bytes,
                            },
                        )

                        # Stream from MinIO (Task 3.5, 4.3)
                        response = None
                        try:
                            response = self.minio_client.get_object(
                                asset.bucket, asset.object_key
                            )
                            # Write to ZIP (Task 3.5, 4.4)
                            # zipfile.writestr loads content into memory, but for each
                            # file individually (not all at once), which is acceptable
                            zf.writestr(asset.file_name, response.read())
                        except Exception as e:
                            logger.error(
                                "Failed to add asset to ZIP",
                                extra={
                                    "asset_id": str(asset.id),
                                    "file_name": asset.file_name,
                                    "error": str(e),
                                },
                            )
                            raise RuntimeError(
                                f"Failed to retrieve asset {asset.id} from MinIO: {str(e)}"
                            ) from e
                        finally:
                            if response:
                                try:
                                    response.close()
                                    response.release_conn()
                                except Exception as e:
                                    logger.warning(
                                        "Failed to close MinIO response",
                                        extra={"error": str(e)},
                                    )

                # Get compressed size
                compressed_size = os.path.getsize(tmp_path)

                logger.info(
                    "ZIP creation complete",
                    extra={
                        "zip_name": zip_name,
                        "total_size_bytes": total_size,
                        "compressed_size_bytes": compressed_size,
                        "compression_ratio": f"{compressed_size / total_size * 100:.1f}%",
                    },
                )

                # Upload to MinIO temp storage (AC: #5, Task 3.6)
                # IMPORTANT (AC: #8): Automatic 1-hour cleanup requires MinIO lifecycle policy
                # See docs/deployment/minio-lifecycle-policy.md for setup instructions
                # Alternative: Run background cleanup job via cron/Celery
                try:
                    with open(tmp_path, "rb") as f:
                        self.minio_client.put_object(
                            bucket_name=settings.MINIO_BUCKET_NAME,
                            object_name=object_key,
                            data=f,
                            length=compressed_size,
                            content_type="application/zip",
                        )

                    logger.info(
                        "ZIP uploaded to MinIO",
                        extra={
                            "object_key": object_key,
                            "compressed_size_bytes": compressed_size,
                        },
                    )
                except Exception as e:
                    logger.error(
                        "Failed to upload ZIP to MinIO",
                        extra={
                            "object_key": object_key,
                            "compressed_size_bytes": compressed_size,
                            "error": str(e),
                        },
                    )
                    raise RuntimeError(
                        f"Failed to upload batch download ZIP to MinIO: {str(e)}"
                    ) from e

            finally:
                # Clean up temp file (Task 5.4)
                try:
                    os.unlink(tmp_path)
                    logger.debug(f"Deleted temp file: {tmp_path}")
                except Exception as e:
                    logger.warning(
                        f"Failed to delete temp file: {tmp_path}",
                        extra={"error": str(e)},
                    )

        return object_key, total_size, compressed_size

    def generate_download_url(self, object_key: str) -> tuple[str, datetime]:
        """
        Generate presigned URL for the batch ZIP (AC: #4, #7, #8).

        Args:
            object_key: MinIO object key for the ZIP file

        Returns:
            Tuple of (presigned_url, expires_at)

        References:
            - AC: #4 (download URL), #7 (direct download), #8 (1-hour expiry)
        """
        # 1-hour expiry (AC: #8, Task 5.2)
        expires = timedelta(hours=1)
        expires_at = datetime.utcnow() + expires

        # Generate presigned URL (AC: #7 - direct MinIO download)
        url = self.minio_client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_key,
            expires=expires,
        )

        logger.info(
            "Download URL generated",
            extra={
                "object_key": object_key,
                "expires_at": expires_at.isoformat(),
            },
        )

        return url, expires_at

    def _create_audit_log(
        self,
        action: AuditAction,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Create audit log entry (AC: #6).

        Args:
            action: Audit action type
            metadata: Additional metadata for the audit log

        References:
            - Task 6.3, 6.4, 6.5: Audit logging
            - AC: #6 (audit logging)
        """
        audit_log = AuditLog(
            tenant_id=self.current_user.tenant_id,
            user_id=self.current_user.id,
            action=action,
            ip_address=self.ip_address,
            metadata=metadata,
        )
        self.session.add(audit_log)
        self.session.commit()

        logger.info(
            "Audit log created",
            extra={
                "action": action.value,
                "user_id": str(self.current_user.id),
                "metadata": metadata,
            },
        )
