# Story 3.1: Implement Single File Upload with Progress Tracking

Status: in-progress

## Story

As a user,
I want to upload a single file to my storage area with progress feedback,
So that I can store my digital assets (FR1).

## Acceptance Criteria

1. **Given** I am authenticated and have write access to my storage area, **When** I send POST `/api/v1/assets/upload` with file data, **Then** the API validates file type and size before accepting (FR9: max 10GB per NFR-P3)

2. **Given** file validation passes, **When** the file is uploaded, **Then** allowed MIME types are validated against a configurable whitelist

3. **Given** validation succeeds, **When** upload completes, **Then** the file is uploaded directly to MinIO bucket with path `/{tenant_type}/{tenant_id}/{file_name}`

4. **Given** upload completes, **When** asset metadata is created, **Then** PostgreSQL stores: user_id, tenant_id, bucket, object_key, file_name, file_size_bytes, mime_type, checksum, created_at

5. **Given** file is uploaded, **When** checksum is calculated, **Then** checksum (MD5) is calculated and stored for integrity verification (FR60, NFR-R5)

6. **Given** upload succeeds, **When** response is returned, **Then** I receive 201 Created with asset metadata including asset_id and upload confirmation

7. **Given** large files are being uploaded, **When** upload is in progress, **Then** the upload does not buffer the entire file in memory (streaming design, NFR-P7)

8. **Given** upload completes, **When** audit logging occurs, **Then** an audit log entry is created with action="upload", user_id, asset_id, timestamp (FR53)

9. **Given** upload is successful, **When** the file is requested, **Then** the file is immediately accessible via download API

10. **Given** file validation fails, **When** invalid file type is detected, **Then** upload is rejected with 400 Bad Request and error_code "INVALID_FILE_TYPE"

11. **Given** file validation fails, **When** file size exceeds limits, **Then** upload is rejected with 400 Bad Request and error_code "FILE_TOO_LARGE"

## Tasks / Subtasks

- [ ] Task 1: Create Asset Model and Database Schema (AC: #4)
  - [ ] 1.1 CREATE `backend/app/models/asset.py` with Asset SQLModel class: id (UUID), user_id (FK), tenant_id (FK), bucket, object_key, file_name, file_size_bytes, mime_type, checksum, is_deleted, created_at, updated_at
  - [ ] 1.2 ADD Asset model to `backend/app/models.py` exports
  - [ ] 1.3 CREATE Alembic migration for assets table with indexes on tenant_id, user_id, created_at
  - [ ] 1.4 ADD row-level security policy for tenant isolation (following RLS pattern from Story 2.3)
  - [ ] 1.5 TEST migration applies cleanly with `alembic upgrade head`

- [ ] Task 2: Implement MinIO Service for Upload Operations (AC: #3, #7)
  - [ ] 2.1 UPDATE `backend/app/core/minio_client.py` to add `put_object_streaming()` method using MinIO SDK
  - [ ] 2.2 IMPLEMENT streaming upload that doesn't buffer entire file in memory
  - [ ] 2.3 ADD `generate_object_key()` function to create path `/{tenant_type}/{tenant_id}/{file_name}`
  - [ ] 2.4 ADD `calculate_checksum()` function for MD5 hash during streaming (NFR-R5)
  - [ ] 2.5 CONFIGURE MinIO bucket policies for prefix-based access control
  - [ ] 2.6 TEST MinIO connectivity and upload operations work correctly

- [ ] Task 3: Create File Validation Service (AC: #1, #2, #10, #11)
  - [ ] 3.1 CREATE `backend/app/services/file_validation_service.py` with validation logic
  - [ ] 3.2 IMPLEMENT `validate_mime_type()` with configurable whitelist from settings
  - [ ] 3.3 IMPLEMENT `validate_file_size()` with type-specific limits (videos: 10GB, images: 500MB, other: 5GB)
  - [ ] 3.4 ADD MIME type whitelist to `backend/app/core/config.py`: application/pdf, video/mp4, video/webm, audio/mp3, audio/wav, audio/mpeg, image/jpeg, image/png, image/gif, application/zip, application/json
  - [ ] 3.5 IMPLEMENT `get_safe_filename()` to sanitize uploaded filenames
  - [ ] 3.6 TEST validation rejects invalid types with error_code "INVALID_FILE_TYPE"
  - [ ] 3.7 TEST validation rejects oversized files with error_code "FILE_TOO_LARGE"

- [ ] Task 4: Implement Asset Service with Upload Logic (AC: #4, #5, #8)
  - [ ] 4.1 CREATE `backend/app/services/asset_service.py` with AssetService class
  - [ ] 4.2 IMPLEMENT `create_asset()` method that orchestrates: validate → upload to MinIO → create metadata → audit log
  - [ ] 4.3 ADD checksum calculation during upload (MD5 hash of file content)
  - [ ] 4.4 ADD audit logging via existing `audit_service.create_audit_log()` with action="ASSET_UPLOAD"
  - [ ] 4.5 ADD new AuditAction enum value "ASSET_UPLOAD" to `backend/app/models.py`
  - [ ] 4.6 ENSURE transactional consistency: rollback MinIO upload if metadata creation fails
  - [ ] 4.7 TEST asset creation workflow end-to-end

- [ ] Task 5: Create Asset Repository (AC: #4, #9)
  - [ ] 5.1 CREATE `backend/app/repositories/asset_repository.py` extending BaseRepository
  - [ ] 5.2 IMPLEMENT `create()` method with tenant_id enforcement
  - [ ] 5.3 IMPLEMENT `get_by_id()` with tenant isolation and permission checks
  - [ ] 5.4 IMPLEMENT `get_by_object_key()` for MinIO object lookup
  - [ ] 5.5 ADD proper indexing queries for tenant + user filtering
  - [ ] 5.6 TEST repository operations with tenant isolation

- [ ] Task 6: Create Upload API Endpoint (AC: #1, #6, #9)
  - [ ] 6.1 CREATE `backend/app/api/routes/upload.py` with upload router
  - [ ] 6.2 IMPLEMENT POST `/api/v1/assets/upload` endpoint using FastAPI UploadFile
  - [ ] 6.3 ADD request dependency for `CurrentUser` and tenant context
  - [ ] 6.4 ADD rate limiting using `@limiter.limit(get_dynamic_rate_limit)` (from Story 2.4)
  - [ ] 6.5 RETURN 201 Created with AssetResponse schema on success
  - [ ] 6.6 ADD endpoint to API router in `backend/app/api/main.py`
  - [ ] 6.7 TEST endpoint returns 201 with asset metadata

- [ ] Task 7: Create Request/Response Schemas (AC: #6)
  - [ ] 7.1 CREATE `backend/app/schemas/asset.py` with AssetCreate, AssetResponse, AssetPublic schemas
  - [ ] 7.2 ENSURE AssetResponse includes: asset_id, file_name, file_size_bytes, mime_type, checksum, object_key, created_at
  - [ ] 7.3 ADD validation for file_name (no path traversal, max length)
  - [ ] 7.4 CREATE `backend/app/schemas/upload.py` with UploadResponse schema
  - [ ] 7.5 TEST schema validation for edge cases

- [ ] Task 8: Implement Error Handling (AC: #10, #11)
  - [ ] 8.1 CREATE custom exceptions in `backend/app/core/exceptions.py`: InvalidFileTypeError, FileTooLargeError
  - [ ] 8.2 ADD exception handlers in `backend/app/main.py` for upload-specific errors
  - [ ] 8.3 ENSURE error responses follow standard format: {error_code, message, details, request_id, timestamp}
  - [ ] 8.4 TEST error responses include request_id from middleware

- [ ] Task 9: Write Comprehensive Tests (AC: #1-#11)
  - [ ] 9.1 CREATE `backend/tests/api/routes/test_upload.py` for upload endpoint tests
  - [ ] 9.2 CREATE `backend/tests/services/test_asset_service.py` for service tests
  - [ ] 9.3 CREATE `backend/tests/services/test_file_validation_service.py` for validation tests
  - [ ] 9.4 TEST upload with valid file creates asset and returns 201
  - [ ] 9.5 TEST upload with invalid MIME type returns 400 with INVALID_FILE_TYPE
  - [ ] 9.6 TEST upload with oversized file returns 400 with FILE_TOO_LARGE
  - [ ] 9.7 TEST checksum is correctly calculated and stored
  - [ ] 9.8 TEST audit log created with action="ASSET_UPLOAD"
  - [ ] 9.9 TEST tenant isolation: users can only upload to their tenant storage
  - [ ] 9.10 TEST uploaded file is accessible via download API
  - [ ] 9.11 TEST rate limiting applies correctly per user role

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**MinIO Object Storage Integration:**
- SDK Version: `minio` 7.2.x (already in pyproject.toml)
- Bucket Strategy: Single `assets` bucket with tenant-specific prefixes
- Path Structure: `/{tenant_type}/{tenant_id}/{file_name}`
- Streaming Design: NFR-P7 requires no full file buffering in memory

**Multi-Tenant Data Isolation:**
- All tenant-specific tables include `tenant_id` column
- PostgreSQL RLS policies enforce isolation
- Middleware injects user context into database queries

**Error Handling Standards:**
```json
{
  "error_code": "INVALID_FILE_TYPE",
  "message": "File type 'application/exe' is not allowed. Supported types: pdf, mp4, mp3, jpg, png, zip",
  "details": {"mime_type": "application/exe", "allowed_types": ["application/pdf", "video/mp4", ...]},
  "request_id": "uuid-v4-request-id",
  "timestamp": "2025-12-17T10:30:00Z"
}
```

**Audit Logging:**
- Decision: Immutable append-only audit table in PostgreSQL
- Logged Events: All CRUD operations on assets
- Schema: Already exists from Epic 2 with `audit_log(id, timestamp, user_id, action, resource_type, resource_id, metadata_json)`

### Existing Code Assets (REUSE from Epic 2)

**`backend/app/api/deps_auth.py`** - Authorization dependencies:
```python
require_admin(current_user: User) -> User
require_supervisor_or_above(current_user: User) -> User
require_role_or_above(minimum_role: UserRole) -> User
CurrentUser = Annotated[User, Depends(get_current_user)]
```

**`backend/app/middleware/rate_limit.py`** - Rate limiting:
```python
get_dynamic_rate_limit(request: Request) -> str | None
# Publishers: 1000 req/hour, Teachers: 500 req/hour, Students: 100 req/hour
# Admin/Supervisor: Unlimited (returns None)
```

**`backend/app/middleware/tenant_context.py`** - Tenant context injection:
```python
TenantContextMiddleware  # Extracts tenant_id from JWT, sets in request.state
```

**`backend/app/services/audit_service.py`** - Audit logging:
```python
create_audit_log(session, user_id, action, ip_address, metadata_json) -> AuditLog
```

**`backend/app/core/minio_client.py`** - MinIO client (needs extension):
```python
# Current implementation for health checks
# EXTEND with upload operations
```

**`backend/app/models.py`** - Existing models:
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    PUBLISHER = "publisher"
    SCHOOL = "school"
    TEACHER = "teacher"
    STUDENT = "student"

class AuditAction(str, Enum):
    # Existing actions from Epic 2
    # ADD: ASSET_UPLOAD for this story
```

**`backend/app/repositories/base.py`** - Base repository with tenant filtering:
```python
class BaseRepository:
    # Provides tenant_id filtering foundation
    # EXTEND for asset operations
```

### Previous Story Intelligence (Epic 2)

**Patterns Established:**
- Rate limiting applied to all endpoints via `@limiter.limit(get_dynamic_rate_limit)`
- Request object required for rate limiter: `request: Request`
- Admin/Supervisor get unlimited API access
- All routes use `CurrentUser` dependency for authentication
- Audit logging with metadata_json for detailed tracking
- Error responses include request_id from middleware
- Use `require_supervisor_or_above` for admin-level endpoints

**Key Files from Epic 2:**
- `backend/app/middleware/rate_limit.py` - Role-based rate limiting
- `backend/app/middleware/tenant_context.py` - JWT claims extraction
- `backend/app/api/deps.py` - CurrentUser dependency
- `backend/app/core/security.py` - JWT token handling
- `backend/app/services/audit_service.py` - Audit logging service
- `backend/app/main.py` - HTTP exception handler for structured errors

**Learnings from Previous Stories:**
- Rate limiting decorator must come AFTER route decorator
- Follow existing error response format with request_id
- Use structured JSON logging for audit/security events
- Audit log only created when actual operations succeed
- Tenant isolation must be enforced at both API and database layers

### Git Intelligence (Recent Commits)

Recent commits show established patterns:
- `feat(story-2.5)`: User management with audit logging
- `feat: Stories 2.3 & 2.4`: Multi-tenant RLS + Rate Limiting
- Commit format: `feat(story-X.Y): Description`
- Branch format: `story/X-Y-description`

### Project Structure (UPDATE/CREATE)

**CREATE Files:**
```
backend/app/models/asset.py                      # Asset SQLModel
backend/app/services/asset_service.py            # Upload orchestration
backend/app/services/file_validation_service.py  # MIME/size validation
backend/app/repositories/asset_repository.py     # Asset CRUD
backend/app/api/routes/upload.py                 # Upload endpoint
backend/app/schemas/asset.py                     # Asset schemas
backend/app/schemas/upload.py                    # Upload schemas
backend/app/alembic/versions/xxx_add_assets_table.py  # Migration
backend/tests/api/routes/test_upload.py          # Upload tests
backend/tests/services/test_asset_service.py     # Service tests
backend/tests/services/test_file_validation_service.py  # Validation tests
```

**UPDATE Files:**
```
backend/app/models.py                    # ADD ASSET_UPLOAD to AuditAction
backend/app/core/minio_client.py         # ADD upload operations
backend/app/core/config.py               # ADD MIME whitelist, size limits
backend/app/core/exceptions.py           # ADD InvalidFileTypeError, FileTooLargeError
backend/app/api/main.py                  # ADD upload router
backend/app/main.py                      # ADD exception handlers for upload errors
```

### Technical Implementation Details

**Asset Model:**
```python
# backend/app/models/asset.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class Asset(SQLModel, table=True):
    __tablename__ = "assets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    tenant_id: UUID = Field(foreign_key="tenant.id", nullable=False, index=True)
    bucket: str = Field(max_length=63, default="assets")
    object_key: str = Field(max_length=1024, nullable=False)  # Full MinIO path
    file_name: str = Field(max_length=255, nullable=False)
    file_size_bytes: int = Field(nullable=False)
    mime_type: str = Field(max_length=127, nullable=False)
    checksum: str = Field(max_length=64, nullable=False)  # MD5 hex
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**MinIO Upload Service:**
```python
# backend/app/core/minio_client.py (extension)
import hashlib
from minio import Minio

def put_object_streaming(
    client: Minio,
    bucket: str,
    object_key: str,
    data: BinaryIO,
    length: int,
    content_type: str,
) -> tuple[str, str]:
    """
    Upload file to MinIO with streaming and checksum calculation.
    Returns (etag, md5_checksum).
    """
    # Calculate checksum while streaming
    md5_hash = hashlib.md5()

    # Use MinIO SDK put_object which handles streaming internally
    result = client.put_object(
        bucket_name=bucket,
        object_name=object_key,
        data=data,
        length=length,
        content_type=content_type,
    )

    return result.etag, md5_hash.hexdigest()
```

**File Validation Service:**
```python
# backend/app/services/file_validation_service.py
from app.core.config import settings

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "video/mp4",
    "video/webm",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/zip",
    "application/json",
]

# Size limits in bytes
SIZE_LIMITS = {
    "video": 10 * 1024 * 1024 * 1024,  # 10GB
    "image": 500 * 1024 * 1024,         # 500MB
    "default": 5 * 1024 * 1024 * 1024,  # 5GB
}

def validate_mime_type(mime_type: str) -> bool:
    """Validate MIME type against whitelist."""
    return mime_type in ALLOWED_MIME_TYPES

def validate_file_size(size: int, mime_type: str) -> bool:
    """Validate file size based on type."""
    if mime_type.startswith("video/"):
        return size <= SIZE_LIMITS["video"]
    elif mime_type.startswith("image/"):
        return size <= SIZE_LIMITS["image"]
    return size <= SIZE_LIMITS["default"]

def get_safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path components, keep only filename
    import os
    return os.path.basename(filename).replace("..", "")
```

**Upload Endpoint:**
```python
# backend/app/api/routes/upload.py
from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.middleware.rate_limit import limiter, get_dynamic_rate_limit
from app.services.asset_service import AssetService
from app.schemas.asset import AssetResponse

router = APIRouter(prefix="/assets", tags=["upload"])

@router.post(
    "/upload",
    response_model=AssetResponse,
    status_code=201,
)
@limiter.limit(get_dynamic_rate_limit)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session: SessionDep,
    current_user: CurrentUser,
) -> AssetResponse:
    """
    Upload a single file to user's storage area.

    - Validates file type and size
    - Uploads to MinIO with streaming (no full memory buffering)
    - Creates asset metadata in PostgreSQL
    - Returns asset details with checksum
    """
    asset_service = AssetService(session=session, current_user=current_user)

    asset = await asset_service.create_asset(
        file=file,
        ip_address=get_client_ip(request),
    )

    return AssetResponse.model_validate(asset)
```

### Dependencies

**Already Available (from pyproject.toml):**
```
minio>=7.2.0,<8.0.0  # MinIO SDK
fastapi[standard]     # UploadFile support
slowapi                # Rate limiting
sqlmodel               # ORM
pydantic               # Validation
```

**No New Dependencies Required**

### Git Workflow

**Branch:** `story/3-1-single-file-upload`

**Commit Pattern (following previous stories):**
```
feat(story-3.1): Implement single file upload with progress tracking
```

### Testing Standards

**Test Commands:**
```bash
# Run upload tests
uv run pytest backend/tests/api/routes/test_upload.py -v

# Run service tests
uv run pytest backend/tests/services/test_asset_service.py -v

# Run validation tests
uv run pytest backend/tests/services/test_file_validation_service.py -v

# Run with coverage
uv run pytest backend/tests/ -v -k "upload or asset" --cov=backend/app

# Test all story-related code
uv run pytest backend/tests/ -v -k "upload"
```

**Key Test Cases:**
```python
# backend/tests/api/routes/test_upload.py

class TestFileUpload:
    def test_upload_valid_pdf_creates_asset(self, authenticated_client, session):
        """POST /assets/upload with valid PDF creates asset."""
        file_content = b"%PDF-1.4 test content"
        response = authenticated_client.post(
            "/api/v1/assets/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
        )
        assert response.status_code == 201
        assert "asset_id" in response.json()
        assert response.json()["mime_type"] == "application/pdf"
        assert response.json()["checksum"] is not None

    def test_upload_invalid_mime_type_returns_400(self, authenticated_client):
        """POST /assets/upload with .exe returns 400 INVALID_FILE_TYPE."""
        file_content = b"MZ executable content"
        response = authenticated_client.post(
            "/api/v1/assets/upload",
            files={"file": ("malware.exe", file_content, "application/x-msdownload")},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error_code"] == "INVALID_FILE_TYPE"

    def test_upload_oversized_file_returns_400(self, authenticated_client):
        """POST /assets/upload with file > limit returns 400 FILE_TOO_LARGE."""
        # Create file larger than image limit (500MB) - use mock
        response = authenticated_client.post(
            "/api/v1/assets/upload",
            files={"file": ("huge.jpg", b"x" * 1000, "image/jpeg")},
            headers={"Content-Length": str(600 * 1024 * 1024)},  # 600MB
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error_code"] == "FILE_TOO_LARGE"

    def test_upload_creates_audit_log(self, authenticated_client, session):
        """POST /assets/upload creates audit log with ASSET_UPLOAD action."""
        file_content = b"test content"
        response = authenticated_client.post(
            "/api/v1/assets/upload",
            files={"file": ("test.txt", file_content, "application/json")},
        )
        assert response.status_code == 201

        # Verify audit log
        from app.models import AuditLog, AuditAction
        audit_logs = session.exec(
            select(AuditLog).where(AuditLog.action == AuditAction.ASSET_UPLOAD)
        ).all()
        assert len(audit_logs) > 0

    def test_upload_respects_tenant_isolation(self, tenant_a_client, tenant_b_client, session):
        """Upload from Tenant A not visible to Tenant B."""
        # Tenant A uploads
        response_a = tenant_a_client.post(
            "/api/v1/assets/upload",
            files={"file": ("secret.pdf", b"secret", "application/pdf")},
        )
        assert response_a.status_code == 201
        asset_id = response_a.json()["asset_id"]

        # Tenant B cannot access
        response_b = tenant_b_client.get(f"/api/v1/assets/{asset_id}")
        assert response_b.status_code == 404
```

### Security Considerations

**Critical Security Requirements:**
- Validate MIME type from both header AND file magic bytes (prevent spoofing)
- Sanitize filenames to prevent path traversal attacks
- Enforce tenant isolation at MinIO path level
- Rate limiting prevents abuse
- Checksum enables integrity verification

**OWASP Compliance:**
- A3:2021 - Injection: Filename sanitization prevents path traversal
- A4:2021 - Insecure Design: File type validation with whitelist approach
- A7:2021 - Identification and Authentication: JWT required for all uploads
- A9:2021 - Security Logging and Monitoring: Audit logs for all uploads

### Integration Notes

**This story prepares foundation for:**
- Story 3.2: Signed URL generation (uses MinIO client from this story)
- Story 3.3: ZIP archive upload (extends upload service)
- Story 3.4: File type validation (uses validation service from this story)
- Epic 4: Download & streaming (uses asset repository)

**Backward Compatibility:**
- New endpoints, no breaking changes
- Existing auth flows unchanged
- Rate limiting applies consistently

### MinIO Path Convention

**Object Key Format:**
```
{tenant_type}/{tenant_id}/{asset_id}/{filename}

Examples:
publishers/550e8400-e29b-41d4-a716-446655440000/abc123/textbook.pdf
teachers/660e8400-e29b-41d4-a716-446655440001/def456/lecture.mp4
students/770e8400-e29b-41d4-a716-446655440002/ghi789/assignment.pdf
```

**Why include asset_id in path:**
- Prevents filename collisions within same tenant
- Enables versioning at MinIO level
- Simplifies cleanup on asset deletion

## References

- [Source: docs/epics.md#Story-3.1] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#MinIO-Object-Storage-Integration] - MinIO specifications
- [Source: docs/architecture/core-architectural-decisions.md#Multi-Tenant-Data-Isolation] - Tenant isolation requirements
- [Source: docs/architecture/project-structure-boundaries.md#Upload-Flow] - Upload workflow architecture
- [Source: docs/sprint-artifacts/2-5-implement-user-management-endpoints-for-admin-supervisor.md] - Previous story patterns

## Dev Agent Record

### Context Reference

Story 3.1 implementation - first story in Epic 3 (Core Asset Upload & Storage).
Implements single file upload with MinIO integration, file validation, and audit logging.
Builds on authorization and rate limiting from Epic 2.
Foundation for subsequent upload stories (ZIP, multipart, signed URLs).

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

**Code Review Findings & Fixes (2025-12-17):**

1. **Security Enhancement**: Added magic bytes validation to prevent MIME spoofing attacks
   - New function `validate_magic_bytes()` in `file_validation_service.py`
   - Validates file content against known magic byte signatures
   - Prevents attackers from uploading executables disguised as PDFs, etc.

2. **Code Quality**: Fixed 5 unused imports in `asset_service.py` (F401 linter warnings)

3. **Test Coverage**: Created `test_asset_service.py` with 13 unit tests
   - Tests for initialization, validation, upload, rollback, audit, and tenant isolation

4. **Test Coverage**: Added 8 tests for magic bytes validation in `test_file_validation_service.py`

5. **Test Updates**: Fixed 3 integration tests to use proper magic bytes in test data

**Total Tests:** 76 passing (14 upload API + 49 validation + 13 asset service)

### File List

**New Files Created:**
- `backend/app/api/routes/upload.py` - Upload endpoint (POST /api/v1/assets/upload)
- `backend/app/schemas/asset.py` - Asset request/response schemas
- `backend/app/services/asset_service.py` - Asset upload orchestration service
- `backend/app/services/file_validation_service.py` - File validation (MIME, size, magic bytes)
- `backend/app/alembic/versions/d93a7c0df933_add_asset_upload_to_auditaction_enum.py` - Migration for ASSET_UPLOAD enum
- `backend/tests/api/routes/test_upload.py` - Upload endpoint integration tests (14 tests)
- `backend/tests/services/test_file_validation_service.py` - File validation unit tests (49 tests)
- `backend/tests/services/test_asset_service.py` - Asset service unit tests (13 tests)
- `backend/tests/services/__init__.py` - Test package init

**Modified Files:**
- `backend/app/api/main.py` - Added upload router
- `backend/app/api/deps.py` - Added TenantSessionDep (already existed from Story 2.3)
- `backend/app/core/config.py` - Added file upload config (ALLOWED_MIME_TYPES, MAX_FILE_SIZE_*)
- `backend/app/core/exceptions.py` - Added InvalidFileTypeError, FileTooLargeError, InvalidFilenameError, UploadError
- `backend/app/core/minio_client.py` - MinIO streaming upload with checksum calculation
- `backend/app/models.py` - Added ASSET_UPLOAD to AuditAction enum
- `backend/app/repositories/asset_repository.py` - Added get_by_object_key method
