import uuid
from typing import Any

from sqlmodel import Session, col, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Asset,
    AssetCreate,
    AssetUpdate,
    AuditLog,
    AuditLogCreate,
    Item,
    ItemCreate,
    Tenant,
    TenantCreate,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    from datetime import datetime

    user_data = user_in.model_dump(exclude_unset=True)
    extra_data: dict[str, Any] = {"updated_at": datetime.utcnow()}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# =============================================================================
# TENANT CRUD
# =============================================================================


def create_tenant(*, session: Session, tenant_in: TenantCreate) -> Tenant:
    """Create a new tenant."""
    db_tenant = Tenant.model_validate(tenant_in)
    session.add(db_tenant)
    session.commit()
    session.refresh(db_tenant)
    return db_tenant


def get_tenant_by_id(*, session: Session, tenant_id: uuid.UUID) -> Tenant | None:
    """Get tenant by ID."""
    return session.get(Tenant, tenant_id)


def get_tenant_by_name(*, session: Session, name: str) -> Tenant | None:
    """Get tenant by name."""
    statement = select(Tenant).where(Tenant.name == name)
    return session.exec(statement).first()


# =============================================================================
# ASSET CRUD
# =============================================================================


def create_asset(
    *, session: Session, asset_in: AssetCreate, user_id: uuid.UUID
) -> Asset:
    """Create a new asset record."""
    db_asset = Asset.model_validate(asset_in, update={"user_id": user_id})
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    return db_asset


def get_asset_by_id(
    *, session: Session, asset_id: uuid.UUID, tenant_id: uuid.UUID | None = None
) -> Asset | None:
    """Get asset by ID, optionally filtered by tenant."""
    statement = select(Asset).where(Asset.id == asset_id)
    if tenant_id is not None:
        statement = statement.where(Asset.tenant_id == tenant_id)
    return session.exec(statement).first()


def update_asset(*, session: Session, db_asset: Asset, asset_in: AssetUpdate) -> Asset:
    """Update an existing asset."""
    from datetime import datetime

    asset_data = asset_in.model_dump(exclude_unset=True)
    db_asset.sqlmodel_update(asset_data, update={"updated_at": datetime.utcnow()})
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    return db_asset


def soft_delete_asset(*, session: Session, db_asset: Asset) -> Asset:
    """Soft delete an asset (set is_deleted=True)."""
    from datetime import datetime

    db_asset.is_deleted = True
    db_asset.deleted_at = datetime.utcnow()
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    return db_asset


def restore_asset(*, session: Session, db_asset: Asset) -> Asset:
    """Restore a soft-deleted asset."""
    db_asset.is_deleted = False
    db_asset.deleted_at = None
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    return db_asset


# =============================================================================
# AUDIT LOG CRUD (Append-only)
# =============================================================================


def create_audit_log(*, session: Session, audit_log_in: AuditLogCreate) -> AuditLog:
    """
    Create an audit log entry.

    NOTE: Audit logs are append-only. There are no update or delete functions
    by design to ensure audit trail integrity.
    """
    db_audit_log = AuditLog.model_validate(audit_log_in)
    session.add(db_audit_log)
    session.commit()
    session.refresh(db_audit_log)
    return db_audit_log


def get_audit_logs_by_user(
    *, session: Session, user_id: uuid.UUID, limit: int = 100, offset: int = 0
) -> list[AuditLog]:
    """Get audit logs for a specific user."""
    statement = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(col(AuditLog.timestamp).desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_audit_logs_by_asset(
    *, session: Session, asset_id: uuid.UUID, limit: int = 100, offset: int = 0
) -> list[AuditLog]:
    """Get audit logs for a specific asset."""
    statement = (
        select(AuditLog)
        .where(AuditLog.asset_id == asset_id)
        .order_by(col(AuditLog.timestamp).desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(statement).all())
