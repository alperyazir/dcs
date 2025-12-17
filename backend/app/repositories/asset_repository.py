"""
Asset Repository with Tenant-Aware Queries (Story 2.3, Task 4).

Provides:
- Asset-specific CRUD operations
- Automatic tenant filtering via TenantAwareRepository
- Soft delete functionality
- Pagination support

References:
- AC: #2 (all queries automatically include tenant_id filters)
- AC: #3 (Asset queries filter by tenant_id)
- AC: #6 (cross-tenant query returns zero results)
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models import Asset, AssetCreate, AssetUpdate
from app.repositories.base import TenantAwareRepository

logger = logging.getLogger(__name__)


class AssetRepository(TenantAwareRepository[Asset]):
    """
    Repository for Asset model with tenant isolation.

    All queries automatically apply tenant_id filter based on
    the current request's TenantContext (set by TenantContextMiddleware).

    Admin/Supervisor users bypass filtering to access all tenants.

    Usage:
        repo = AssetRepository(session=db_session)
        assets = repo.list_by_user(user_id=current_user.id)
        asset = repo.get_by_id(asset_id)
    """

    def __init__(self, session: Session):
        """
        Initialize AssetRepository.

        Args:
            session: SQLModel database session
        """
        super().__init__(session, Asset)

    def get_by_id(self, asset_id: UUID) -> Asset | None:
        """
        Get asset by ID with tenant filtering.

        Args:
            asset_id: Asset UUID

        Returns:
            Asset if found and user has access, None otherwise.
            Cross-tenant access returns None (AC: #6).
        """
        statement = select(Asset).where(Asset.id == asset_id)
        statement = self._apply_tenant_filter(statement)
        return self.session.exec(statement).first()

    def get_by_ids(self, asset_ids: list[UUID]) -> list[Asset]:
        """
        Get multiple assets by IDs with tenant filtering (Story 4.4).

        Args:
            asset_ids: List of asset UUIDs

        Returns:
            List of assets found (may be fewer than requested if some don't exist
            or are in other tenants). Returns empty list if none found.

        References:
            - Task 3.2: Batch access validation
            - Story 4.4: Batch Download
        """
        if not asset_ids:
            return []

        statement = select(Asset).where(Asset.id.in_(asset_ids))  # type: ignore[attr-defined]
        statement = self._apply_tenant_filter(statement)
        return list(self.session.exec(statement).all())

    def list_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50,
        include_deleted: bool = False,
    ) -> list[Asset]:
        """
        List assets for a user with pagination.

        Args:
            user_id: Owner user UUID
            page: Page number (1-indexed)
            page_size: Number of items per page (max 100)
            include_deleted: Include soft-deleted assets

        Returns:
            List of assets visible to current user.
        """
        # Enforce max page size
        page_size = min(page_size, 100)
        offset = (page - 1) * page_size

        statement = select(Asset).where(Asset.user_id == user_id)

        # Exclude soft-deleted by default
        if not include_deleted:
            statement = statement.where(Asset.is_deleted == False)  # noqa: E712

        statement = self._apply_tenant_filter(statement)
        statement = statement.offset(offset).limit(page_size)
        statement = statement.order_by(Asset.created_at.desc())  # type: ignore[attr-defined]

        return list(self.session.exec(statement).all())

    def list_by_tenant(
        self,
        page: int = 1,
        page_size: int = 50,
        include_deleted: bool = False,
    ) -> list[Asset]:
        """
        List all assets in current tenant with pagination.

        Uses tenant_id from context, not an explicit parameter.
        This ensures tenant isolation is always enforced.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page (max 100)
            include_deleted: Include soft-deleted assets

        Returns:
            List of assets in current tenant.
        """
        page_size = min(page_size, 100)
        offset = (page - 1) * page_size

        statement = select(Asset)

        if not include_deleted:
            statement = statement.where(Asset.is_deleted == False)  # noqa: E712

        statement = self._apply_tenant_filter(statement)
        statement = statement.offset(offset).limit(page_size)
        statement = statement.order_by(Asset.created_at.desc())  # type: ignore[attr-defined]

        return list(self.session.exec(statement).all())

    def create(
        self,
        data: AssetCreate,
        user_id: UUID,
    ) -> Asset:
        """
        Create a new asset.

        The tenant_id is taken from the AssetCreate data and validated
        against the current user's tenant (AC: #5 - cross-tenant write prevention).

        Args:
            data: Asset creation data
            user_id: Owner user UUID

        Returns:
            Created Asset instance.

        Raises:
            PermissionDeniedException: If user attempts cross-tenant write.
        """
        # Validate tenant ownership before write (AC: #5, Task 8)
        self._validate_tenant_ownership(data.tenant_id)

        asset = Asset(
            **data.model_dump(),
            user_id=user_id,
        )
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)

        logger.info(
            "Asset created",
            extra={
                "asset_id": str(asset.id),
                "user_id": str(user_id),
                "tenant_id": str(asset.tenant_id),
                "file_name": asset.file_name,
            },
        )

        return asset

    def update(self, asset_id: UUID, data: AssetUpdate) -> Asset | None:
        """
        Update an asset.

        Args:
            asset_id: Asset UUID
            data: Update data (partial)

        Returns:
            Updated Asset if found and user has access, None otherwise.
        """
        asset = self.get_by_id(asset_id)
        if not asset:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset, field, value)

        asset.updated_at = datetime.now(UTC)
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)

        logger.info(
            "Asset updated",
            extra={
                "asset_id": str(asset_id),
                "updated_fields": list(update_data.keys()),
            },
        )

        return asset

    def soft_delete(self, asset_id: UUID) -> Asset | None:
        """
        Soft delete an asset (set is_deleted=True).

        Args:
            asset_id: Asset UUID

        Returns:
            Soft-deleted Asset if found and user has access, None otherwise.
        """
        asset = self.get_by_id(asset_id)
        if not asset:
            return None

        asset.is_deleted = True
        asset.deleted_at = datetime.now(UTC)
        asset.updated_at = datetime.now(UTC)

        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)

        logger.info(
            "Asset soft deleted",
            extra={
                "asset_id": str(asset_id),
                "tenant_id": str(asset.tenant_id),
            },
        )

        return asset

    def restore(self, asset_id: UUID) -> Asset | None:
        """
        Restore a soft-deleted asset.

        Args:
            asset_id: Asset UUID

        Returns:
            Restored Asset if found and user has access, None otherwise.
        """
        # Need to include deleted assets to find it
        statement = select(Asset).where(
            Asset.id == asset_id,
            Asset.is_deleted == True,  # noqa: E712
        )
        statement = self._apply_tenant_filter(statement)
        asset = self.session.exec(statement).first()

        if not asset:
            return None

        asset.is_deleted = False
        asset.deleted_at = None
        asset.updated_at = datetime.now(UTC)

        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)

        logger.info(
            "Asset restored",
            extra={
                "asset_id": str(asset_id),
                "tenant_id": str(asset.tenant_id),
            },
        )

        return asset

    def count_by_user(self, user_id: UUID, include_deleted: bool = False) -> int:
        """
        Count assets for a user.

        Args:
            user_id: Owner user UUID
            include_deleted: Include soft-deleted assets

        Returns:
            Count of assets visible to current user.
        """
        from sqlalchemy import func

        statement = (
            select(func.count()).select_from(Asset).where(Asset.user_id == user_id)
        )

        if not include_deleted:
            statement = statement.where(Asset.is_deleted == False)  # noqa: E712

        statement = self._apply_tenant_filter(statement)
        return self.session.exec(statement).one()

    def get_by_object_key(
        self,
        bucket: str,
        object_key: str,
    ) -> Asset | None:
        """
        Get asset by MinIO object key (Story 3.1, Task 5.4).

        Used for download API to lookup asset by MinIO path.

        Args:
            bucket: MinIO bucket name
            object_key: Full object key (path in bucket)

        Returns:
            Asset if found and user has access, None otherwise.
        """
        statement = select(Asset).where(
            Asset.bucket == bucket,
            Asset.object_key == object_key,
            Asset.is_deleted == False,  # noqa: E712
        )
        statement = self._apply_tenant_filter(statement)
        return self.session.exec(statement).first()
