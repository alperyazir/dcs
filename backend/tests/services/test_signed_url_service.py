"""
Unit Tests for SignedURLService (Story 3.2, Task 8.2).

Tests service layer logic in isolation:
- Permission validation (_check_asset_access)
- Audit log creation (_create_audit_log)
- URL generation orchestration
- Tenant isolation enforcement

References:
- Task 8.2: CREATE `backend/tests/services/test_signed_url_service.py` for service tests
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.core.exceptions import AssetAccessDeniedError, AssetNotFoundError, UploadError
from app.models import Asset, AuditAction, TenantType, User, UserRole
from app.services.signed_url_service import SignedURLService


class TestCheckAssetAccess:
    """Tests for _check_asset_access permission validation (Task 7)."""

    def test_admin_can_access_any_asset(self) -> None:
        """Admin role bypasses all permission checks (Task 7.2)."""
        # Arrange
        admin_user = MagicMock(spec=User)
        admin_user.id = uuid.uuid4()
        admin_user.role = UserRole.ADMIN
        admin_user.tenant_id = uuid.uuid4()

        asset = MagicMock(spec=Asset)
        asset.id = uuid.uuid4()
        asset.user_id = uuid.uuid4()  # Different user
        asset.tenant_id = uuid.uuid4()  # Different tenant

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=admin_user)

        # Act & Assert - should not raise
        service._check_asset_access(asset)

    def test_supervisor_can_access_any_asset(self) -> None:
        """Supervisor role bypasses all permission checks (Task 7.2)."""
        # Arrange
        supervisor_user = MagicMock(spec=User)
        supervisor_user.id = uuid.uuid4()
        supervisor_user.role = UserRole.SUPERVISOR
        supervisor_user.tenant_id = uuid.uuid4()

        asset = MagicMock(spec=Asset)
        asset.id = uuid.uuid4()
        asset.user_id = uuid.uuid4()  # Different user
        asset.tenant_id = uuid.uuid4()  # Different tenant

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=supervisor_user)

        # Act & Assert - should not raise
        service._check_asset_access(asset)

    def test_owner_can_access_own_asset(self) -> None:
        """Asset owner can access their own assets (Task 7.1)."""
        # Arrange
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        owner_user = MagicMock(spec=User)
        owner_user.id = user_id
        owner_user.role = UserRole.PUBLISHER
        owner_user.tenant_id = tenant_id

        asset = MagicMock(spec=Asset)
        asset.id = uuid.uuid4()
        asset.user_id = user_id  # Same user
        asset.tenant_id = tenant_id  # Same tenant

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=owner_user)

        # Act & Assert - should not raise
        service._check_asset_access(asset)

    def test_cross_tenant_access_denied(self) -> None:
        """Cross-tenant access is denied (Task 7.3)."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.TEACHER
        user.tenant_id = uuid.uuid4()

        asset = MagicMock(spec=Asset)
        asset.id = uuid.uuid4()
        asset.user_id = uuid.uuid4()
        asset.tenant_id = uuid.uuid4()  # Different tenant!

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act & Assert
        with pytest.raises(AssetAccessDeniedError) as exc_info:
            service._check_asset_access(asset)

        assert "Cross-tenant access" in str(exc_info.value.detail)

    def test_non_owner_same_tenant_denied(self) -> None:
        """Non-owner in same tenant is denied (Task 7.1)."""
        # Arrange
        tenant_id = uuid.uuid4()

        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.STUDENT
        user.tenant_id = tenant_id

        asset = MagicMock(spec=Asset)
        asset.id = uuid.uuid4()
        asset.user_id = uuid.uuid4()  # Different user
        asset.tenant_id = tenant_id  # Same tenant

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act & Assert
        with pytest.raises(AssetAccessDeniedError) as exc_info:
            service._check_asset_access(asset)

        assert "do not have permission" in str(exc_info.value.detail)


class TestGenerateDownloadUrl:
    """Tests for generate_download_url method."""

    @patch("app.services.signed_url_service.generate_presigned_download_url")
    @patch("app.services.signed_url_service.AssetRepository")
    def test_returns_url_and_expiration(
        self, mock_repo_class: MagicMock, mock_generate_url: MagicMock
    ) -> None:
        """generate_download_url returns tuple of (url, expires_at)."""
        # Arrange
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        asset_id = uuid.uuid4()

        user = MagicMock(spec=User)
        user.id = user_id
        user.role = UserRole.PUBLISHER
        user.tenant_id = tenant_id

        asset = MagicMock(spec=Asset)
        asset.id = asset_id
        asset.user_id = user_id
        asset.tenant_id = tenant_id
        asset.bucket = "assets"
        asset.object_key = "publisher/tenant/asset/file.pdf"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = asset
        mock_repo_class.return_value = mock_repo

        expected_url = "http://minio:9000/assets/test?X-Amz-Algorithm=AWS4-HMAC-SHA256"
        expected_expires = datetime.now(timezone.utc)
        mock_generate_url.return_value = (expected_url, expected_expires)

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act
        url, expires_at = service.generate_download_url(asset_id)

        # Assert
        assert url == expected_url
        assert expires_at == expected_expires
        mock_generate_url.assert_called_once_with(
            bucket=asset.bucket,
            object_key=asset.object_key,
        )

    @patch("app.services.signed_url_service.AssetRepository")
    def test_raises_not_found_for_missing_asset(
        self, mock_repo_class: MagicMock
    ) -> None:
        """generate_download_url raises AssetNotFoundError for non-existent asset."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.PUBLISHER
        user.tenant_id = uuid.uuid4()

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None  # Asset not found
        mock_repo_class.return_value = mock_repo

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act & Assert
        fake_asset_id = uuid.uuid4()
        with pytest.raises(AssetNotFoundError):
            service.generate_download_url(fake_asset_id)


class TestGenerateUploadUrl:
    """Tests for generate_upload_url method."""

    @patch("app.services.signed_url_service.generate_presigned_upload_url")
    @patch("app.services.signed_url_service.generate_object_key")
    @patch("app.services.signed_url_service.get_safe_filename")
    def test_returns_url_and_metadata(
        self,
        mock_safe_filename: MagicMock,
        mock_generate_key: MagicMock,
        mock_generate_url: MagicMock,
    ) -> None:
        """generate_upload_url returns tuple of (url, expires_at, asset_id, object_key)."""
        # Arrange
        tenant_id = uuid.uuid4()

        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.PUBLISHER
        user.tenant_id = tenant_id
        user.tenant = MagicMock()
        user.tenant.tenant_type = TenantType.PUBLISHER

        mock_safe_filename.return_value = "safe_file.pdf"
        mock_generate_key.return_value = f"publisher/{tenant_id}/asset-id/safe_file.pdf"

        expected_url = (
            "http://minio:9000/assets/upload?X-Amz-Algorithm=AWS4-HMAC-SHA256"
        )
        expected_expires = datetime.now(timezone.utc)
        mock_generate_url.return_value = (expected_url, expected_expires)

        session = MagicMock(spec=Session)
        session.add = MagicMock()
        session.commit = MagicMock()

        service = SignedURLService(session=session, current_user=user)

        # Act
        url, expires_at, asset_id, object_key = service.generate_upload_url(
            file_name="test.pdf",
            mime_type="application/pdf",
            file_size=1024,
        )

        # Assert
        assert url == expected_url
        assert expires_at == expected_expires
        assert asset_id is not None
        assert object_key is not None

    def test_raises_error_if_no_tenant(self) -> None:
        """generate_upload_url raises UploadError if user has no tenant."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.PUBLISHER
        user.tenant_id = None  # No tenant!

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act & Assert
        with pytest.raises(UploadError) as exc_info:
            service.generate_upload_url(
                file_name="test.pdf",
                mime_type="application/pdf",
                file_size=1024,
            )

        assert "no tenant assigned" in str(exc_info.value.detail).lower()


class TestGetTenantType:
    """Tests for _get_tenant_type helper method."""

    def test_returns_tenant_type_from_tenant(self) -> None:
        """Returns tenant type from user's tenant if available."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        user.tenant = MagicMock()
        user.tenant.tenant_type = TenantType.SCHOOL
        user.role = UserRole.TEACHER

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act
        result = service._get_tenant_type()

        # Assert
        assert result == "school"

    def test_fallback_to_role_if_no_tenant(self) -> None:
        """Falls back to user role if tenant not loaded."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        user.tenant = None  # Not loaded
        user.role = UserRole.TEACHER

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act
        result = service._get_tenant_type()

        # Assert
        assert result == "teacher"

    def test_defaults_to_publisher_for_admin(self) -> None:
        """Defaults to 'publisher' for admin role."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        user.tenant = None
        user.role = UserRole.ADMIN

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act
        result = service._get_tenant_type()

        # Assert
        assert result == "publisher"


class TestAuditLogCreation:
    """Tests for _create_audit_log method."""

    def test_creates_audit_log_entry(self) -> None:
        """_create_audit_log adds entry to session."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()

        session = MagicMock(spec=Session)
        service = SignedURLService(
            session=session,
            current_user=user,
            ip_address="192.168.1.1",
        )

        asset_id = uuid.uuid4()

        # Act
        service._create_audit_log(
            asset_id=asset_id,
            action=AuditAction.SIGNED_URL_DOWNLOAD,
            metadata={"url_type": "download"},
        )

        # Assert
        session.add.assert_called_once()
        session.commit.assert_called_once()

        # Verify the audit log was created with correct values
        audit_log = session.add.call_args[0][0]
        assert audit_log.user_id == user.id
        assert audit_log.asset_id == asset_id
        assert audit_log.action == AuditAction.SIGNED_URL_DOWNLOAD
        assert audit_log.ip_address == "192.168.1.1"

    def test_does_not_fail_on_audit_error(self) -> None:
        """_create_audit_log catches exceptions and logs error."""
        # Arrange
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()

        session = MagicMock(spec=Session)
        session.commit.side_effect = Exception("DB error")

        service = SignedURLService(session=session, current_user=user)

        # Act - should not raise
        service._create_audit_log(
            asset_id=uuid.uuid4(),
            action=AuditAction.SIGNED_URL_DOWNLOAD,
        )

        # Assert - session.add was still called
        session.add.assert_called_once()


class TestUrlGenerationPerformance:
    """Performance tests for URL generation (AC: #4, Task 8.8)."""

    @patch("app.services.signed_url_service.generate_presigned_download_url")
    @patch("app.services.signed_url_service.AssetRepository")
    def test_download_url_generation_under_100ms(
        self, mock_repo_class: MagicMock, mock_generate_url: MagicMock
    ) -> None:
        """URL generation should complete in under 100ms (AC: #4)."""
        import time

        # Arrange
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        user = MagicMock(spec=User)
        user.id = user_id
        user.role = UserRole.PUBLISHER
        user.tenant_id = tenant_id

        asset = MagicMock(spec=Asset)
        asset.id = uuid.uuid4()
        asset.user_id = user_id
        asset.tenant_id = tenant_id
        asset.bucket = "assets"
        asset.object_key = "test/path"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = asset
        mock_repo_class.return_value = mock_repo

        mock_generate_url.return_value = ("http://url", datetime.now(timezone.utc))

        session = MagicMock(spec=Session)
        service = SignedURLService(session=session, current_user=user)

        # Act
        start_time = time.time()
        service.generate_download_url(asset.id)
        duration_ms = (time.time() - start_time) * 1000

        # Assert - should complete in under 100ms
        assert (
            duration_ms < 100
        ), f"URL generation took {duration_ms:.2f}ms, expected < 100ms"
