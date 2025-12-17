"""
Tests for Asset Service (Story 3.1, Task 9.2).

Unit tests for AssetService class:
- File validation integration
- MinIO upload orchestration
- Metadata creation
- Audit logging
- Transactional consistency (rollback on failure)

References:
- AC: #3 (upload to MinIO)
- AC: #4 (create metadata in PostgreSQL)
- AC: #5 (checksum calculation)
- AC: #8 (audit logging)
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from app.core.exceptions import (
    InvalidFilenameError,
    InvalidFileTypeError,
    UploadError,
)
from app.models import Tenant, TenantType, User, UserRole
from app.services.asset_service import AssetService


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def mock_user():
    """Create a mock user with tenant."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="test_tenant",
        tenant_type=TenantType.PUBLISHER,
    )
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        role=UserRole.PUBLISHER,
        tenant_id=tenant.id,
    )
    user.tenant = tenant
    return user


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile with PDF content."""

    async def create_upload_file(
        content: bytes = b"%PDF-1.4 test content",
        filename: str = "test.pdf",
        content_type: str = "application/pdf",
    ):
        file = MagicMock(spec=UploadFile)
        file.filename = filename
        file.content_type = content_type
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        return file

    return create_upload_file


class TestAssetServiceInit:
    """Tests for AssetService initialization."""

    def test_init_with_valid_params(self, mock_session, mock_user):
        """AssetService initializes with session and user."""
        service = AssetService(session=mock_session, current_user=mock_user)
        assert service.session == mock_session
        assert service.current_user == mock_user

    def test_get_tenant_type_from_tenant(self, mock_session, mock_user):
        """Tenant type is derived from user's tenant."""
        service = AssetService(session=mock_session, current_user=mock_user)
        assert service._get_tenant_type() == "publisher"


class TestAssetServiceValidation:
    """Tests for file validation in AssetService."""

    @pytest.mark.asyncio
    async def test_invalid_mime_type_raises_error(
        self, mock_session, mock_user, mock_upload_file
    ):
        """Invalid MIME type raises InvalidFileTypeError."""
        file = await mock_upload_file(
            content=b"MZ executable",
            filename="malware.exe",
            content_type="application/x-msdownload",
        )

        service = AssetService(session=mock_session, current_user=mock_user)

        with pytest.raises(InvalidFileTypeError) as exc_info:
            await service.create_asset(file=file, ip_address="127.0.0.1")

        assert "application/x-msdownload" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_filename_raises_error(
        self, mock_session, mock_user, mock_upload_file
    ):
        """Path traversal in filename raises InvalidFilenameError."""
        file = await mock_upload_file(
            content=b"%PDF-1.4 content",
            filename="../../../etc/passwd",
            content_type="application/pdf",
        )

        service = AssetService(session=mock_session, current_user=mock_user)

        with pytest.raises(InvalidFilenameError):
            await service.create_asset(file=file, ip_address="127.0.0.1")

    @pytest.mark.asyncio
    async def test_magic_bytes_mismatch_raises_error(
        self, mock_session, mock_user, mock_upload_file
    ):
        """File with wrong magic bytes raises InvalidFileTypeError."""
        # EXE content claimed as PDF
        file = await mock_upload_file(
            content=b"MZ\x90\x00 executable content",
            filename="document.pdf",
            content_type="application/pdf",
        )

        service = AssetService(session=mock_session, current_user=mock_user)

        with pytest.raises(InvalidFileTypeError):
            await service.create_asset(file=file, ip_address="127.0.0.1")


class TestAssetServiceUpload:
    """Tests for MinIO upload functionality."""

    @pytest.mark.asyncio
    async def test_successful_upload_creates_asset(
        self, mock_session, mock_user, mock_upload_file
    ):
        """Successful upload creates asset with all required fields."""
        file = await mock_upload_file()

        with patch("app.services.asset_service.ensure_bucket_exists"), patch(
            "app.services.asset_service.put_object_streaming"
        ) as mock_upload, patch(
            "app.services.asset_service.AssetRepository"
        ) as mock_repo_class:
            # Mock MinIO upload
            mock_upload.return_value = ('"etag123"', "abc123checksum")

            # Mock repository
            mock_repo = MagicMock()
            mock_asset = MagicMock()
            mock_asset.id = uuid.uuid4()
            mock_asset.file_name = "test.pdf"
            mock_asset.file_size_bytes = 21
            mock_asset.mime_type = "application/pdf"
            mock_asset.checksum = "abc123checksum"
            mock_asset.object_key = "publisher/tenant-id/asset-id/test.pdf"
            mock_asset.bucket = "assets"
            mock_asset.tenant_id = mock_user.tenant_id
            mock_asset.user_id = mock_user.id
            mock_repo.create.return_value = mock_asset
            mock_repo_class.return_value = mock_repo

            service = AssetService(session=mock_session, current_user=mock_user)
            result = await service.create_asset(file=file, ip_address="127.0.0.1")

            # Verify asset was created
            assert result is not None
            mock_upload.assert_called_once()
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_minio_failure_raises_upload_error(
        self, mock_session, mock_user, mock_upload_file
    ):
        """MinIO upload failure raises UploadError."""
        file = await mock_upload_file()

        with patch("app.services.asset_service.ensure_bucket_exists"), patch(
            "app.services.asset_service.put_object_streaming"
        ) as mock_upload:
            mock_upload.side_effect = Exception("MinIO connection failed")

            service = AssetService(session=mock_session, current_user=mock_user)

            with pytest.raises(UploadError) as exc_info:
                await service.create_asset(file=file, ip_address="127.0.0.1")

            assert "Failed to upload file to storage" in str(exc_info.value.detail)


class TestAssetServiceRollback:
    """Tests for transactional consistency and rollback."""

    @pytest.mark.asyncio
    async def test_metadata_failure_rolls_back_minio(
        self, mock_session, mock_user, mock_upload_file
    ):
        """If metadata creation fails, MinIO upload is rolled back."""
        file = await mock_upload_file()

        with patch("app.services.asset_service.ensure_bucket_exists"), patch(
            "app.services.asset_service.put_object_streaming"
        ) as mock_upload, patch(
            "app.services.asset_service.delete_object"
        ) as mock_delete, patch(
            "app.services.asset_service.AssetRepository"
        ) as mock_repo_class:
            # MinIO upload succeeds
            mock_upload.return_value = ('"etag123"', "abc123checksum")

            # Repository create fails
            mock_repo = MagicMock()
            mock_repo.create.side_effect = Exception("Database error")
            mock_repo_class.return_value = mock_repo

            service = AssetService(session=mock_session, current_user=mock_user)

            with pytest.raises(UploadError):
                await service.create_asset(file=file, ip_address="127.0.0.1")

            # Verify MinIO object was deleted (rollback)
            mock_delete.assert_called_once()


class TestAssetServiceAudit:
    """Tests for audit logging in AssetService."""

    @pytest.mark.asyncio
    async def test_successful_upload_creates_audit_log(
        self, mock_session, mock_user, mock_upload_file
    ):
        """Successful upload creates audit log entry."""
        file = await mock_upload_file()

        with patch("app.services.asset_service.ensure_bucket_exists"), patch(
            "app.services.asset_service.put_object_streaming"
        ) as mock_upload, patch(
            "app.services.asset_service.AssetRepository"
        ) as mock_repo_class:
            mock_upload.return_value = ('"etag123"', "abc123checksum")

            mock_repo = MagicMock()
            mock_asset = MagicMock()
            mock_asset.id = uuid.uuid4()
            mock_asset.file_name = "test.pdf"
            mock_asset.file_size_bytes = 21
            mock_asset.mime_type = "application/pdf"
            mock_asset.checksum = "abc123checksum"
            mock_asset.object_key = "publisher/tenant-id/asset-id/test.pdf"
            mock_asset.bucket = "assets"
            mock_asset.tenant_id = mock_user.tenant_id
            mock_asset.user_id = mock_user.id
            mock_repo.create.return_value = mock_asset
            mock_repo_class.return_value = mock_repo

            service = AssetService(session=mock_session, current_user=mock_user)
            await service.create_asset(file=file, ip_address="127.0.0.1")

            # Verify session.add was called (for audit log)
            # The service adds both asset and audit log
            assert mock_session.add.call_count >= 1
            assert mock_session.commit.call_count >= 1


class TestAssetServiceTenantIsolation:
    """Tests for tenant isolation in uploads."""

    @pytest.mark.asyncio
    async def test_user_without_tenant_raises_error(
        self, mock_session, mock_upload_file
    ):
        """User without tenant_id cannot upload."""
        user = User(
            id=uuid.uuid4(),
            email="no_tenant@example.com",
            hashed_password="hashed",
            is_active=True,
            role=UserRole.STUDENT,
            tenant_id=None,  # No tenant
        )
        user.tenant = None

        file = await mock_upload_file()

        service = AssetService(session=mock_session, current_user=user)

        with pytest.raises(UploadError) as exc_info:
            await service.create_asset(file=file, ip_address="127.0.0.1")

        assert "no tenant assigned" in str(exc_info.value.detail).lower()

    def test_object_key_includes_tenant_info(self, mock_session, mock_user):
        """Generated object key includes tenant type and ID."""
        from app.core.minio_client import generate_object_key

        tenant_type = "publisher"
        tenant_id = uuid.uuid4()
        asset_id = uuid.uuid4()
        filename = "test.pdf"

        object_key = generate_object_key(tenant_type, tenant_id, asset_id, filename)

        assert tenant_type in object_key
        assert str(tenant_id) in object_key
        assert str(asset_id) in object_key
        assert filename in object_key
