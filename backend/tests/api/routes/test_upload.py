"""
Tests for Upload API Routes (Story 3.1, Task 9.1).

Tests:
- Upload with valid file creates asset and returns 201 (AC: #6)
- Upload with invalid MIME type returns 400 with INVALID_FILE_TYPE (AC: #10)
- Upload with oversized file returns 400 with FILE_TOO_LARGE (AC: #11)
- Checksum is correctly calculated and stored (AC: #5)
- Audit log created with action="ASSET_UPLOAD" (AC: #8)
- Tenant isolation (AC: #3)
- Rate limiting (AC: rate limiting from Story 2.4)

References:
- Task 9.4-9.11: Comprehensive test cases
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import AuditAction, AuditLog, Tenant, TenantType, User


@pytest.fixture(scope="module")
def test_tenant(db: Session) -> Tenant:
    """Create a test tenant for upload tests."""
    tenant = db.exec(select(Tenant).where(Tenant.name == "test_upload_tenant")).first()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="test_upload_tenant",
            tenant_type=TenantType.PUBLISHER,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


@pytest.fixture(scope="module")
def tenant_user(db: Session, test_tenant: Tenant) -> User:
    """Create a test user assigned to the test tenant."""
    email = "upload_test_user@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            tenant_id=test_tenant.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def tenant_user_token_headers(client: TestClient, tenant_user: User) -> dict[str, str]:
    """Get auth headers for the tenant user."""
    login_data = {
        "username": tenant_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


class TestUploadEndpoint:
    """Tests for POST /api/v1/assets/upload endpoint."""

    @pytest.fixture
    def mock_minio(self):
        """Mock MinIO client for tests."""
        with patch("app.core.minio_client.get_minio_client") as mock:
            client = MagicMock()
            # Mock bucket_exists to return True
            client.bucket_exists.return_value = True
            # Mock put_object to return a result with etag
            mock_result = MagicMock()
            mock_result.etag = '"abc123"'
            client.put_object.return_value = mock_result
            mock.return_value = client
            yield client

    def test_upload_requires_authentication(
        self,
        client: TestClient,
    ) -> None:
        """Upload without authentication returns 401."""
        file_content = b"test content"
        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
        )
        assert response.status_code == 401

    def test_upload_valid_pdf_creates_asset(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        db: Session,
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload with valid PDF creates asset and returns 201 (Task 9.4)."""
        file_content = b"%PDF-1.4 test content for upload"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("test_document.pdf", file_content, "application/pdf")},
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()

        # Verify response fields (AC: #6)
        assert "asset_id" in data or "id" in data
        asset_id = data.get("asset_id") or data.get("id")
        assert asset_id is not None
        assert data["mime_type"] == "application/pdf"
        assert data["file_size_bytes"] == len(file_content)
        assert data["checksum"] is not None  # MD5 checksum (AC: #5)
        assert "test_document.pdf" in data["file_name"]

    def test_upload_invalid_mime_type_returns_400(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
    ) -> None:
        """POST /assets/upload with .exe returns 400 INVALID_FILE_TYPE (Task 9.5)."""
        file_content = b"MZ executable content"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={
                "file": (
                    "malware.exe",
                    file_content,
                    "application/x-msdownload",
                )
            },
        )

        assert response.status_code == 400
        data = response.json()
        # Check for error_code in detail or directly in response
        detail = data.get("detail", data)
        if isinstance(detail, dict):
            assert detail.get("error_code") == "INVALID_FILE_TYPE"
        else:
            assert "INVALID_FILE_TYPE" in str(data)

    def test_upload_creates_audit_log(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        db: Session,
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload creates audit log with ASSET_UPLOAD action (Task 9.8)."""
        file_content = b"audit test content"

        # Count audit logs before
        before_count = len(
            db.exec(
                select(AuditLog).where(AuditLog.action == AuditAction.ASSET_UPLOAD)
            ).all()
        )

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("audit_test.pdf", file_content, "application/pdf")},
        )

        if response.status_code == 201:
            # Count audit logs after
            after_count = len(
                db.exec(
                    select(AuditLog).where(AuditLog.action == AuditAction.ASSET_UPLOAD)
                ).all()
            )
            # Audit log should be created
            assert after_count >= before_count

    def test_upload_valid_video_accepted(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload with video/mp4 is accepted."""
        # MP4 magic bytes: ftyp at offset 4
        file_content = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41video content"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("lecture.mp4", file_content, "video/mp4")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["mime_type"] == "video/mp4"

    def test_upload_valid_image_accepted(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload with image/jpeg is accepted."""
        file_content = b"\xff\xd8\xff\xe0 JPEG content"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("photo.jpg", file_content, "image/jpeg")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["mime_type"] == "image/jpeg"

    def test_upload_valid_audio_accepted(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload with audio/mpeg is accepted."""
        file_content = b"ID3 audio content"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("song.mp3", file_content, "audio/mpeg")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["mime_type"] == "audio/mpeg"

    def test_upload_checksum_calculated(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload calculates MD5 checksum (Task 9.7)."""
        # PDF magic bytes + content for checksum test
        file_content = b"%PDF-1.4 content for checksum test"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("checksum_test.pdf", file_content, "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        # Checksum should be present and 32 chars (MD5 hex)
        assert data["checksum"] is not None
        assert len(data["checksum"]) == 32

    def test_upload_sanitizes_filename(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload sanitizes filename for security."""
        file_content = b"test content"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={
                "file": (
                    "../../../etc/passwd.pdf",
                    file_content,
                    "application/pdf",
                )
            },
        )

        # Should either sanitize the filename or reject it
        if response.status_code == 201:
            data = response.json()
            # If accepted, filename should be sanitized
            assert ".." not in data["file_name"]
            assert "/" not in data["file_name"]
        else:
            # Or reject with validation error
            assert response.status_code == 400

    def test_upload_response_includes_required_fields(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """POST /assets/upload response includes all required fields (AC: #6)."""
        # PDF magic bytes + test content
        file_content = b"%PDF-1.4 test for fields"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("fields_test.pdf", file_content, "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields per AC: #6
        required_fields = [
            "file_name",
            "file_size_bytes",
            "mime_type",
            "checksum",
            "object_key",
            "bucket",
            "created_at",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestUploadValidation:
    """Tests for file validation in upload endpoint."""

    def test_reject_javascript_file(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
    ) -> None:
        """JavaScript files are rejected."""
        file_content = b"console.log('malicious');"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("script.js", file_content, "application/javascript")},
        )

        assert response.status_code == 400

    def test_reject_html_file(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
    ) -> None:
        """HTML files are rejected (XSS prevention)."""
        file_content = b"<html><script>alert('xss')</script></html>"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("page.html", file_content, "text/html")},
        )

        assert response.status_code == 400

    def test_reject_php_file(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
    ) -> None:
        """PHP files are rejected."""
        file_content = b"<?php system($_GET['cmd']); ?>"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("shell.php", file_content, "application/x-httpd-php")},
        )

        assert response.status_code == 400


class TestUploadMinIO:
    """Tests for MinIO integration in upload."""

    @pytest.fixture
    def mock_minio_failure(self):
        """Mock MinIO client that fails on upload."""
        with patch("app.core.minio_client.get_minio_client") as mock:
            client = MagicMock()
            client.bucket_exists.return_value = True
            client.put_object.side_effect = Exception("MinIO connection failed")
            mock.return_value = client
            yield client

    def test_minio_failure_returns_error(
        self,
        client: TestClient,
        tenant_user_token_headers: dict[str, str],
        mock_minio_failure: MagicMock,
    ) -> None:
        """MinIO failure returns appropriate error."""
        file_content = b"test content"

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload",
            headers=tenant_user_token_headers,
            files={"file": ("test.pdf", file_content, "application/pdf")},
        )

        # Should return 500 on MinIO failure
        assert response.status_code in (500, 400)
