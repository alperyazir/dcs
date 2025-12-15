import uuid
from datetime import datetime
from enum import Enum

from pydantic import EmailStr
from sqlalchemy import JSON, CheckConstraint, Column, Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

# =============================================================================
# ENUMS
# =============================================================================


class UserRole(str, Enum):
    """User roles for role-based access control (RBAC)."""

    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    PUBLISHER = "publisher"
    SCHOOL = "school"
    TEACHER = "teacher"
    STUDENT = "student"


class TenantType(str, Enum):
    """Types of tenants in the multi-tenant system."""

    PUBLISHER = "publisher"
    SCHOOL = "school"
    TEACHER = "teacher"
    STUDENT = "student"


class AuditAction(str, Enum):
    """Actions tracked in audit logs."""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    RESTORE = "restore"
    UPDATE = "update"
    LOGIN = "login"
    LOGOUT = "logout"


# =============================================================================
# TENANT MODEL
# =============================================================================


class TenantBase(SQLModel):
    """Shared properties for Tenant."""

    name: str = Field(max_length=255, unique=True, index=True)
    tenant_type: TenantType


class TenantCreate(TenantBase):
    """Properties to receive via API on tenant creation."""

    pass


class Tenant(TenantBase, table=True):
    """Database model for tenants (multi-tenant isolation)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    users: list["User"] = Relationship(back_populates="tenant")
    assets: list["Asset"] = Relationship(back_populates="tenant")


class TenantPublic(TenantBase):
    """Properties to return via API."""

    id: uuid.UUID
    created_at: datetime


# =============================================================================
# USER MODEL
# =============================================================================


class UserBase(SQLModel):
    """Shared properties for User."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.STUDENT)


class UserCreate(UserBase):
    """Properties to receive via API on user creation."""

    password: str = Field(min_length=8, max_length=128)
    tenant_id: uuid.UUID | None = None


class UserRegister(SQLModel):
    """Properties for user self-registration."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    """Properties to receive via API on user update, all optional."""

    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None  # type: ignore
    tenant_id: uuid.UUID | None = None


class UserUpdateMe(SQLModel):
    """Properties for user to update their own profile."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    """Properties for password update."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    """Database model for users."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    tenant_id: uuid.UUID | None = Field(
        default=None, foreign_key="tenant.id", nullable=True, index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Tenant | None = Relationship(back_populates="users")
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    assets: list["Asset"] = Relationship(back_populates="owner")


class UserPublic(UserBase):
    """Properties to return via API."""

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class UsersPublic(SQLModel):
    """Paginated list of users."""

    data: list[UserPublic]
    count: int


# =============================================================================
# ASSET MODEL
# =============================================================================


class AssetBase(SQLModel):
    """Shared properties for Asset."""

    bucket: str = Field(max_length=255)
    object_key: str = Field(max_length=1024)
    file_name: str = Field(max_length=255)
    file_size_bytes: int = Field(ge=0)
    mime_type: str = Field(max_length=255)
    checksum: str | None = Field(default=None, max_length=64)


class AssetCreate(AssetBase):
    """Properties to receive via API on asset creation."""

    tenant_id: uuid.UUID


class AssetUpdate(SQLModel):
    """Properties to receive via API on asset update."""

    file_name: str | None = Field(default=None, max_length=255)
    checksum: str | None = Field(default=None, max_length=64)


class Asset(AssetBase, table=True):
    """Database model for assets (files stored in MinIO)."""

    __table_args__ = (
        Index("idx_assets_tenant_id", "tenant_id"),
        Index("idx_assets_user_id", "user_id"),
        Index("idx_assets_created_at", "created_at"),
        Index("idx_assets_tenant_is_deleted", "tenant_id", "is_deleted"),
        UniqueConstraint("bucket", "object_key", name="uq_asset_bucket_object_key"),
        CheckConstraint("file_size_bytes >= 0", name="ck_assets_file_size_positive"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    tenant_id: uuid.UUID = Field(foreign_key="tenant.id", nullable=False, index=True)
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    owner: User | None = Relationship(back_populates="assets")
    tenant: Tenant | None = Relationship(back_populates="assets")


class AssetPublic(AssetBase):
    """Properties to return via API."""

    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssetsPublic(SQLModel):
    """Paginated list of assets."""

    data: list[AssetPublic]
    count: int


# =============================================================================
# AUDIT LOG MODEL
# =============================================================================


class AuditLogBase(SQLModel):
    """Shared properties for AuditLog."""

    action: AuditAction
    ip_address: str = Field(max_length=45)  # IPv6 max length
    metadata_json: dict | None = Field(default=None, sa_column=Column(JSON))


class AuditLogCreate(AuditLogBase):
    """Properties to receive on audit log creation."""

    user_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None


class AuditLog(AuditLogBase, table=True):
    """Database model for audit logs (immutable, append-only)."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_log_user_id", "user_id"),
        Index("idx_audit_log_timestamp", "timestamp"),
        Index("idx_audit_log_asset_id", "asset_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID | None = Field(
        default=None, index=True
    )  # Nullable for system actions
    asset_id: uuid.UUID | None = Field(
        default=None, index=True
    )  # Nullable for non-asset actions
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)


class AuditLogPublic(AuditLogBase):
    """Properties to return via API."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    asset_id: uuid.UUID | None
    timestamp: datetime


class AuditLogsPublic(SQLModel):
    """Paginated list of audit logs."""

    data: list[AuditLogPublic]
    count: int


# =============================================================================
# ITEM MODEL (Legacy from template - kept for backward compatibility)
# =============================================================================


class ItemBase(SQLModel):
    """Shared properties for Item."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    """Properties to receive on item creation."""

    pass


class ItemUpdate(ItemBase):
    """Properties to receive on item update."""

    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    """Database model for items (legacy template model)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(ItemBase):
    """Properties to return via API."""

    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    """Paginated list of items."""

    data: list[ItemPublic]
    count: int


# =============================================================================
# GENERIC SCHEMAS
# =============================================================================


class Message(SQLModel):
    """Generic message response."""

    message: str


class Token(SQLModel):
    """JSON payload containing access token."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    """Contents of JWT token."""

    sub: str | None = None


class NewPassword(SQLModel):
    """Properties for password reset."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)
