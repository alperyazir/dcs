import uuid
from typing import Any

from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# =============================================================================
# ROW-LEVEL SECURITY (RLS) STRATEGY
# =============================================================================
#
# Multi-tenant isolation is implemented using tenant_id columns on all tenant-
# scoped tables (users, assets). The isolation strategy works as follows:
#
# 1. APPLICATION LAYER (Primary Enforcement):
#    - All queries MUST include tenant_id filtering via get_tenant_filter()
#    - Middleware extracts tenant_id from authenticated user's JWT token
#    - Services/repositories inject tenant_id into all queries
#
# 2. DATABASE LAYER (Defense in Depth - Future Implementation):
#    - PostgreSQL Row-Level Security policies will be enabled as backstop
#    - RLS policies will use session variables set via SET LOCAL
#    - Example policy for assets table:
#      CREATE POLICY tenant_isolation ON asset
#      FOR ALL USING (tenant_id = current_setting('app.current_tenant')::uuid);
#
# 3. IMPLEMENTATION NOTES:
#    - Superusers (tenant_id IS NULL) can access all tenants for admin functions
#    - System actions (audit logs, etc.) may have NULL tenant_id
#    - Always use get_tenant_filter() helper for consistent filtering
#
# TODO: Enable PostgreSQL RLS policies in production deployment
# TODO: Add middleware to inject tenant context from JWT claims
# =============================================================================


def get_tenant_filter(tenant_id: uuid.UUID | None) -> dict[str, Any]:
    """
    Get tenant filter for database queries.

    This helper function returns a dictionary suitable for use in SQLModel
    query filtering to enforce multi-tenant isolation.

    Usage:
        # In a repository/service function:
        tenant_filter = get_tenant_filter(current_user.tenant_id)
        query = select(Asset).where(Asset.tenant_id == tenant_filter["tenant_id"])

    Args:
        tenant_id: The tenant UUID to filter by, or None for superuser/system access.

    Returns:
        Dictionary with tenant_id key. If tenant_id is None (superuser),
        the filter should be handled specially to allow cross-tenant access.
    """
    return {"tenant_id": tenant_id}


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
