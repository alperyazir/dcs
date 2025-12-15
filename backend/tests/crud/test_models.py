"""Tests for multi-tenant models: Tenant, Asset, AuditLog."""
import uuid

from sqlmodel import Session

from app import crud
from app.models import (
    AssetCreate,
    AuditAction,
    AuditLogCreate,
    TenantCreate,
    TenantType,
    UserCreate,
    UserRole,
)


def test_create_tenant(db: Session) -> None:
    """Test tenant creation."""
    tenant_in = TenantCreate(name="Test Publisher", tenant_type=TenantType.PUBLISHER)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    assert tenant.name == "Test Publisher"
    assert tenant.tenant_type == TenantType.PUBLISHER
    assert tenant.id is not None
    assert tenant.created_at is not None


def test_get_tenant_by_id(db: Session) -> None:
    """Test retrieving tenant by ID."""
    tenant_in = TenantCreate(name="Test School", tenant_type=TenantType.SCHOOL)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    retrieved = crud.get_tenant_by_id(session=db, tenant_id=tenant.id)
    assert retrieved is not None
    assert retrieved.id == tenant.id
    assert retrieved.name == "Test School"


def test_get_tenant_by_name(db: Session) -> None:
    """Test retrieving tenant by name."""
    tenant_in = TenantCreate(name="Unique School Name", tenant_type=TenantType.SCHOOL)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    retrieved = crud.get_tenant_by_name(session=db, name="Unique School Name")
    assert retrieved is not None
    assert retrieved.id == tenant.id


def test_user_with_role_and_tenant(db: Session) -> None:
    """Test user creation with role and tenant_id."""
    # Create tenant first
    tenant_in = TenantCreate(
        name="Test Tenant for User", tenant_type=TenantType.PUBLISHER
    )
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    # Create user with role and tenant
    user_in = UserCreate(
        email=f"teacher_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        role=UserRole.TEACHER,
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    assert user.role == UserRole.TEACHER
    assert user.tenant_id == tenant.id
    assert user.created_at is not None
    assert user.updated_at is not None


def test_create_asset(db: Session) -> None:
    """Test asset creation."""
    # Create tenant and user first
    tenant_in = TenantCreate(name="Asset Test Tenant", tenant_type=TenantType.SCHOOL)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    user_in = UserCreate(
        email=f"assetuser_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Create asset
    asset_in = AssetCreate(
        bucket="assets",
        object_key=f"test/{uuid.uuid4().hex}/document.pdf",
        file_name="document.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        tenant_id=tenant.id,
    )
    asset = crud.create_asset(session=db, asset_in=asset_in, user_id=user.id)

    assert asset.id is not None
    assert asset.user_id == user.id
    assert asset.tenant_id == tenant.id
    assert asset.bucket == "assets"
    assert asset.file_name == "document.pdf"
    assert asset.file_size_bytes == 1024
    assert asset.is_deleted is False
    assert asset.deleted_at is None


def test_soft_delete_and_restore_asset(db: Session) -> None:
    """Test soft delete and restore functionality for assets."""
    # Create tenant and user
    tenant_in = TenantCreate(name="Delete Test Tenant", tenant_type=TenantType.SCHOOL)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    user_in = UserCreate(
        email=f"deleteuser_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Create asset
    asset_in = AssetCreate(
        bucket="assets",
        object_key=f"test/{uuid.uuid4().hex}/to_delete.txt",
        file_name="to_delete.txt",
        file_size_bytes=512,
        mime_type="text/plain",
        tenant_id=tenant.id,
    )
    asset = crud.create_asset(session=db, asset_in=asset_in, user_id=user.id)

    # Soft delete
    deleted_asset = crud.soft_delete_asset(session=db, db_asset=asset)
    assert deleted_asset.is_deleted is True
    assert deleted_asset.deleted_at is not None

    # Restore
    restored_asset = crud.restore_asset(session=db, db_asset=deleted_asset)
    assert restored_asset.is_deleted is False
    assert restored_asset.deleted_at is None


def test_create_audit_log(db: Session) -> None:
    """Test audit log creation."""
    # Create tenant and user for the audit log
    tenant_in = TenantCreate(name="Audit Test Tenant", tenant_type=TenantType.PUBLISHER)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    user_in = UserCreate(
        email=f"audituser_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Create audit log
    audit_in = AuditLogCreate(
        action=AuditAction.LOGIN,
        ip_address="192.168.1.1",
        user_id=user.id,
        metadata_json={"browser": "Chrome", "platform": "Windows"},
    )
    audit_log = crud.create_audit_log(session=db, audit_log_in=audit_in)

    assert audit_log.id is not None
    assert audit_log.action == AuditAction.LOGIN
    assert audit_log.user_id == user.id
    assert audit_log.ip_address == "192.168.1.1"
    assert audit_log.metadata_json == {"browser": "Chrome", "platform": "Windows"}
    assert audit_log.timestamp is not None


def test_audit_log_for_asset_action(db: Session) -> None:
    """Test audit log for asset-related actions."""
    # Create tenant, user, and asset
    tenant_in = TenantCreate(name="Asset Audit Tenant", tenant_type=TenantType.SCHOOL)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    user_in = UserCreate(
        email=f"assetaudituser_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    asset_in = AssetCreate(
        bucket="assets",
        object_key=f"test/{uuid.uuid4().hex}/audited.pdf",
        file_name="audited.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        tenant_id=tenant.id,
    )
    asset = crud.create_asset(session=db, asset_in=asset_in, user_id=user.id)

    # Create upload audit log
    audit_in = AuditLogCreate(
        action=AuditAction.UPLOAD,
        ip_address="10.0.0.1",
        user_id=user.id,
        asset_id=asset.id,
        metadata_json={"file_size": 2048, "mime_type": "application/pdf"},
    )
    audit_log = crud.create_audit_log(session=db, audit_log_in=audit_in)

    assert audit_log.action == AuditAction.UPLOAD
    assert audit_log.asset_id == asset.id


def test_get_audit_logs_by_user(db: Session) -> None:
    """Test retrieving audit logs by user ID."""
    # Create tenant and user
    tenant_in = TenantCreate(name="Logs By User Tenant", tenant_type=TenantType.TEACHER)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    user_in = UserCreate(
        email=f"logsuser_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Create multiple audit logs
    for action in [AuditAction.LOGIN, AuditAction.UPLOAD, AuditAction.DOWNLOAD]:
        audit_in = AuditLogCreate(
            action=action,
            ip_address="192.168.1.100",
            user_id=user.id,
        )
        crud.create_audit_log(session=db, audit_log_in=audit_in)

    # Retrieve logs
    logs = crud.get_audit_logs_by_user(session=db, user_id=user.id)
    assert len(logs) >= 3


def test_audit_log_system_action(db: Session) -> None:
    """Test audit log for system actions (no user_id)."""
    audit_in = AuditLogCreate(
        action=AuditAction.DELETE,
        ip_address="0.0.0.0",
        user_id=None,  # System action
        metadata_json={"reason": "scheduled_cleanup", "files_deleted": 42},
    )
    audit_log = crud.create_audit_log(session=db, audit_log_in=audit_in)

    assert audit_log.user_id is None
    assert audit_log.action == AuditAction.DELETE
    assert audit_log.metadata_json["reason"] == "scheduled_cleanup"


def test_get_asset_by_id(db: Session) -> None:
    """Test retrieving asset by ID with optional tenant filtering."""
    # Create tenant and user
    tenant_in = TenantCreate(
        name="Get Asset Test Tenant", tenant_type=TenantType.PUBLISHER
    )
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    user_in = UserCreate(
        email=f"getassetuser_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Create asset
    asset_in = AssetCreate(
        bucket="test-bucket",
        object_key=f"test/{uuid.uuid4().hex}/gettest.pdf",
        file_name="gettest.pdf",
        file_size_bytes=100,
        mime_type="application/pdf",
        tenant_id=tenant.id,
    )
    asset = crud.create_asset(session=db, asset_in=asset_in, user_id=user.id)

    # Test get by ID without tenant filter
    retrieved = crud.get_asset_by_id(session=db, asset_id=asset.id)
    assert retrieved is not None
    assert retrieved.id == asset.id

    # Test get by ID with correct tenant filter
    retrieved_with_tenant = crud.get_asset_by_id(
        session=db, asset_id=asset.id, tenant_id=tenant.id
    )
    assert retrieved_with_tenant is not None
    assert retrieved_with_tenant.id == asset.id

    # Test get by ID with wrong tenant filter
    wrong_tenant_id = uuid.uuid4()
    not_found = crud.get_asset_by_id(
        session=db, asset_id=asset.id, tenant_id=wrong_tenant_id
    )
    assert not_found is None


def test_get_audit_logs_by_asset(db: Session) -> None:
    """Test retrieving audit logs by asset ID."""
    # Create tenant, user, and asset
    tenant_in = TenantCreate(name="Logs By Asset Tenant", tenant_type=TenantType.SCHOOL)
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)

    user_in = UserCreate(
        email=f"logsassetuser_{uuid.uuid4().hex[:8]}@example.com",
        password="testpassword123",
        tenant_id=tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)

    asset_in = AssetCreate(
        bucket="logs-bucket",
        object_key=f"test/{uuid.uuid4().hex}/logged.pdf",
        file_name="logged.pdf",
        file_size_bytes=500,
        mime_type="application/pdf",
        tenant_id=tenant.id,
    )
    asset = crud.create_asset(session=db, asset_in=asset_in, user_id=user.id)

    # Create multiple audit logs for this asset
    for action in [AuditAction.UPLOAD, AuditAction.DOWNLOAD, AuditAction.UPDATE]:
        audit_in = AuditLogCreate(
            action=action,
            ip_address="10.0.0.50",
            user_id=user.id,
            asset_id=asset.id,
        )
        crud.create_audit_log(session=db, audit_log_in=audit_in)

    # Retrieve logs by asset
    logs = crud.get_audit_logs_by_asset(session=db, asset_id=asset.id)
    assert len(logs) >= 3
    assert all(log.asset_id == asset.id for log in logs)
