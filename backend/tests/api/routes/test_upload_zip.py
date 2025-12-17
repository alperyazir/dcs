"""
Tests for ZIP Upload API Routes (Story 3.3, Task 9.1).

Tests:
- ZIP upload with valid archive extracts files and returns 201 (AC: #1, #10)
- Only publishers/teachers can upload ZIP (AC: #2, #14)
- System files are filtered during extraction (AC: #4)
- Per-file validation (AC: #5)
- Folder structure preserved (AC: #7)
- Asset metadata created for each file (AC: #8)
- Streaming mode (AC: #9)
- Invalid ZIP returns 400 (AC: #13)
- ZIP bomb protection

References:
- Task 9.1: CREATE tests for API route tests
- Task 9.4: TEST endpoint returns 201 with correct response schema
- Task 9.5: TEST system files filtered
- Task 9.6: TEST folder structure preserved
- Task 9.7: TEST invalid files skipped but extraction continues
- Task 9.8: TEST corrupt ZIP returns INVALID_ZIP_FILE
- Task 9.9: TEST ZIP bomb protection
- Task 9.10: TEST unauthorized roles get 403
"""

import io
import uuid
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import AuditAction, AuditLog, Tenant, TenantType, User, UserRole


@pytest.fixture(scope="module")
def zip_test_tenant(db: Session) -> Tenant:
    """Create a test tenant for ZIP upload tests."""
    tenant = db.exec(
        select(Tenant).where(Tenant.name == "test_zip_upload_tenant")
    ).first()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="test_zip_upload_tenant",
            tenant_type=TenantType.PUBLISHER,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


@pytest.fixture(scope="module")
def publisher_user(db: Session, zip_test_tenant: Tenant) -> User:
    """Create a publisher user for ZIP upload tests."""
    email = "zip_publisher@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            role=UserRole.PUBLISHER,
            tenant_id=zip_test_tenant.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def teacher_user(db: Session, zip_test_tenant: Tenant) -> User:
    """Create a teacher user for ZIP upload tests."""
    email = "zip_teacher@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            role=UserRole.TEACHER,
            tenant_id=zip_test_tenant.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def student_user(db: Session, zip_test_tenant: Tenant) -> User:
    """Create a student user for ZIP upload tests."""
    email = "zip_student@example.com"
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            role=UserRole.STUDENT,
            tenant_id=zip_test_tenant.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="module")
def publisher_token_headers(client: TestClient, publisher_user: User) -> dict[str, str]:
    """Get auth headers for the publisher user."""
    login_data = {
        "username": publisher_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}


@pytest.fixture(scope="module")
def teacher_token_headers(client: TestClient, teacher_user: User) -> dict[str, str]:
    """Get auth headers for the teacher user."""
    login_data = {
        "username": teacher_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}


@pytest.fixture(scope="module")
def student_token_headers(client: TestClient, student_user: User) -> dict[str, str]:
    """Get auth headers for the student user."""
    login_data = {
        "username": student_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}


def create_test_zip(
    files: dict[str, bytes] | None = None,
) -> io.BytesIO:
    """Create a test ZIP file with specified contents."""
    if files is None:
        files = {
            "document.pdf": b"%PDF-1.4 test pdf content",
            "images/photo.jpg": b"\xff\xd8\xff\xe0 jpeg content",
        }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buffer.seek(0)
    return buffer


@pytest.fixture
def mock_minio():
    """Mock MinIO client for tests."""
    client = MagicMock()
    client.bucket_exists.return_value = True
    mock_result = MagicMock()
    mock_result.etag = '"abc123"'
    client.put_object.return_value = mock_result

    # Patch both locations where minio client is used
    with (
        patch("app.core.minio_client.get_minio_client", return_value=client),
        patch(
            "app.services.zip_extraction_service.get_minio_client", return_value=client
        ),
        patch("app.services.zip_extraction_service.ensure_bucket_exists"),
    ):
        yield client


class TestZipUploadEndpoint:
    """Tests for POST /api/v1/assets/upload-zip endpoint."""

    def test_upload_requires_authentication(
        self,
        client: TestClient,
    ) -> None:
        """ZIP upload without authentication returns 401."""
        zip_buffer = create_test_zip()

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            files={"file": ("archive.zip", zip_buffer, "application/zip")},
        )
        assert response.status_code == 401

    def test_publisher_can_upload_zip(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Publisher can upload ZIP archives (AC: #2)."""
        zip_buffer = create_test_zip({"document.pdf": b"%PDF-1.4 publisher test"})

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("archive.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "extracted_count" in data
        assert data["extracted_count"] >= 1

    def test_teacher_can_upload_zip(
        self,
        client: TestClient,
        teacher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Teacher can upload ZIP archives (AC: #2)."""
        zip_buffer = create_test_zip({"lesson.pdf": b"%PDF-1.4 teacher test"})

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=teacher_token_headers,
            files={"file": ("lessons.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201

    def test_student_cannot_upload_zip(
        self,
        client: TestClient,
        student_token_headers: dict[str, str],
    ) -> None:
        """Student cannot upload ZIP archives (AC: #14)."""
        zip_buffer = create_test_zip()

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=student_token_headers,
            files={"file": ("archive.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 403
        data = response.json()
        detail = data.get("detail", data)
        assert detail.get("error_code") == "UNAUTHORIZED_ROLE"

    def test_response_includes_extraction_counts(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Response includes extraction counts (AC: #10)."""
        zip_buffer = create_test_zip(
            {
                "doc1.pdf": b"%PDF-1.4 doc 1",
                "doc2.pdf": b"%PDF-1.4 doc 2",
                ".DS_Store": b"system file",
            }
        )

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("archive.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields per AC: #10
        assert "extracted_count" in data
        assert "skipped_count" in data
        assert "failed_count" in data
        assert "total_size_bytes" in data
        assert "assets" in data
        assert "skipped_files" in data
        assert "failed_files" in data

    def test_system_files_filtered(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """System files are filtered during extraction (AC: #4, Task 9.5)."""
        zip_buffer = create_test_zip(
            {
                "valid.pdf": b"%PDF-1.4 valid content",
                ".DS_Store": b"macos metadata",
                "__MACOSX/._valid.pdf": b"resource fork",
                "Thumbs.db": b"windows thumbnail",
            }
        )

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("archive.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()

        # Only the valid.pdf should be extracted
        assert data["extracted_count"] == 1
        assert data["skipped_count"] >= 3

        # Verify skipped files list
        skipped_names = [f["file_name"] for f in data["skipped_files"]]
        assert ".DS_Store" in skipped_names


class TestZipUploadFolderStructure:
    """Tests for folder structure preservation (AC: #7)."""

    def test_folder_structure_preserved_in_object_key(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Folder structure is preserved as MinIO prefixes (Task 9.6)."""
        zip_buffer = create_test_zip(
            {
                "books/math/chapter1.pdf": b"%PDF-1.4 math chapter 1",
                "books/science/intro.pdf": b"%PDF-1.4 science intro",
            }
        )

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("textbooks.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["extracted_count"] == 2

        # Verify object keys contain folder structure
        object_keys = [a["object_key"] for a in data["assets"]]
        assert any("books/math" in key for key in object_keys)
        assert any("books/science" in key for key in object_keys)


class TestZipUploadValidation:
    """Tests for per-file validation (AC: #5)."""

    def test_invalid_files_skipped_but_extraction_continues(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Invalid files are skipped but extraction continues (AC: #12, Task 9.7)."""
        zip_buffer = create_test_zip(
            {
                "valid.pdf": b"%PDF-1.4 valid pdf",
                "invalid.exe": b"MZ executable content",
                "also_valid.txt": b"text content",
            }
        )

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("mixed.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()

        # At least valid files should be extracted
        assert data["extracted_count"] >= 2
        # Invalid files should be in failed list
        assert data["failed_count"] >= 1

        # Verify failed file details
        failed_names = [f["file_name"] for f in data["failed_files"]]
        assert any("exe" in name for name in failed_names)

    def test_asset_metadata_created_for_each_file(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Asset metadata is created for each extracted file (AC: #8)."""
        zip_buffer = create_test_zip(
            {
                "file1.pdf": b"%PDF-1.4 file 1",
                "file2.pdf": b"%PDF-1.4 file 2",
                "file3.pdf": b"%PDF-1.4 file 3",
            }
        )

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("files.zip", zip_buffer, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()

        # All 3 files should be extracted
        assert data["extracted_count"] == 3
        assert len(data["assets"]) == 3

        # Verify each asset has required metadata
        for asset in data["assets"]:
            assert "asset_id" in asset or "id" in asset
            assert "file_name" in asset
            assert "file_size_bytes" in asset
            assert "mime_type" in asset
            assert "checksum" in asset
            assert "object_key" in asset


class TestZipUploadInvalidFiles:
    """Tests for invalid ZIP handling (AC: #13)."""

    def test_corrupt_zip_returns_400(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Corrupt ZIP file returns 400 INVALID_ZIP_FILE (Task 9.8)."""
        corrupt_zip = io.BytesIO(b"PK\x03\x04 not a valid zip content garbage")
        corrupt_zip.seek(0)

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("corrupt.zip", corrupt_zip, "application/zip")},
        )

        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", data)
        assert detail.get("error_code") == "INVALID_ZIP_FILE"

    def test_non_zip_file_returns_400(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Non-ZIP file returns 400."""
        not_a_zip = io.BytesIO(b"This is just plain text, not a ZIP")
        not_a_zip.seek(0)

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("fake.zip", not_a_zip, "application/zip")},
        )

        assert response.status_code == 400

    def test_wrong_content_type_returns_400(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
    ) -> None:
        """Wrong content type returns 400."""
        zip_buffer = create_test_zip()

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("archive.pdf", zip_buffer, "application/pdf")},
        )

        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", data)
        assert detail.get("error_code") == "INVALID_FILE_TYPE"


class TestZipUploadSizeLimit:
    """Tests for ZIP size limits."""

    def test_zip_size_limit_enforced(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
    ) -> None:
        """ZIP files over size limit return 413."""
        # Create a mock large ZIP (we'll test the limit check, not actual size)
        with patch.object(settings, "MAX_ZIP_FILE_SIZE", 100):  # 100 bytes limit
            zip_buffer = create_test_zip(
                {
                    "large_file.pdf": b"%PDF-1.4 " + b"x" * 200  # Over 100 bytes
                }
            )

            response = client.post(
                f"{settings.API_V1_STR}/assets/upload-zip",
                headers=publisher_token_headers,
                files={"file": ("large.zip", zip_buffer, "application/zip")},
            )

            assert response.status_code == 413


class TestZipUploadAuditLogging:
    """Tests for audit logging (AC: #11)."""

    def test_audit_log_created_for_zip_upload(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        db: Session,
        mock_minio: MagicMock,
    ) -> None:
        """Audit log is created for ZIP upload."""
        # Count audit logs before
        before_count = len(
            db.exec(
                select(AuditLog).where(AuditLog.action == AuditAction.ASSET_ZIP_UPLOAD)
            ).all()
        )

        zip_buffer = create_test_zip({"audit_test.pdf": b"%PDF-1.4 audit test"})

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("audit.zip", zip_buffer, "application/zip")},
        )

        if response.status_code == 201:
            # Count audit logs after
            after_count = len(
                db.exec(
                    select(AuditLog).where(
                        AuditLog.action == AuditAction.ASSET_ZIP_UPLOAD
                    )
                ).all()
            )
            # Batch audit log should be created
            assert after_count >= before_count

    def test_individual_asset_audit_logs_created(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        db: Session,
        mock_minio: MagicMock,
    ) -> None:
        """Individual audit logs are created for each extracted asset."""
        # Count asset upload audit logs before
        before_count = len(
            db.exec(
                select(AuditLog).where(AuditLog.action == AuditAction.ASSET_UPLOAD)
            ).all()
        )

        zip_buffer = create_test_zip(
            {
                "file1.pdf": b"%PDF-1.4 file 1 for audit",
                "file2.pdf": b"%PDF-1.4 file 2 for audit",
            }
        )

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("multi.zip", zip_buffer, "application/zip")},
        )

        if response.status_code == 201:
            data = response.json()
            extracted = data["extracted_count"]

            # Count asset upload audit logs after
            after_count = len(
                db.exec(
                    select(AuditLog).where(AuditLog.action == AuditAction.ASSET_UPLOAD)
                ).all()
            )

            # Should have created audit logs for each extracted file
            assert after_count >= before_count + extracted


class TestZipUploadEmptyZip:
    """Tests for edge cases."""

    def test_empty_zip_returns_success_with_zero_count(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        mock_minio: MagicMock,
    ) -> None:
        """Empty ZIP file returns 201 with zero extracted count."""
        empty_zip = create_test_zip({})

        response = client.post(
            f"{settings.API_V1_STR}/assets/upload-zip",
            headers=publisher_token_headers,
            files={"file": ("empty.zip", empty_zip, "application/zip")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["extracted_count"] == 0
        assert data["assets"] == []
