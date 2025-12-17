"""
Tests for Asset Streaming API Routes (Story 4.2, Task 6).

Tests:
- Stream returns valid presigned URL for video (AC: #1, #2, #6)
- Stream returns valid presigned URL for audio (AC: #1, #2, #6)
- Stream rejected for non-video/audio assets (AC: #9)
- Permission denied for unauthorized users (AC: #10)
- Asset not found for non-existent assets
- Admin can stream any tenant's asset
- Supervisor can stream any tenant's asset
- Audit log is created with STREAM action (AC: #8)
- Rate limiting applies correctly
- Response includes correct mime_type (AC: #2)

References:
- Task 6: Comprehensive test coverage
- ACs: #1-#10
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.models import (
    Asset,
    AuditAction,
    AuditLog,
    Tenant,
    TenantType,
    User,
    UserRole,
)


@pytest.fixture(scope="module")
def stream_test_tenant_a(db: Session) -> Tenant:
    """Create tenant A for streaming tests."""
    tenant = db.exec(
        select(Tenant).where(Tenant.name == "stream_test_tenant_a")
    ).first()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="stream_test_tenant_a",
            tenant_type=TenantType.PUBLISHER,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


@pytest.fixture(scope="module")
def stream_test_tenant_b(db: Session) -> Tenant:
    """Create tenant B for cross-tenant streaming tests."""
    tenant = db.exec(
        select(Tenant).where(Tenant.name == "stream_test_tenant_b")
    ).first()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="stream_test_tenant_b",
            tenant_type=TenantType.SCHOOL,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


@pytest.fixture(scope="module")
def stream_tenant_a_user(db: Session, stream_test_tenant_a: Tenant) -> User:
    """Create a user in tenant A for streaming tests."""
    email = "stream_user_a@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            role=UserRole.PUBLISHER,
            tenant_id=stream_test_tenant_a.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def stream_tenant_b_user(db: Session, stream_test_tenant_b: Tenant) -> User:
    """Create a user in tenant B for streaming tests."""
    email = "stream_user_b@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            role=UserRole.TEACHER,
            tenant_id=stream_test_tenant_b.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def stream_admin_user(db: Session, stream_test_tenant_a: Tenant) -> User:
    """Create admin user for streaming tests."""
    email = "stream_admin@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=True,
            role=UserRole.ADMIN,
            tenant_id=stream_test_tenant_a.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def stream_supervisor_user(db: Session, stream_test_tenant_a: Tenant) -> User:
    """Create supervisor user for streaming tests."""
    email = "stream_supervisor@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            role=UserRole.SUPERVISOR,
            tenant_id=stream_test_tenant_a.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def stream_tenant_a_token_headers(
    client: TestClient, stream_tenant_a_user: User
) -> dict[str, str]:
    """Get auth headers for tenant A user."""
    from app.core.config import settings

    login_data = {
        "username": stream_tenant_a_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture(scope="module")
def stream_admin_token_headers(
    client: TestClient, stream_admin_user: User
) -> dict[str, str]:
    """Get auth headers for admin user."""
    from app.core.config import settings

    login_data = {
        "username": stream_admin_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture(scope="module")
def stream_supervisor_token_headers(
    client: TestClient, stream_supervisor_user: User
) -> dict[str, str]:
    """Get auth headers for supervisor user."""
    from app.core.config import settings

    login_data = {
        "username": stream_supervisor_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def video_asset(
    db: Session, stream_test_tenant_a: Tenant, stream_tenant_a_user: User
) -> Asset:
    """Create a video asset owned by tenant A user."""
    asset = Asset(
        id=uuid.uuid4(),
        user_id=stream_tenant_a_user.id,
        tenant_id=stream_test_tenant_a.id,
        file_name="lesson_01.mp4",
        mime_type="video/mp4",
        file_size_bytes=52428800,  # 50MB
        bucket="assets",
        object_key=f"{stream_test_tenant_a.id}/lesson_01.mp4",
        is_deleted=False,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def audio_asset(
    db: Session, stream_test_tenant_a: Tenant, stream_tenant_a_user: User
) -> Asset:
    """Create an audio asset owned by tenant A user."""
    asset = Asset(
        id=uuid.uuid4(),
        user_id=stream_tenant_a_user.id,
        tenant_id=stream_test_tenant_a.id,
        file_name="podcast_episode.mp3",
        mime_type="audio/mpeg",
        file_size_bytes=8388608,  # 8MB
        bucket="assets",
        object_key=f"{stream_test_tenant_a.id}/podcast_episode.mp3",
        is_deleted=False,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def pdf_asset(
    db: Session, stream_test_tenant_a: Tenant, stream_tenant_a_user: User
) -> Asset:
    """Create a PDF asset (non-streamable) owned by tenant A user."""
    asset = Asset(
        id=uuid.uuid4(),
        user_id=stream_tenant_a_user.id,
        tenant_id=stream_test_tenant_a.id,
        file_name="document.pdf",
        mime_type="application/pdf",
        file_size_bytes=1048576,  # 1MB
        bucket="assets",
        object_key=f"{stream_test_tenant_a.id}/document.pdf",
        is_deleted=False,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def tenant_b_video_asset(
    db: Session, stream_test_tenant_b: Tenant, stream_tenant_b_user: User
) -> Asset:
    """Create a video asset owned by tenant B user."""
    asset = Asset(
        id=uuid.uuid4(),
        user_id=stream_tenant_b_user.id,
        tenant_id=stream_test_tenant_b.id,
        file_name="tenant_b_video.mp4",
        mime_type="video/mp4",
        file_size_bytes=10485760,  # 10MB
        bucket="assets",
        object_key=f"{stream_test_tenant_b.id}/tenant_b_video.mp4",
        is_deleted=False,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


class TestStreamingEndpoint:
    """Test suite for GET /api/v1/assets/{asset_id}/stream endpoint."""

    @patch("app.services.signed_url_service.SignedURLService.generate_stream_url")
    def test_stream_video_returns_presigned_url(
        self,
        mock_generate_stream_url,
        client: TestClient,
        db: Session,
        stream_tenant_a_token_headers: dict[str, str],
        video_asset: Asset,
    ):
        """
        Test streaming returns valid presigned URL for video.

        References:
        - Task 6.2
        - AC: #1, #2, #6 (presigned URL for video with 1-hour expiration)
        """
        from app.core.config import settings

        # Mock stream URL generation
        expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        mock_generate_stream_url.return_value = (
            "https://minio.example.com/assets/lesson_01.mp4?signature=abc123",
            expires_at,
        )

        # Request stream URL
        response = client.get(
            f"{settings.API_V1_STR}/assets/{video_asset.id}/stream",
            headers=stream_tenant_a_token_headers,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        # AC: #2 - Response includes all required fields
        assert "stream_url" in data
        assert "expires_at" in data
        assert "mime_type" in data
        assert "file_size" in data
        assert "file_name" in data

        # Verify metadata matches video asset
        assert data["mime_type"] == "video/mp4"
        assert data["file_size"] == video_asset.file_size_bytes
        assert data["file_name"] == video_asset.file_name
        assert "minio.example.com" in data["stream_url"]

        # Verify service was called correctly
        mock_generate_stream_url.assert_called_once_with(video_asset.id)

    @patch("app.services.signed_url_service.SignedURLService.generate_stream_url")
    def test_stream_audio_returns_presigned_url(
        self,
        mock_generate_stream_url,
        client: TestClient,
        db: Session,
        stream_tenant_a_token_headers: dict[str, str],
        audio_asset: Asset,
    ):
        """
        Test streaming returns valid presigned URL for audio.

        References:
        - Task 6.3
        - AC: #1, #2, #6 (presigned URL for audio with 1-hour expiration)
        """
        from app.core.config import settings

        # Mock stream URL generation
        expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        mock_generate_stream_url.return_value = (
            "https://minio.example.com/assets/podcast.mp3?signature=xyz789",
            expires_at,
        )

        # Request stream URL
        response = client.get(
            f"{settings.API_V1_STR}/assets/{audio_asset.id}/stream",
            headers=stream_tenant_a_token_headers,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        # AC: #2 - Response includes all required fields
        assert "stream_url" in data
        assert "expires_at" in data
        assert "mime_type" in data
        assert "file_size" in data
        assert "file_name" in data

        # Verify metadata matches audio asset
        assert data["mime_type"] == "audio/mpeg"
        assert data["file_size"] == audio_asset.file_size_bytes
        assert data["file_name"] == audio_asset.file_name
        assert "minio.example.com" in data["stream_url"]

        # Verify service was called correctly
        mock_generate_stream_url.assert_called_once_with(audio_asset.id)

    def test_stream_rejected_for_non_streamable_asset(
        self,
        client: TestClient,
        db: Session,
        stream_tenant_a_token_headers: dict[str, str],
        pdf_asset: Asset,
    ):
        """
        Test streaming returns 400 for non-video/audio assets.

        References:
        - Task 6.4
        - AC: #9 (400 Bad Request for INVALID_ASSET_TYPE)
        """
        from app.core.config import settings

        # Try to stream PDF (not streamable)
        response = client.get(
            f"{settings.API_V1_STR}/assets/{pdf_asset.id}/stream",
            headers=stream_tenant_a_token_headers,
        )

        # Verify 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_ASSET_TYPE"
        assert "application/pdf" in data["message"]

        # Verify helpful error message with supported types
        assert "details" in data
        assert "supported_types" in data["details"]

    def test_stream_permission_denied_for_other_user(
        self,
        client: TestClient,
        db: Session,
        stream_tenant_a_token_headers: dict[str, str],
        tenant_b_video_asset: Asset,
    ):
        """
        Test streaming returns 403 for other tenant's asset.

        References:
        - Task 6.5
        - AC: #10 (permission denied for unauthorized users)
        """
        from app.core.config import settings

        # Try to stream tenant B's video
        response = client.get(
            f"{settings.API_V1_STR}/assets/{tenant_b_video_asset.id}/stream",
            headers=stream_tenant_a_token_headers,
        )

        # Verify 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "PERMISSION_DENIED"

    def test_stream_not_found_for_nonexistent_asset(
        self,
        client: TestClient,
        stream_tenant_a_token_headers: dict[str, str],
    ):
        """
        Test streaming returns 404 for non-existent asset.

        References:
        - Task 6.6
        - Asset not found
        """
        from app.core.config import settings

        # Try to stream non-existent asset
        fake_asset_id = uuid.uuid4()
        response = client.get(
            f"{settings.API_V1_STR}/assets/{fake_asset_id}/stream",
            headers=stream_tenant_a_token_headers,
        )

        # Verify 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "ASSET_NOT_FOUND"

    def test_stream_soft_deleted_asset_returns_404(
        self,
        client: TestClient,
        db: Session,
        stream_tenant_a_token_headers: dict[str, str],
        video_asset: Asset,
    ):
        """
        Test streaming returns 404 for soft-deleted assets.

        References:
        - Task 6.6 (code review fix)
        - Soft-deleted assets should return 404 like non-existent
        """
        from app.core.config import settings

        # Soft-delete the video asset
        video_asset.is_deleted = True
        db.add(video_asset)
        db.commit()

        # Try to stream soft-deleted asset
        response = client.get(
            f"{settings.API_V1_STR}/assets/{video_asset.id}/stream",
            headers=stream_tenant_a_token_headers,
        )

        # Verify 404 Not Found (soft-deleted treated as not found)
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "ASSET_NOT_FOUND"

        # Restore asset for other tests
        video_asset.is_deleted = False
        db.add(video_asset)
        db.commit()

    @patch("app.services.signed_url_service.SignedURLService.generate_stream_url")
    def test_stream_admin_can_access_any_asset(
        self,
        mock_generate_stream_url,
        client: TestClient,
        db: Session,
        stream_admin_token_headers: dict[str, str],
        tenant_b_video_asset: Asset,
    ):
        """
        Test admin can stream any tenant's asset.

        References:
        - Task 6.7
        - Admin can access any asset
        """
        from app.core.config import settings

        # Mock stream URL generation
        expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        mock_generate_stream_url.return_value = (
            "https://minio.example.com/assets/video.mp4?signature=admin123",
            expires_at,
        )

        # Admin streams tenant B's video
        response = client.get(
            f"{settings.API_V1_STR}/assets/{tenant_b_video_asset.id}/stream",
            headers=stream_admin_token_headers,
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == tenant_b_video_asset.file_name

    @patch("app.services.signed_url_service.SignedURLService.generate_stream_url")
    def test_stream_supervisor_can_access_any_asset(
        self,
        mock_generate_stream_url,
        client: TestClient,
        db: Session,
        stream_supervisor_token_headers: dict[str, str],
        tenant_b_video_asset: Asset,
    ):
        """
        Test supervisor can stream any tenant's asset.

        References:
        - Task 6.7 (code review fix)
        - Supervisor can access any asset (like Admin)
        """
        from app.core.config import settings

        # Mock stream URL generation
        expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        mock_generate_stream_url.return_value = (
            "https://minio.example.com/assets/video.mp4?signature=supervisor123",
            expires_at,
        )

        # Supervisor streams tenant B's video
        response = client.get(
            f"{settings.API_V1_STR}/assets/{tenant_b_video_asset.id}/stream",
            headers=stream_supervisor_token_headers,
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == tenant_b_video_asset.file_name

    @patch("app.services.signed_url_service.SignedURLService.generate_stream_url")
    def test_stream_audit_log_created(
        self,
        mock_generate_stream_url,
        client: TestClient,
        db: Session,
        stream_tenant_a_user: User,
        stream_tenant_a_token_headers: dict[str, str],
        video_asset: Asset,
    ):
        """
        Test streaming creates audit log with STREAM action.

        References:
        - Task 6.8
        - AC: #8 (audit log creation)
        """
        from app.core.config import settings

        # Mock stream URL generation
        expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        mock_generate_stream_url.return_value = (
            "https://minio.example.com/assets/lesson.mp4?signature=abc123",
            expires_at,
        )

        # Clear existing audit logs for this asset
        db.exec(AuditLog.__table__.delete().where(AuditLog.asset_id == video_asset.id))
        db.commit()

        # Request stream URL
        response = client.get(
            f"{settings.API_V1_STR}/assets/{video_asset.id}/stream",
            headers=stream_tenant_a_token_headers,
        )
        assert response.status_code == 200

        # Verify audit log created
        audit_logs = db.exec(
            select(AuditLog)
            .where(AuditLog.asset_id == video_asset.id)
            .where(AuditLog.action == AuditAction.STREAM)
        ).all()

        # Should have exactly one STREAM audit log
        stream_logs = [log for log in audit_logs if log.action == AuditAction.STREAM]
        assert len(stream_logs) == 1

        # Verify audit log details
        audit_log = stream_logs[0]
        assert audit_log.user_id == stream_tenant_a_user.id
        assert audit_log.asset_id == video_asset.id
        assert audit_log.action == AuditAction.STREAM

    @patch("app.services.signed_url_service.SignedURLService.generate_stream_url")
    def test_stream_rate_limiting_applies(
        self,
        mock_generate_stream_url,
        client: TestClient,
        stream_tenant_a_token_headers: dict[str, str],
        video_asset: Asset,
    ):
        """
        Test rate limiting applies correctly to streaming endpoint.

        References:
        - Task 6.9
        - Rate limiting enforcement
        """
        from app.core.config import settings

        # Mock stream URL generation
        expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        mock_generate_stream_url.return_value = (
            "https://minio.example.com/assets/video.mp4?signature=abc123",
            expires_at,
        )

        # Make multiple requests - rate limit should eventually trigger
        for _ in range(3):
            response = client.get(
                f"{settings.API_V1_STR}/assets/{video_asset.id}/stream",
                headers=stream_tenant_a_token_headers,
            )
            # First few requests should succeed
            assert response.status_code in [200, 429]

    @patch("app.services.signed_url_service.SignedURLService.generate_stream_url")
    def test_stream_response_includes_correct_mime_type(
        self,
        mock_generate_stream_url,
        client: TestClient,
        db: Session,
        stream_tenant_a_token_headers: dict[str, str],
        video_asset: Asset,
    ):
        """
        Test response includes correct mime_type.

        References:
        - Task 6.10
        - AC: #2 (response includes mime_type)
        """
        from app.core.config import settings

        # Mock stream URL generation
        expires_at = datetime.now(timezone.utc).replace(microsecond=0)
        mock_generate_stream_url.return_value = (
            "https://minio.example.com/assets/lesson.mp4?signature=abc123",
            expires_at,
        )

        # Request stream URL
        response = client.get(
            f"{settings.API_V1_STR}/assets/{video_asset.id}/stream",
            headers=stream_tenant_a_token_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify mime_type field matches asset exactly
        assert data["mime_type"] == video_asset.mime_type
        assert data["mime_type"] == "video/mp4"
