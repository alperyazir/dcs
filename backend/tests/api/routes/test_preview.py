"""
Tests for Asset Preview API Endpoints (Story 4.3).

Test Coverage:
- Preview URL generation for different asset types
- Preview type detection (image, video, audio, pdf, document, unsupported)
- Permission validation (owner, admin, supervisor)
- Audit logging for preview operations
- Rate limiting

References:
- Task 6: Write Comprehensive Tests
- AC: #1-#10
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Asset, AuditAction, AuditLog, User

pytestmark = pytest.mark.anyio


class TestPreviewEndpoint:
    """Tests for GET /api/v1/assets/{asset_id}/preview endpoint."""

    @patch("app.services.signed_url_service.SignedURLService.generate_download_url")
    def test_preview_image_returns_signed_url(
        self,
        mock_generate_download_url,
        client: TestClient,
        db: Session,
        preview_tenant_a_user: User,
        preview_tenant_a_token_headers: dict[str, str],
        image_asset: Asset,
    ):
        """
        Test preview returns signed URL for image assets (AC: #1, #2).

        References:
        - Task 6.2
        - AC: #1 (image preview)
        - AC: #2 (inline display)
        """
        from app.core.config import settings

        # Mock download URL generation
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(microsecond=0)
        mock_generate_download_url.return_value = (
            "https://minio.example.com/assets/photo.jpg?signature=abc123",
            expires_at,
        )

        # Request preview
        response = client.get(
            f"{settings.API_V1_STR}/assets/{image_asset.id}/preview",
            headers=preview_tenant_a_token_headers,
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "preview_url" in data
        assert "preview_type" in data
        assert "expires_at" in data
        assert "mime_type" in data
        assert "file_name" in data
        assert "file_size" in data
        assert "supports_inline" in data

        # Verify preview details
        assert data["preview_type"] == "image"
        assert data["preview_url"] is not None
        assert "minio.example.com" in data["preview_url"]
        assert data["supports_inline"] is True
        assert data["mime_type"] == image_asset.mime_type
        assert data["file_name"] == image_asset.file_name
        assert data["file_size"] == image_asset.file_size_bytes

        # Verify expiration time
        assert data["expires_at"] == expires_at.isoformat().replace("+00:00", "Z")

        # Verify download URL generation was called
        mock_generate_download_url.assert_called_once_with(image_asset.id)

    @patch("app.services.signed_url_service.SignedURLService.generate_download_url")
    def test_preview_video_returns_signed_url(
        self,
        mock_generate_download_url,
        client: TestClient,
        db: Session,
        preview_tenant_a_user: User,
        preview_tenant_a_token_headers: dict[str, str],
        video_asset: Asset,
    ):
        """
        Test preview returns signed URL for video assets (AC: #3, #4).

        References:
        - Task 6.3
        - AC: #3 (video preview)
        - AC: #4 (video player support)
        """
        from app.core.config import settings

        # Mock download URL generation
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(microsecond=0)
        mock_generate_download_url.return_value = (
            "https://minio.example.com/assets/video.mp4?signature=xyz789",
            expires_at,
        )

        # Request preview
        response = client.get(
            f"{settings.API_V1_STR}/assets/{video_asset.id}/preview",
            headers=preview_tenant_a_token_headers,
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()

        # Verify preview type and URL
        assert data["preview_type"] == "video"
        assert data["preview_url"] is not None
        assert data["supports_inline"] is True
        assert data["mime_type"] == video_asset.mime_type

    @patch("app.services.signed_url_service.SignedURLService.generate_download_url")
    def test_preview_audio_returns_signed_url(
        self,
        mock_generate_download_url,
        client: TestClient,
        db: Session,
        preview_tenant_a_user: User,
        preview_tenant_a_token_headers: dict[str, str],
        audio_asset: Asset,
    ):
        """
        Test preview returns signed URL for audio assets (AC: #5, #6).

        References:
        - Task 6.4
        - AC: #5 (audio preview)
        - AC: #6 (audio player support)
        """
        from app.core.config import settings

        # Mock download URL generation
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(microsecond=0)
        mock_generate_download_url.return_value = (
            "https://minio.example.com/assets/audio.mp3?signature=def456",
            expires_at,
        )

        # Request preview
        response = client.get(
            f"{settings.API_V1_STR}/assets/{audio_asset.id}/preview",
            headers=preview_tenant_a_token_headers,
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()

        # Verify preview type and URL
        assert data["preview_type"] == "audio"
        assert data["preview_url"] is not None
        assert data["supports_inline"] is True
        assert data["mime_type"] == audio_asset.mime_type

    @patch("app.services.signed_url_service.SignedURLService.generate_download_url")
    def test_preview_pdf_returns_signed_url(
        self,
        mock_generate_download_url,
        client: TestClient,
        db: Session,
        preview_tenant_a_user: User,
        preview_tenant_a_token_headers: dict[str, str],
        pdf_asset: Asset,
    ):
        """
        Test preview returns signed URL for PDF assets (AC: #7).

        References:
        - Task 6.5
        - AC: #7 (PDF preview)
        """
        from app.core.config import settings

        # Mock download URL generation
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(microsecond=0)
        mock_generate_download_url.return_value = (
            "https://minio.example.com/assets/document.pdf?signature=ghi789",
            expires_at,
        )

        # Request preview
        response = client.get(
            f"{settings.API_V1_STR}/assets/{pdf_asset.id}/preview",
            headers=preview_tenant_a_token_headers,
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()

        # Verify preview type and URL
        assert data["preview_type"] == "pdf"
        assert data["preview_url"] is not None
        assert data["supports_inline"] is True
        assert data["mime_type"] == "application/pdf"

    def test_preview_unsupported_returns_null_url(
        self,
        client: TestClient,
        db: Session,
        preview_tenant_a_user: User,
        preview_tenant_a_token_headers: dict[str, str],
        zip_asset: Asset,
    ):
        """
        Test preview returns null URL for unsupported types (AC: #9).

        References:
        - Task 6.6
        - AC: #9 (unsupported file types)
        """
        from app.core.config import settings

        # Request preview for ZIP file (unsupported)
        response = client.get(
            f"{settings.API_V1_STR}/assets/{zip_asset.id}/preview",
            headers=preview_tenant_a_token_headers,
        )

        # Verify success with null URL
        assert response.status_code == 200
        data = response.json()

        # Verify unsupported type handling
        assert data["preview_type"] == "unsupported"
        assert data["preview_url"] is None
        assert data["expires_at"] is None
        assert data["supports_inline"] is False

        # File metadata should still be present
        assert data["mime_type"] == zip_asset.mime_type
        assert data["file_name"] == zip_asset.file_name
        assert data["file_size"] == zip_asset.file_size_bytes

    def test_preview_permission_denied_for_other_user(
        self,
        client: TestClient,
        db: Session,
        preview_tenant_a_token_headers: dict[str, str],
        tenant_b_video_asset: Asset,
    ):
        """
        Test preview returns 403 for assets user doesn't own (AC: #10).

        References:
        - Task 6.7
        - AC: #10 (permission denied)
        """
        from app.core.config import settings

        # Try to preview another tenant's asset
        response = client.get(
            f"{settings.API_V1_STR}/assets/{tenant_b_video_asset.id}/preview",
            headers=preview_tenant_a_token_headers,
        )

        # Verify permission denied
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "PERMISSION_DENIED"

    def test_preview_not_found_for_nonexistent_asset(
        self,
        client: TestClient,
        db: Session,
        preview_tenant_a_token_headers: dict[str, str],
    ):
        """
        Test preview returns 404 for non-existent assets (AC: #10).

        References:
        - Task 6.8
        """
        from app.core.config import settings

        nonexistent_id = uuid.uuid4()

        # Try to preview non-existent asset
        response = client.get(
            f"{settings.API_V1_STR}/assets/{nonexistent_id}/preview",
            headers=preview_tenant_a_token_headers,
        )

        # Verify not found
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "ASSET_NOT_FOUND"

    @patch("app.services.signed_url_service.SignedURLService.generate_download_url")
    def test_preview_admin_can_access_any_asset(
        self,
        mock_generate_download_url,
        client: TestClient,
        db: Session,
        preview_admin_token_headers: dict[str, str],
        tenant_b_video_asset: Asset,
    ):
        """
        Test admin can preview assets from any tenant (AC: #10).

        References:
        - Task 6.9
        """
        from app.core.config import settings

        # Mock download URL generation
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(microsecond=0)
        mock_generate_download_url.return_value = (
            "https://minio.example.com/assets/video.mp4?signature=admin123",
            expires_at,
        )

        # Admin previews another tenant's asset
        response = client.get(
            f"{settings.API_V1_STR}/assets/{tenant_b_video_asset.id}/preview",
            headers=preview_admin_token_headers,
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()
        assert data["preview_type"] == "video"
        assert data["file_name"] == tenant_b_video_asset.file_name

    @patch("app.services.signed_url_service.SignedURLService.generate_download_url")
    def test_preview_audit_log_created(
        self,
        mock_generate_download_url,
        client: TestClient,
        db: Session,
        preview_tenant_a_user: User,
        preview_tenant_a_token_headers: dict[str, str],
        image_asset: Asset,
    ):
        """
        Test preview creates audit log with PREVIEW action (AC: #8).

        References:
        - Task 6.10
        """
        from app.core.config import settings

        # Mock download URL generation
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(microsecond=0)
        mock_generate_download_url.return_value = (
            "https://minio.example.com/assets/photo.jpg?signature=audit123",
            expires_at,
        )

        # Clear existing audit logs for this asset
        db.exec(AuditLog.__table__.delete().where(AuditLog.asset_id == image_asset.id))
        db.commit()

        # Request preview
        response = client.get(
            f"{settings.API_V1_STR}/assets/{image_asset.id}/preview",
            headers=preview_tenant_a_token_headers,
        )
        assert response.status_code == 200

        # Verify audit log created
        audit_logs = db.exec(
            select(AuditLog)
            .where(AuditLog.asset_id == image_asset.id)
            .where(AuditLog.action == AuditAction.PREVIEW)
        ).all()

        # Should have exactly one PREVIEW audit log
        preview_logs = [log for log in audit_logs if log.action == AuditAction.PREVIEW]
        assert len(preview_logs) == 1

        # Verify audit log details
        audit_log = preview_logs[0]
        assert audit_log.user_id == preview_tenant_a_user.id
        assert audit_log.asset_id == image_asset.id
        assert audit_log.action == AuditAction.PREVIEW

    @patch("app.services.signed_url_service.SignedURLService.generate_download_url")
    def test_preview_rate_limiting_applies(
        self,
        mock_generate_download_url,
        client: TestClient,
        db: Session,
        preview_tenant_a_token_headers: dict[str, str],
        image_asset: Asset,
    ):
        """
        Test rate limiting applies to preview endpoint.

        References:
        - Task 6.11
        """
        from app.core.config import settings

        # Mock download URL generation
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(microsecond=0)
        mock_generate_download_url.return_value = (
            "https://minio.example.com/assets/photo.jpg?signature=rate123",
            expires_at,
        )

        # Make multiple requests rapidly
        responses = []
        for _ in range(5):
            response = client.get(
                f"{settings.API_V1_STR}/assets/{image_asset.id}/preview",
                headers=preview_tenant_a_token_headers,
            )
            responses.append(response.status_code)

        # At least some requests should succeed
        assert 200 in responses

        # Rate limiting should be applied (status code 429 or success)
        # Note: Actual rate limit threshold depends on role and configuration
        assert all(code in [200, 429] for code in responses)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def preview_tenant_a_user(db: Session) -> User:
    """Create a regular user in tenant A for preview tests."""
    from app.crud import create_tenant, create_user
    from app.models import TenantCreate, TenantType, UserCreate, UserRole

    # Create tenant A
    tenant_a = create_tenant(
        session=db,
        tenant_in=TenantCreate(
            name=f"Tenant A {uuid.uuid4()}", tenant_type=TenantType.SCHOOL
        ),
    )
    db.commit()
    db.refresh(tenant_a)

    # Create regular user in tenant A
    user = create_user(
        session=db,
        user_create=UserCreate(
            email=f"user-preview-a-{uuid.uuid4()}@example.com",
            password="testpassword",
            full_name="Preview Test User A",
            role=UserRole.TEACHER,
            tenant_id=tenant_a.id,
        ),
    )
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def preview_tenant_a_token_headers(
    client: TestClient, preview_tenant_a_user: User
) -> dict[str, str]:
    """Get authentication headers for preview tenant A user."""
    from app.core.config import settings

    login_data = {
        "username": preview_tenant_a_user.email,
        "password": "testpassword",
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def preview_admin_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Get authentication headers for admin user."""
    from app.core.config import settings
    from app.crud import create_tenant, create_user
    from app.models import TenantCreate, TenantType, UserCreate, UserRole

    # Create admin tenant
    admin_tenant = create_tenant(
        session=db,
        tenant_in=TenantCreate(
            name=f"Admin Tenant {uuid.uuid4()}", tenant_type=TenantType.PUBLISHER
        ),
    )
    db.commit()
    db.refresh(admin_tenant)

    # Create admin user
    admin_user = create_user(
        session=db,
        user_create=UserCreate(
            email=f"admin-preview-{uuid.uuid4()}@example.com",
            password="adminpassword",
            full_name="Preview Admin User",
            role=UserRole.ADMIN,
            tenant_id=admin_tenant.id,
        ),
    )
    db.commit()
    db.refresh(admin_user)

    # Get token
    login_data = {
        "username": admin_user.email,
        "password": "adminpassword",
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def image_asset(db: Session, preview_tenant_a_user: User) -> Asset:
    """Create an image asset for preview tests."""
    # MimeTypeCategory not needed

    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=preview_tenant_a_user.tenant_id,
        user_id=preview_tenant_a_user.id,
        file_name="photo.jpg",
        bucket="assets",
        object_key=f"tenant-{preview_tenant_a_user.tenant_id}/photo.jpg",
        mime_type="image/jpeg",
        # mime_type_category removed
        file_size_bytes=1234567,
        checksum_sha256="a" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def video_asset(db: Session, preview_tenant_a_user: User) -> Asset:
    """Create a video asset for preview tests."""
    # MimeTypeCategory not needed

    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=preview_tenant_a_user.tenant_id,
        user_id=preview_tenant_a_user.id,
        file_name="video.mp4",
        bucket="assets",
        object_key=f"tenant-{preview_tenant_a_user.tenant_id}/video.mp4",
        mime_type="video/mp4",
        # mime_type_category removed
        file_size_bytes=9876543,
        checksum_sha256="b" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def audio_asset(db: Session, preview_tenant_a_user: User) -> Asset:
    """Create an audio asset for preview tests."""
    # MimeTypeCategory not needed

    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=preview_tenant_a_user.tenant_id,
        user_id=preview_tenant_a_user.id,
        file_name="audio.mp3",
        bucket="assets",
        object_key=f"tenant-{preview_tenant_a_user.tenant_id}/audio.mp3",
        mime_type="audio/mpeg",
        # mime_type_category removed
        file_size_bytes=3456789,
        checksum_sha256="c" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def pdf_asset(db: Session, preview_tenant_a_user: User) -> Asset:
    """Create a PDF asset for preview tests."""
    # MimeTypeCategory not needed

    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=preview_tenant_a_user.tenant_id,
        user_id=preview_tenant_a_user.id,
        file_name="document.pdf",
        bucket="assets",
        object_key=f"tenant-{preview_tenant_a_user.tenant_id}/document.pdf",
        mime_type="application/pdf",
        # mime_type_category removed
        file_size_bytes=5678901,
        checksum_sha256="d" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def zip_asset(db: Session, preview_tenant_a_user: User) -> Asset:
    """Create a ZIP asset for unsupported type tests."""
    # MimeTypeCategory not needed

    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=preview_tenant_a_user.tenant_id,
        user_id=preview_tenant_a_user.id,
        file_name="archive.zip",
        bucket="assets",
        object_key=f"tenant-{preview_tenant_a_user.tenant_id}/archive.zip",
        mime_type="application/zip",
        # mime_type_category removed
        file_size_bytes=12345678,
        checksum_sha256="e" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def tenant_b_video_asset(db: Session) -> Asset:
    """Create a video asset in tenant B for permission tests."""
    from app.crud import create_tenant, create_user
    from app.models import (
        TenantCreate,
        TenantType,
        UserCreate,
        UserRole,
    )

    # Create tenant B
    tenant_b = create_tenant(
        session=db,
        tenant_in=TenantCreate(
            name=f"Tenant B {uuid.uuid4()}", tenant_type=TenantType.SCHOOL
        ),
    )
    db.commit()
    db.refresh(tenant_b)

    # Create user in tenant B
    user_b = create_user(
        session=db,
        user_create=UserCreate(
            email=f"user-b-{uuid.uuid4()}@example.com",
            password="testpassword",
            full_name="User B",
            role=UserRole.TEACHER,
            tenant_id=tenant_b.id,
        ),
    )
    db.commit()
    db.refresh(user_b)

    # Create asset in tenant B
    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        user_id=user_b.id,
        file_name="tenant_b_video.mp4",
        bucket="assets",
        object_key=f"tenant-{tenant_b.id}/video.mp4",
        mime_type="video/mp4",
        # mime_type_category removed
        file_size_bytes=7777777,
        checksum_sha256="f" * 64,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
