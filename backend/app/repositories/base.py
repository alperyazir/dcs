"""
Base Repository with Automatic Tenant Filtering (Story 2.3, Task 2).

Provides TenantAwareRepository base class that:
- Automatically filters queries by tenant_id
- Supports Admin/Supervisor bypass
- Uses __tenant_aware__ marker on models

References:
- AC: #2 (all queries automatically include tenant_id filters)
- AC: #3 (Asset queries filter by tenant_id)
- AC: #4 (Admin/Supervisor bypass tenant filtering)
- AC: #6 (cross-tenant query returns zero results)
- AC: #10 (consistent filtering across all repository methods)
"""

import logging
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlmodel import Session, select

from app.core.exceptions import PermissionDeniedException
from app.core.tenant_context import get_tenant_context
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

# Type variable for generic repository
T = TypeVar("T")


class TenantAwareRepository(Generic[T]):
    """
    Base repository with automatic tenant filtering.

    All query methods automatically apply tenant_id filters based on:
    1. Current request's TenantContext (from contextvars)
    2. Model's __tenant_aware__ attribute

    Admin/Supervisor users bypass filtering when bypass_filter=True.

    Usage:
        class AssetRepository(TenantAwareRepository[Asset]):
            def __init__(self, session: Session):
                super().__init__(session, Asset)

            async def get_by_bucket(self, bucket: str) -> List[Asset]:
                statement = select(Asset).where(Asset.bucket == bucket)
                statement = self._apply_tenant_filter(statement)
                return self.session.exec(statement).all()

    Attributes:
        session: SQLModel database session
        model: The model class this repository operates on
    """

    def __init__(self, session: Session, model: type[T]):
        """
        Initialize repository.

        Args:
            session: SQLModel database session
            model: Model class (must have __tenant_aware__ = True for filtering)
        """
        self.session = session
        self.model = model

    def _is_tenant_aware(self) -> bool:
        """
        Check if the model supports tenant filtering.

        Returns:
            True if model has __tenant_aware__ = True, False otherwise.
        """
        return getattr(self.model, "__tenant_aware__", False) is True

    def _apply_tenant_filter(self, statement: Any) -> Any:
        """
        Apply tenant filter to query statement if applicable.

        Filtering is applied when ALL of these conditions are met:
        1. Model has __tenant_aware__ = True
        2. TenantContext has a tenant_id
        3. TenantContext.bypass_filter is False

        Args:
            statement: SQLModel select statement

        Returns:
            Statement with tenant_id filter applied (or unchanged if not applicable)
        """
        # Check if model is tenant-aware
        if not self._is_tenant_aware():
            return statement

        # Get current tenant context
        ctx = get_tenant_context()

        # Bypass for Admin/Supervisor (AC: #4)
        if ctx.bypass_filter:
            logger.debug(
                "Tenant filter bypassed",
                extra={
                    "user_id": str(ctx.user_id) if ctx.user_id else None,
                    "model": self.model.__name__,
                },
            )
            return statement

        # No tenant_id - return unfiltered (unauthenticated or system operation)
        if ctx.tenant_id is None:
            return statement

        # Apply tenant filter (AC: #2, #3, #6)
        logger.debug(
            "Applying tenant filter",
            extra={
                "tenant_id": str(ctx.tenant_id),
                "model": self.model.__name__,
            },
        )
        return statement.where(self.model.tenant_id == ctx.tenant_id)  # type: ignore[attr-defined]

    def _validate_tenant_ownership(
        self, resource_tenant_id: UUID, resource_id: UUID | None = None
    ) -> None:
        """
        Validate that the current user can write to the specified tenant (AC: #5).

        Cross-tenant writes are blocked unless:
        - User has bypass_filter=True (Admin/Supervisor)
        - Resource tenant_id matches user's tenant_id

        Args:
            resource_tenant_id: The tenant_id of the resource being written
            resource_id: Optional resource UUID for audit logging

        Raises:
            PermissionDeniedException: If user attempts cross-tenant write
        """
        ctx = get_tenant_context()

        # Admin/Supervisor bypass (AC: #4)
        if ctx.bypass_filter:
            logger.debug(
                "Cross-tenant write allowed (admin bypass)",
                extra={
                    "user_id": str(ctx.user_id) if ctx.user_id else None,
                    "resource_tenant_id": str(resource_tenant_id),
                },
            )
            return

        # No tenant context - allow (system operation)
        if ctx.tenant_id is None:
            return

        # Check tenant ownership
        if ctx.tenant_id != resource_tenant_id:
            # Log the cross-tenant write attempt (AC: #8)
            if ctx.user_id:
                AuditService.log_authorization_denial(
                    user_id=ctx.user_id,
                    action="write",
                    resource_type=self.model.__name__,
                    resource_id=resource_id,
                    reason=f"Cross-tenant write denied: user tenant {ctx.tenant_id} != resource tenant {resource_tenant_id}",
                )

            logger.warning(
                "Cross-tenant write blocked",
                extra={
                    "user_id": str(ctx.user_id) if ctx.user_id else None,
                    "user_tenant_id": str(ctx.tenant_id),
                    "resource_tenant_id": str(resource_tenant_id),
                    "model": self.model.__name__,
                },
            )

            raise PermissionDeniedException(
                user_id=ctx.user_id or UUID(int=0),
                resource_type=self.model.__name__,
                resource_id=resource_id,
                action="write",
                reason="Cross-tenant write not allowed",
            )

    def get_by_id(self, id: UUID) -> T | None:
        """
        Get entity by ID with tenant filtering.

        Args:
            id: Entity UUID

        Returns:
            Entity if found and user has access, None otherwise.
        """
        statement = select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        statement = self._apply_tenant_filter(statement)
        return self.session.exec(statement).first()

    def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        """
        List entities with pagination and tenant filtering.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum records to return

        Returns:
            List of entities visible to current user.
        """
        statement = select(self.model).offset(skip).limit(limit)
        statement = self._apply_tenant_filter(statement)
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        """
        Count entities visible to current user.

        Returns:
            Total count of accessible entities.
        """
        from sqlalchemy import func

        statement = select(func.count()).select_from(self.model)
        statement = self._apply_tenant_filter(statement)
        return self.session.exec(statement).one()
