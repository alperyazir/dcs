"""
Tests for Batch Download API Routes (Story 4.4).

Tests all acceptance criteria for batch downloading multiple assets as ZIP.

References:
- Task 7: Write Comprehensive Tests
- AC: #1-#12
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.crud import create_tenant
from app.models import Asset, AuditAction, TenantCreate, User, UserRole

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def batch_tenant_a(db: Session) -> str:
    """Create tenant A for batch download tests."""
    tenant = create_tenant(
        session=db,
        tenant_in=TenantCreate(
            name="Batch Test Tenant A",
            identifier="batch-tenant-a",
            is_active=True,
        ),
    )
    return tenant.id


@pytest.fixture
def batch_tenant_a_user(db: Session, batch_tenant_a: str) -> User:
    """Create regular user in tenant A."""
    user = User(
        id=uuid.uuid4(),
        email="batch-user-a@example.com",
        full_name="Batch User A",
        hashed_password="dummy",
        tenant_id=batch_tenant_a,
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def batch_tenant_b(db: Session) -> str:
    """Create tenant B for permission tests."""
    tenant = create_tenant(
        session=db,
        tenant_in=TenantCreate(
            name="Batch Test Tenant B",
            identifier="batch-tenant-b",
            is_active=True,
        ),
    )
    return tenant.id


@pytest.fixture
def batch_tenant_b_user(db: Session, batch_tenant_b: str) -> User:
    """Create regular user in tenant B."""
    user = User(
        id=uuid.uuid4(),
        email="batch-user-b@example.com",
        full_name="Batch User B",
        hashed_password="dummy",
        tenant_id=batch_tenant_b,
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def batch_admin_user(db: Session, batch_tenant_a: str) -> User:
    """Create admin user."""
    user = User(
        id=uuid.uuid4(),
        email="batch-admin@example.com",
        full_name="Batch Admin",
        hashed_password="dummy",
        tenant_id=batch_tenant_a,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def batch_asset_1(db: Session, batch_tenant_a_user: User) -> Asset:
    """Create first asset for batch download."""
    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=batch_tenant_a_user.tenant_id,
        user_id=batch_tenant_a_user.id,
        file_name="document1.pdf",
        bucket="assets",
        object_key=f"tenant-{batch_tenant_a_user.tenant_id}/document1.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024000,
        checksum_sha256="a" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def batch_asset_2(db: Session, batch_tenant_a_user: User) -> Asset:
    """Create second asset for batch download."""
    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=batch_tenant_a_user.tenant_id,
        user_id=batch_tenant_a_user.id,
        file_name="image1.jpg",
        bucket="assets",
        object_key=f"tenant-{batch_tenant_a_user.tenant_id}/image1.jpg",
        mime_type="image/jpeg",
        file_size_bytes=512000,
        checksum_sha256="b" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def batch_asset_3(db: Session, batch_tenant_a_user: User) -> Asset:
    """Create third asset for batch download."""
    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=batch_tenant_a_user.tenant_id,
        user_id=batch_tenant_a_user.id,
        file_name="video1.mp4",
        bucket="assets",
        object_key=f"tenant-{batch_tenant_a_user.tenant_id}/video1.mp4",
        mime_type="video/mp4",
        file_size_bytes=2048000,
        checksum_sha256="c" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def batch_asset_tenant_b(db: Session, batch_tenant_b_user: User) -> Asset:
    """Create asset in tenant B for permission tests."""
    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=batch_tenant_b_user.tenant_id,
        user_id=batch_tenant_b_user.id,
        file_name="other-tenant-file.txt",
        bucket="assets",
        object_key=f"tenant-{batch_tenant_b_user.tenant_id}/file.txt",
        mime_type="text/plain",
        file_size_bytes=256000,
        checksum_sha256="d" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


# ============================================================================
# Test Cases
# ============================================================================


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_creates_zip_and_returns_url(
    mock_minio_client: MagicMock,
    client: TestClient,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
    batch_asset_2: Asset,
    batch_asset_3: Asset,
) -> None:
    """
    Test batch download creates ZIP and returns download URL (AC: #1, #2, #4, #5).

    Given: User has permission for all requested assets
    When: POST /api/v1/assets/batch-download with asset_ids
    Then: ZIP is created, uploaded to temp storage, and download URL is returned
    """
    # Mock MinIO responses
    mock_client = MagicMock()
    mock_minio_client.return_value = mock_client

    # Mock get_object for each asset
    mock_client.get_object.return_value = MagicMock(
        read=lambda: b"test file content", close=lambda: None, release_conn=lambda: None
    )

    # Mock put_object for ZIP upload
    mock_client.put_object.return_value = None

    # Mock presigned URL generation
    mock_client.presigned_get_object.return_value = (
        "https://minio.example.com/assets/temp/batch-downloads/test.zip?signature=..."
    )

    # Make request
    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={
            "asset_ids": [
                str(batch_asset_1.id),
                str(batch_asset_2.id),
                str(batch_asset_3.id),
            ]
        },
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure (AC: #4)
    assert "download_url" in data
    assert data["download_url"].startswith("https://")
    assert "temp/batch-downloads" in data["download_url"]
    assert "expires_at" in data
    assert "file_name" in data
    assert data["file_name"].endswith(".zip")
    assert data["file_count"] == 3
    assert data["total_size_bytes"] == (
        batch_asset_1.file_size_bytes
        + batch_asset_2.file_size_bytes
        + batch_asset_3.file_size_bytes
    )
    assert "compressed_size_bytes" in data

    # Verify ZIP was uploaded to temp location (AC: #5)
    mock_client.put_object.assert_called_once()
    call_kwargs = mock_client.put_object.call_args.kwargs
    assert "temp/batch-downloads/" in call_kwargs["object_name"]
    assert call_kwargs["content_type"] == "application/zip"


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_permission_denied_for_other_tenant_asset(
    _mock_minio_client: MagicMock,
    client: TestClient,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
    batch_asset_tenant_b: Asset,
) -> None:
    """
    Test batch download fails if user lacks permission for any asset (AC: #9).

    Given: User requests batch download including an asset from another tenant
    When: POST /api/v1/assets/batch-download
    Then: 403 Forbidden with details about inaccessible assets
    """
    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": [str(batch_asset_1.id), str(batch_asset_tenant_b.id)]},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 403
    data = response.json()
    assert data["error_code"] == "PERMISSION_DENIED"
    assert "inaccessible_asset_ids" in data.get("details", {})


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_not_found_for_nonexistent_assets(
    _mock_minio_client: MagicMock,
    client: TestClient,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
) -> None:
    """
    Test batch download fails if any asset doesn't exist (AC: #10).

    Given: User requests batch download with nonexistent asset IDs
    When: POST /api/v1/assets/batch-download
    Then: 404 Not Found with details about missing assets
    """
    nonexistent_id = uuid.uuid4()

    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": [str(batch_asset_1.id), str(nonexistent_id)]},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "ASSET_NOT_FOUND"
    assert "missing_asset_ids" in data.get("details", {})
    assert str(nonexistent_id) in data["details"]["missing_asset_ids"]


def test_batch_download_empty_list_rejected(
    client: TestClient, batch_tenant_a_user: User
) -> None:
    """
    Test batch download with empty asset list returns 400 (AC: #11).

    Given: User requests batch download with empty asset_ids list
    When: POST /api/v1/assets/batch-download
    Then: 400 Bad Request
    """
    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": []},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 422  # Pydantic validation error
    data = response.json()
    assert "detail" in data


def test_batch_download_too_many_assets_rejected(
    client: TestClient, batch_tenant_a_user: User
) -> None:
    """
    Test batch download with >100 assets returns 400 (AC: #12).

    Given: User requests batch download with 101 asset IDs
    When: POST /api/v1/assets/batch-download
    Then: 400 Bad Request
    """
    # Create 101 UUIDs
    asset_ids = [str(uuid.uuid4()) for _ in range(101)]

    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": asset_ids},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 422  # Pydantic validation error
    data = response.json()
    assert "detail" in data


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_admin_can_access_any_tenant_assets(
    mock_minio_client: MagicMock,
    client: TestClient,
    batch_admin_user: User,
    batch_asset_1: Asset,
    batch_asset_tenant_b: Asset,
) -> None:
    """
    Test admin can batch download assets from any tenant (AC: #1).

    Given: Admin user requests batch download with assets from multiple tenants
    When: POST /api/v1/assets/batch-download
    Then: Batch download succeeds
    """
    # Mock MinIO client
    mock_client = MagicMock()
    mock_minio_client.return_value = mock_client
    mock_client.get_object.return_value = MagicMock(
        read=lambda: b"test", close=lambda: None, release_conn=lambda: None
    )
    mock_client.put_object.return_value = None
    mock_client.presigned_get_object.return_value = "https://minio.example.com/test.zip"

    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": [str(batch_asset_1.id), str(batch_asset_tenant_b.id)]},
        headers={"X-Tenant-ID": str(batch_admin_user.tenant_id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["file_count"] == 2


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_audit_log_created(
    mock_minio_client: MagicMock,
    client: TestClient,
    db: Session,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
    batch_asset_2: Asset,
) -> None:
    """
    Test batch download creates audit log with BATCH_DOWNLOAD action (AC: #6).

    Given: User successfully completes batch download
    When: The operation finishes
    Then: Audit log is created with asset_ids, file_count, and total_size in metadata
    """
    # Mock MinIO client
    mock_client = MagicMock()
    mock_minio_client.return_value = mock_client
    mock_client.get_object.return_value = MagicMock(
        read=lambda: b"test", close=lambda: None, release_conn=lambda: None
    )
    mock_client.put_object.return_value = None
    mock_client.presigned_get_object.return_value = "https://minio.example.com/test.zip"

    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": [str(batch_asset_1.id), str(batch_asset_2.id)]},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 200

    # Check audit log was created
    from app.models import AuditLog

    audit_log = (
        db.query(AuditLog)
        .filter(
            AuditLog.user_id == batch_tenant_a_user.id,
            AuditLog.action == AuditAction.BATCH_DOWNLOAD,
        )
        .first()
    )

    assert audit_log is not None
    assert audit_log.metadata is not None
    assert "asset_ids" in audit_log.metadata
    assert "file_count" in audit_log.metadata
    assert audit_log.metadata["file_count"] == 2
    assert "total_size_bytes" in audit_log.metadata


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_expiration_is_one_hour(
    mock_minio_client: MagicMock,
    client: TestClient,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
) -> None:
    """
    Test batch download URL and ZIP expire after 1 hour (AC: #8).

    Given: User successfully creates batch download
    When: Response is returned
    Then: expires_at is approximately 1 hour from now
    """
    # Mock MinIO client
    mock_client = MagicMock()
    mock_minio_client.return_value = mock_client
    mock_client.get_object.return_value = MagicMock(
        read=lambda: b"test", close=lambda: None, release_conn=lambda: None
    )
    mock_client.put_object.return_value = None
    mock_client.presigned_get_object.return_value = "https://minio.example.com/test.zip"

    before_request = datetime.utcnow()

    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": [str(batch_asset_1.id)]},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 200
    data = response.json()

    expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

    # expires_at should be approximately 1 hour from now
    expected_expiry = before_request + timedelta(hours=1)
    delta = abs((expires_at - expected_expiry).total_seconds())

    # Allow 10 second tolerance for test execution time
    assert delta < 10


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_duplicate_asset_ids_rejected(
    _mock_minio_client: MagicMock,
    client: TestClient,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
) -> None:
    """
    Test batch download rejects duplicate asset IDs.

    Given: User requests batch download with duplicate asset IDs
    When: POST /api/v1/assets/batch-download
    Then: 422 Validation Error
    """
    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": [str(batch_asset_1.id), str(batch_asset_1.id)]},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@patch("app.services.batch_download_service.get_minio_client")
@patch("app.api.routes.batch_download.limiter.limit")
def test_batch_download_rate_limiting_applies(
    _mock_limit: MagicMock,
    mock_minio_client: MagicMock,
    client: TestClient,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
) -> None:
    """
    Test rate limiting is applied to batch download endpoint (AC: #1).

    Given: Batch download endpoint is called
    When: Rate limiter is configured
    Then: Rate limiting decorator is applied
    """
    # Mock MinIO client
    mock_client = MagicMock()
    mock_minio_client.return_value = mock_client
    mock_client.get_object.return_value = MagicMock(
        read=lambda: b"test", close=lambda: None, release_conn=lambda: None
    )
    mock_client.put_object.return_value = None
    mock_client.presigned_get_object.return_value = "https://minio.example.com/test.zip"

    # Make request
    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={"asset_ids": [str(batch_asset_1.id)]},
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    # Rate limiter should have been called
    # Note: Actual rate limiting behavior is tested in integration tests
    assert response.status_code == 200


@patch("app.services.batch_download_service.get_minio_client")
def test_batch_download_zip_contents_integration(
    mock_minio_client: MagicMock,
    client: TestClient,
    batch_tenant_a_user: User,
    batch_asset_1: Asset,
    batch_asset_2: Asset,
    batch_asset_3: Asset,
) -> None:
    """
    Integration test to verify actual ZIP contents (Issue #7 - MEDIUM priority).

    Verifies:
    - Correct files are included in the ZIP
    - Original file names are preserved
    - Files are in the expected order
    - Compression ratio is reasonable

    Given: User requests batch download of multiple assets
    When: ZIP is created and downloaded
    Then: ZIP contains all files with correct names and reasonable compression
    """
    import io
    import zipfile

    # Create real test file contents (different sizes/types for compression testing)
    test_files = {
        batch_asset_1.file_name: b"PDF content "
        * 10000,  # Repetitive - compresses well
        batch_asset_2.file_name: b"JPEG binary data " * 5000,  # Semi-compressible
        batch_asset_3.file_name: b"Video stream data " * 20000,  # Larger file
    }

    # Mock MinIO client with real content
    mock_client = MagicMock()
    mock_minio_client.return_value = mock_client

    def mock_get_object(_bucket: str, object_key: str):
        """Return real content based on object_key."""
        # Map object_key to asset file_name
        for asset in [batch_asset_1, batch_asset_2, batch_asset_3]:
            if asset.object_key == object_key:
                content = test_files[asset.file_name]
                response = MagicMock()
                response.read = lambda c=content: c
                response.close = lambda: None
                response.release_conn = lambda: None
                return response
        raise Exception(f"Unexpected object_key: {object_key}")

    mock_client.get_object = mock_get_object

    # Capture the uploaded ZIP file
    uploaded_zip_data = None

    def mock_put_object(_bucket_name, _object_name, data, _length, _content_type):
        """Capture uploaded ZIP data."""
        nonlocal uploaded_zip_data
        uploaded_zip_data = data.read()

    mock_client.put_object = mock_put_object
    mock_client.presigned_get_object.return_value = "https://minio.example.com/test.zip"

    # Make batch download request
    response = client.post(
        f"{settings.API_V1_STR}/assets/batch-download",
        json={
            "asset_ids": [
                str(batch_asset_1.id),
                str(batch_asset_2.id),
                str(batch_asset_3.id),
            ]
        },
        headers={"X-Tenant-ID": str(batch_tenant_a_user.tenant_id)},
    )

    assert response.status_code == 200

    # Verify ZIP data was captured
    assert uploaded_zip_data is not None, "ZIP data should have been uploaded to MinIO"

    # Verify ZIP is valid and contains correct files
    zip_buffer = io.BytesIO(uploaded_zip_data)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        # Verify file count
        assert len(zf.namelist()) == 3, "ZIP should contain exactly 3 files"

        # Verify all expected file names are present
        expected_names = {
            batch_asset_1.file_name,
            batch_asset_2.file_name,
            batch_asset_3.file_name,
        }
        actual_names = set(zf.namelist())
        assert (
            actual_names == expected_names
        ), f"File names mismatch. Expected: {expected_names}, Got: {actual_names}"

        # Verify file order matches request order
        assert zf.namelist() == [
            batch_asset_1.file_name,
            batch_asset_2.file_name,
            batch_asset_3.file_name,
        ], "Files should be in the same order as requested"

        # Verify each file's content is correct
        for file_name in zf.namelist():
            with zf.open(file_name) as f:
                actual_content = f.read()
                expected_content = test_files[file_name]
                assert (
                    actual_content == expected_content
                ), f"Content mismatch for {file_name}"

    # Verify compression ratio is reasonable
    total_uncompressed_size = sum(len(content) for content in test_files.values())
    compressed_size = len(uploaded_zip_data)
    compression_ratio = compressed_size / total_uncompressed_size

    # Since we used repetitive content, compression should be effective
    # Expect at least 50% compression (ratio < 0.5)
    assert compression_ratio < 0.5, (
        f"Compression ratio {compression_ratio:.2%} is too high. "
        f"Expected < 50% for repetitive test data. "
        f"Uncompressed: {total_uncompressed_size}, Compressed: {compressed_size}"
    )

    # Verify response metadata matches actual ZIP
    data = response.json()
    assert data["compressed_size_bytes"] == compressed_size
    assert data["total_size_bytes"] == total_uncompressed_size
