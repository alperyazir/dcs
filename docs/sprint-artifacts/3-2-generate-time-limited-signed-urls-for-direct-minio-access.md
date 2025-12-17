# Story 3.2: Generate Time-Limited Signed URLs for Direct MinIO Access

Status: review

## Story

As a developer,
I want the API to generate signed URLs for direct MinIO access,
So that files are not proxied through the API layer (FR21, FR49, NFR-P2, NFR-P7).

## Acceptance Criteria

1. **Given** a user requests access to an asset they're authorized for, **When** I call the signed URL generation service, **Then** the backend generates a presigned URL using MinIO SDK with HMAC-SHA256 signature

2. **Given** signed URL is requested for upload, **When** URL is generated, **Then** signed URLs for uploads have 15-minute TTL (short-lived for security)

3. **Given** signed URL is requested for download, **When** URL is generated, **Then** signed URLs for downloads have 1-hour TTL (classroom viewing duration)

4. **Given** signed URL generation is triggered, **When** processing completes, **Then** the signed URL generation completes within 100ms (NFR-P2)

5. **Given** a signed URL is generated, **When** the client uses it, **Then** clients use the signed URL to upload/download directly to/from MinIO without API proxying

6. **Given** files are accessed via signed URLs, **When** monitoring system resources, **Then** API CPU and RAM usage remains minimal as files bypass the API layer (FR51, NFR-P5, NFR-P6)

7. **Given** a signed URL has been issued, **When** the signed URL expires, **Then** MinIO rejects the request and the client must request a new signed URL

8. **Given** a user requests a signed URL, **When** the asset permissions are checked, **Then** the API validates the user has read/write permission for the asset before generating the URL

9. **Given** a signed URL is successfully generated, **When** the URL is returned to the client, **Then** the response includes the signed URL and expiration timestamp in ISO-8601 format

10. **Given** a user requests a signed URL for upload, **When** the upload completes, **Then** the uploaded file is stored at the correct tenant-isolated path in MinIO

## Tasks / Subtasks

- [x] Task 1: Add Signed URL Configuration to Settings (AC: #2, #3)
  - [x] 1.1 UPDATE `backend/app/core/config.py` to add `PRESIGNED_URL_UPLOAD_EXPIRES_SECONDS: int = 900` (15 minutes)
  - [x] 1.2 ADD `PRESIGNED_URL_DOWNLOAD_EXPIRES_SECONDS: int = 3600` (1 hour)
  - [x] 1.3 ADD `PRESIGNED_URL_STREAM_EXPIRES_SECONDS: int = 3600` (1 hour, same as download)
  - [x] 1.4 DOCUMENT environment variables in `.env.example`

- [x] Task 2: Extend MinIO Client with Signed URL Generation (AC: #1, #4, #7)
  - [x] 2.1 UPDATE `backend/app/core/minio_client.py` to add `generate_presigned_download_url()` function
  - [x] 2.2 ADD `generate_presigned_upload_url()` function for PUT operations
  - [x] 2.3 IMPLEMENT using MinIO SDK's `presigned_get_object()` and `presigned_put_object()` methods
  - [x] 2.4 ENSURE URL generation uses HMAC-SHA256 signatures (MinIO SDK default)
  - [x] 2.5 ADD logging for URL generation with timing metrics
  - [x] 2.6 TEST URL generation completes within 100ms (NFR-P2)

- [x] Task 3: Create Signed URL Service (AC: #1, #8, #9)
  - [x] 3.1 CREATE `backend/app/services/signed_url_service.py` with SignedURLService class
  - [x] 3.2 IMPLEMENT `generate_download_url(asset_id: UUID)` with permission validation
  - [x] 3.3 IMPLEMENT `generate_upload_url(file_name: str, mime_type: str)` for new uploads
  - [x] 3.4 IMPLEMENT `generate_stream_url(asset_id: UUID)` for video/audio streaming
  - [x] 3.5 ADD permission checking using existing authorization patterns from Epic 2
  - [x] 3.6 RETURN signed URL with ISO-8601 expiration timestamp
  - [x] 3.7 ADD audit logging for signed URL generation (actions: SIGNED_URL_DOWNLOAD, SIGNED_URL_UPLOAD)

- [x] Task 4: Create Signed URL API Endpoints (AC: #5, #9)
  - [x] 4.1 CREATE `backend/app/api/routes/signed_urls.py` with router
  - [x] 4.2 IMPLEMENT `GET /api/v1/assets/{asset_id}/download-url` endpoint
  - [x] 4.3 IMPLEMENT `GET /api/v1/assets/{asset_id}/stream-url` endpoint (for video/audio)
  - [x] 4.4 IMPLEMENT `POST /api/v1/assets/upload-url` endpoint (for presigned upload)
  - [x] 4.5 ADD rate limiting using existing `get_dynamic_rate_limit` decorator
  - [x] 4.6 ADD router to `backend/app/api/main.py`
  - [x] 4.7 RETURN `SignedURLResponse` schema with `url` and `expires_at` fields

- [x] Task 5: Create Request/Response Schemas (AC: #9)
  - [x] 5.1 CREATE `backend/app/schemas/signed_url.py` with `SignedURLResponse` schema
  - [x] 5.2 ADD fields: `url: str`, `expires_at: datetime`, `type: Literal["download", "upload", "stream"]`
  - [x] 5.3 CREATE `UploadURLRequest` schema with `file_name: str`, `mime_type: str`, `file_size: int`
  - [x] 5.4 ADD validation for file_name and mime_type (reuse from file_validation_service)
  - [x] 5.5 TEST schema validation for edge cases

- [x] Task 6: Add Audit Logging Support (AC: #8)
  - [x] 6.1 ADD `SIGNED_URL_DOWNLOAD` to `AuditAction` enum in `backend/app/models.py`
  - [x] 6.2 ADD `SIGNED_URL_UPLOAD` to `AuditAction` enum
  - [x] 6.3 CREATE Alembic migration for new enum values
  - [x] 6.4 IMPLEMENT audit logging in SignedURLService
  - [x] 6.5 TEST audit logs are created for signed URL generation

- [x] Task 7: Implement Permission Validation (AC: #8)
  - [x] 7.1 IMPLEMENT asset ownership check in SignedURLService
  - [x] 7.2 ADD Admin/Supervisor bypass for all assets
  - [x] 7.3 IMPLEMENT tenant isolation check (user can only access own tenant's assets)
  - [x] 7.4 RETURN 403 Forbidden if user lacks permission
  - [x] 7.5 RETURN 404 Not Found if asset doesn't exist (prevent enumeration)
  - [x] 7.6 TEST permission validation for all user roles

- [x] Task 8: Write Comprehensive Tests (AC: #1-#10)
  - [x] 8.1 CREATE `backend/tests/api/routes/test_signed_urls.py` for endpoint tests
  - [x] 8.2 CREATE `backend/tests/services/test_signed_url_service.py` for service tests
  - [x] 8.3 TEST download URL generation returns valid presigned URL
  - [x] 8.4 TEST upload URL generation returns valid presigned URL
  - [x] 8.5 TEST URL expiration times match configuration
  - [x] 8.6 TEST permission denied for unauthorized users
  - [x] 8.7 TEST asset not found for non-existent assets
  - [x] 8.8 TEST URL generation performance (< 100ms)
  - [x] 8.9 TEST audit logs are created
  - [x] 8.10 TEST tenant isolation prevents cross-tenant access
  - [x] 8.11 TEST rate limiting applies correctly

- [x] Task 9: Documentation and Integration (AC: #5)
  - [x] 9.1 ADD OpenAPI documentation for new endpoints
  - [x] 9.2 UPDATE API documentation with signed URL workflow
  - [x] 9.3 ADD example requests/responses in endpoint docstrings
  - [x] 9.4 VERIFY endpoints appear in `/docs` Swagger UI

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Signed URL Generation:**
- Decision: HMAC-SHA256 signatures generated by backend, validated by MinIO
- SDK: MinIO Python SDK `presigned_get_object()` and `presigned_put_object()` methods
- Default TTL: 1 hour (configurable per request type)
- Upload URLs: 15 minutes TTL for security (short-lived)
- Download URLs: 1 hour TTL for classroom usage
- Zero-proxy Architecture: Clients access MinIO directly via signed URLs (NFR-P4)

**MinIO SDK Methods:**
```python
from minio import Minio
from datetime import timedelta

client = Minio(...)

# For downloads (GET)
url = client.presigned_get_object(
    bucket_name="assets",
    object_name="publishers/uuid/asset-id/file.pdf",
    expires=timedelta(hours=1),  # 1 hour for downloads
)

# For uploads (PUT)
url = client.presigned_put_object(
    bucket_name="assets",
    object_name="publishers/uuid/asset-id/file.pdf",
    expires=timedelta(minutes=15),  # 15 minutes for uploads
)
```

**Performance Requirements:**
- NFR-P2: Signed URL generation shall complete within 100ms
- NFR-P5: API server CPU utilization shall remain below 70%
- NFR-P6: API server memory usage shall not exceed 80%
- NFR-P7: File operations shall not buffer entire files in memory

**Security Requirements:**
- NFR-S4: Signed URLs shall be time-limited (configurable)
- NFR-S8: Users shall only access storage areas they are authorized for
- NFR-S9: Cross-tenant access shall be prevented

### Existing Code Assets (REUSE from Story 3.1)

**`backend/app/core/minio_client.py`** - MinIO client (extend with signed URL methods):
```python
# Current implementation includes:
get_minio_client()  # Singleton MinIO client
generate_object_key()  # Tenant-isolated path generation
put_object_streaming()  # Upload with checksum
delete_object()  # Object deletion
get_object_url()  # Direct URL (NOT presigned - for internal use)

# ADD for Story 3.2:
generate_presigned_download_url()
generate_presigned_upload_url()
```

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

**`backend/app/repositories/asset_repository.py`** - Asset CRUD:
```python
class AssetRepository:
    def get_by_id(asset_id: UUID) -> Asset | None
    def get_by_object_key(object_key: str) -> Asset | None
    # Includes tenant isolation
```

**`backend/app/models.py`** - Models and enums:
```python
class Asset  # Asset model with tenant_id, object_key, etc.
class AuditAction  # Enum for audit log actions
class AuditLog  # Audit log model
```

### Previous Story Intelligence (Story 3.1)

**Patterns Established:**
- Asset model stores `bucket`, `object_key`, `tenant_id` for MinIO reference
- Object key format: `{tenant_type}/{tenant_id}/{asset_id}/{file_name}`
- Rate limiting applied via `@limiter.limit(get_dynamic_rate_limit)` decorator
- Request object required for rate limiter: `request: Request`
- Audit logging with `AuditAction` enum and `AuditLog` model
- Error responses follow standard format with `error_code`, `message`, `details`, `request_id`
- File validation service for MIME type and size checks
- Transaction consistency: rollback operations on failure

**Key Files from Story 3.1:**
- `backend/app/core/minio_client.py` - MinIO operations (extend this)
- `backend/app/services/asset_service.py` - Upload workflow pattern to follow
- `backend/app/repositories/asset_repository.py` - Asset data access
- `backend/app/api/routes/upload.py` - Endpoint pattern to follow
- `backend/app/schemas/asset.py` - Schema pattern to follow

**Learnings from Story 3.1:**
- MinIO SDK handles HMAC signatures automatically via presigned methods
- Use `datetime.timedelta` for expiration time
- Log timing metrics for performance monitoring
- Audit log only after successful operation
- Return structured response with timestamp

### Git Intelligence (Recent Commits)

Recent commits show established patterns:
- `feat(story-3.1): Implement single file upload with validation and security`
- `feat(story-2.5): Implement User Management Endpoints for Admin/Supervisor`
- `feat: Stories 2.3 & 2.4 - Multi-tenant RLS + Rate Limiting`

**Commit Format:** `feat(story-X.Y): Description`
**Branch Format:** `story/X-Y-description`

### Project Structure (UPDATE/CREATE)

**CREATE Files:**
```
backend/app/services/signed_url_service.py       # Signed URL generation service
backend/app/api/routes/signed_urls.py            # Signed URL endpoints
backend/app/schemas/signed_url.py                # Request/Response schemas
backend/app/alembic/versions/xxx_add_signed_url_audit_actions.py  # Migration
backend/tests/api/routes/test_signed_urls.py     # Endpoint tests
backend/tests/services/test_signed_url_service.py # Service tests
```

**UPDATE Files:**
```
backend/app/core/config.py               # ADD presigned URL expiration settings
backend/app/core/minio_client.py         # ADD presigned URL generation functions
backend/app/models.py                    # ADD SIGNED_URL_DOWNLOAD, SIGNED_URL_UPLOAD to AuditAction
backend/app/api/main.py                  # ADD signed_urls router
.env.example                             # ADD new environment variables
```

### Technical Implementation Details

**MinIO Client Extension:**
```python
# backend/app/core/minio_client.py (additions)
from datetime import timedelta
from app.core.config import settings

def generate_presigned_download_url(
    bucket: str,
    object_key: str,
    expires_seconds: int | None = None,
    client: Minio | None = None,
) -> tuple[str, datetime]:
    """
    Generate presigned URL for downloading an object.

    Args:
        bucket: Bucket name
        object_key: Full object key (path in bucket)
        expires_seconds: URL expiration in seconds (default from settings)
        client: MinIO client (uses singleton if not provided)

    Returns:
        Tuple of (presigned_url, expiration_datetime)
    """
    if client is None:
        client = get_minio_client()

    if expires_seconds is None:
        expires_seconds = settings.PRESIGNED_URL_DOWNLOAD_EXPIRES_SECONDS

    expires = timedelta(seconds=expires_seconds)
    expiration_time = datetime.utcnow() + expires

    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_key,
        expires=expires,
    )

    logger.info(
        "Generated presigned download URL",
        extra={
            "bucket": bucket,
            "object_key": object_key,
            "expires_seconds": expires_seconds,
        },
    )

    return url, expiration_time


def generate_presigned_upload_url(
    bucket: str,
    object_key: str,
    expires_seconds: int | None = None,
    client: Minio | None = None,
) -> tuple[str, datetime]:
    """
    Generate presigned URL for uploading an object.

    Args:
        bucket: Bucket name
        object_key: Full object key (path in bucket)
        expires_seconds: URL expiration in seconds (default from settings)
        client: MinIO client (uses singleton if not provided)

    Returns:
        Tuple of (presigned_url, expiration_datetime)
    """
    if client is None:
        client = get_minio_client()

    if expires_seconds is None:
        expires_seconds = settings.PRESIGNED_URL_UPLOAD_EXPIRES_SECONDS

    expires = timedelta(seconds=expires_seconds)
    expiration_time = datetime.utcnow() + expires

    url = client.presigned_put_object(
        bucket_name=bucket,
        object_name=object_key,
        expires=expires,
    )

    logger.info(
        "Generated presigned upload URL",
        extra={
            "bucket": bucket,
            "object_key": object_key,
            "expires_seconds": expires_seconds,
        },
    )

    return url, expiration_time
```

**Signed URL Service:**
```python
# backend/app/services/signed_url_service.py
from uuid import UUID
from datetime import datetime
from sqlmodel import Session
from app.core.config import settings
from app.core.exceptions import AssetNotFoundError, PermissionDeniedError
from app.core.minio_client import (
    generate_presigned_download_url,
    generate_presigned_upload_url,
    generate_object_key,
)
from app.models import AuditAction, AuditLog, Asset, User, UserRole
from app.repositories.asset_repository import AssetRepository

class SignedURLService:
    """Service for generating signed URLs with permission validation."""

    def __init__(self, session: Session, current_user: User):
        self.session = session
        self.current_user = current_user
        self.asset_repo = AssetRepository(session)

    def _check_asset_access(self, asset: Asset) -> None:
        """Check if current user can access the asset."""
        # Admin/Supervisor can access all assets
        if self.current_user.role in (UserRole.ADMIN, UserRole.SUPERVISOR):
            return

        # Check tenant isolation
        if asset.tenant_id != self.current_user.tenant_id:
            raise PermissionDeniedError(
                message="You do not have permission to access this asset",
                details={"asset_id": str(asset.id)},
            )

        # Check ownership for non-admin users
        if asset.user_id != self.current_user.id:
            # TODO: Check asset_permissions table for granted access (Story 7.3)
            raise PermissionDeniedError(
                message="You do not have permission to access this asset",
                details={"asset_id": str(asset.id)},
            )

    def generate_download_url(self, asset_id: UUID) -> tuple[str, datetime]:
        """Generate presigned download URL for an asset."""
        asset = self.asset_repo.get_by_id(asset_id)

        if not asset:
            raise AssetNotFoundError(
                message="Asset not found",
                details={"asset_id": str(asset_id)},
            )

        self._check_asset_access(asset)

        url, expires_at = generate_presigned_download_url(
            bucket=asset.bucket,
            object_key=asset.object_key,
        )

        # Audit log
        self._create_audit_log(asset.id, AuditAction.SIGNED_URL_DOWNLOAD)

        return url, expires_at

    def generate_stream_url(self, asset_id: UUID) -> tuple[str, datetime]:
        """Generate presigned stream URL for video/audio assets."""
        # Same as download URL but uses stream expiration
        asset = self.asset_repo.get_by_id(asset_id)

        if not asset:
            raise AssetNotFoundError(
                message="Asset not found",
                details={"asset_id": str(asset_id)},
            )

        self._check_asset_access(asset)

        url, expires_at = generate_presigned_download_url(
            bucket=asset.bucket,
            object_key=asset.object_key,
            expires_seconds=settings.PRESIGNED_URL_STREAM_EXPIRES_SECONDS,
        )

        self._create_audit_log(asset.id, AuditAction.SIGNED_URL_DOWNLOAD)

        return url, expires_at
```

**API Endpoints:**
```python
# backend/app/api/routes/signed_urls.py
from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException
from app.api.deps import CurrentUser, SessionDep, get_client_ip
from app.middleware.rate_limit import limiter, get_dynamic_rate_limit
from app.schemas.signed_url import SignedURLResponse, UploadURLRequest
from app.services.signed_url_service import SignedURLService

router = APIRouter(prefix="/assets", tags=["signed-urls"])

@router.get(
    "/{asset_id}/download-url",
    response_model=SignedURLResponse,
)
@limiter.limit(get_dynamic_rate_limit)
async def get_download_url(
    request: Request,
    asset_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> SignedURLResponse:
    """
    Generate a presigned URL for downloading an asset.

    The URL is valid for 1 hour (configurable).
    Clients should use this URL to download directly from MinIO.
    """
    service = SignedURLService(session=session, current_user=current_user)
    url, expires_at = service.generate_download_url(asset_id)

    return SignedURLResponse(
        url=url,
        expires_at=expires_at,
        type="download",
    )

@router.get(
    "/{asset_id}/stream-url",
    response_model=SignedURLResponse,
)
@limiter.limit(get_dynamic_rate_limit)
async def get_stream_url(
    request: Request,
    asset_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> SignedURLResponse:
    """
    Generate a presigned URL for streaming video/audio assets.

    The URL supports HTTP Range requests for seeking.
    Valid for 1 hour (configurable).
    """
    service = SignedURLService(session=session, current_user=current_user)
    url, expires_at = service.generate_stream_url(asset_id)

    return SignedURLResponse(
        url=url,
        expires_at=expires_at,
        type="stream",
    )
```

**Response Schema:**
```python
# backend/app/schemas/signed_url.py
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class SignedURLResponse(BaseModel):
    """Response schema for signed URL generation."""

    url: str = Field(description="Presigned URL for direct MinIO access")
    expires_at: datetime = Field(description="URL expiration time (ISO-8601)")
    type: Literal["download", "upload", "stream"] = Field(
        description="Type of signed URL operation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://minio.example.com/assets/publishers/uuid/asset-id/file.pdf?X-Amz-...",
                "expires_at": "2025-12-17T12:00:00Z",
                "type": "download",
            }
        }

class UploadURLRequest(BaseModel):
    """Request schema for presigned upload URL generation."""

    file_name: str = Field(
        max_length=255,
        description="Name of the file to upload",
    )
    mime_type: str = Field(
        max_length=127,
        description="MIME type of the file",
    )
    file_size: int = Field(
        gt=0,
        description="Size of the file in bytes",
    )
```

### Dependencies

**Already Available (from pyproject.toml):**
```
minio>=7.2.0,<8.0.0  # MinIO SDK with presigned URL support
fastapi[standard]     # API framework
slowapi                # Rate limiting
sqlmodel               # ORM
pydantic               # Validation
```

**No New Dependencies Required**

### Git Workflow

**Branch:** `story/3-2-signed-urls`

**Commit Pattern:**
```
feat(story-3.2): Generate time-limited signed URLs for direct MinIO access
```

### Testing Standards

**Test Commands:**
```bash
# Run signed URL tests
uv run pytest backend/tests/api/routes/test_signed_urls.py -v

# Run service tests
uv run pytest backend/tests/services/test_signed_url_service.py -v

# Run with coverage
uv run pytest backend/tests/ -v -k "signed" --cov=backend/app

# Test performance (URL generation < 100ms)
uv run pytest backend/tests/ -v -k "performance"
```

**Key Test Cases:**
```python
# backend/tests/api/routes/test_signed_urls.py

class TestSignedURLEndpoints:
    def test_download_url_returns_valid_presigned_url(self, authenticated_client, asset):
        """GET /assets/{id}/download-url returns presigned URL."""
        response = authenticated_client.get(f"/api/v1/assets/{asset.id}/download-url")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "expires_at" in data
        assert data["type"] == "download"
        assert "X-Amz-" in data["url"]  # MinIO signature params

    def test_download_url_permission_denied_for_other_tenant(
        self, tenant_a_client, tenant_b_asset
    ):
        """GET /assets/{id}/download-url returns 403 for other tenant's asset."""
        response = tenant_a_client.get(
            f"/api/v1/assets/{tenant_b_asset.id}/download-url"
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "PERMISSION_DENIED"

    def test_download_url_not_found_for_nonexistent_asset(self, authenticated_client):
        """GET /assets/{id}/download-url returns 404 for non-existent asset."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = authenticated_client.get(f"/api/v1/assets/{fake_id}/download-url")
        assert response.status_code == 404

    def test_download_url_admin_can_access_any_asset(
        self, admin_client, tenant_a_asset
    ):
        """Admin can get download URL for any tenant's asset."""
        response = admin_client.get(
            f"/api/v1/assets/{tenant_a_asset.id}/download-url"
        )
        assert response.status_code == 200

    def test_url_generation_performance(self, authenticated_client, asset):
        """URL generation should complete within 100ms."""
        import time
        start = time.time()
        response = authenticated_client.get(f"/api/v1/assets/{asset.id}/download-url")
        duration = time.time() - start
        assert response.status_code == 200
        assert duration < 0.1  # 100ms

    def test_stream_url_returns_valid_presigned_url(
        self, authenticated_client, video_asset
    ):
        """GET /assets/{id}/stream-url returns presigned URL for streaming."""
        response = authenticated_client.get(
            f"/api/v1/assets/{video_asset.id}/stream-url"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "stream"

    def test_audit_log_created_on_download_url_generation(
        self, authenticated_client, asset, session
    ):
        """Download URL generation creates audit log."""
        response = authenticated_client.get(f"/api/v1/assets/{asset.id}/download-url")
        assert response.status_code == 200

        from app.models import AuditLog, AuditAction
        from sqlmodel import select

        audit_logs = session.exec(
            select(AuditLog).where(
                AuditLog.action == AuditAction.SIGNED_URL_DOWNLOAD
            )
        ).all()
        assert len(audit_logs) > 0
```

### Security Considerations

**Critical Security Requirements:**
- Signed URLs are time-limited (15 min upload, 1 hour download)
- Permission validation before URL generation
- Tenant isolation enforced at service layer
- URLs use HMAC-SHA256 signatures (MinIO SDK default)
- Asset existence check prevents enumeration attacks

**OWASP Compliance:**
- A1:2021 - Broken Access Control: Permission validation before URL generation
- A3:2021 - Injection: No user input in MinIO paths (pre-validated object_key from DB)
- A7:2021 - Identification: JWT required for all endpoints
- A9:2021 - Security Logging: Audit logs for all URL generation

### Integration Notes

**This story enables:**
- Story 3.3: ZIP archive upload (uses upload URLs)
- Story 4.1: Asset download (uses download URLs)
- Story 4.2: Video/audio streaming (uses stream URLs)
- Story 4.3: Asset preview (uses download URLs)
- Epic 7: Integration APIs (signed URLs for external apps)

**Backward Compatibility:**
- New endpoints, no breaking changes
- Existing upload workflow unchanged (Story 3.1)
- Rate limiting applies consistently

### Performance Optimization

**URL Generation Performance (NFR-P2 < 100ms):**
- MinIO client is cached via lru_cache singleton
- No database queries for URL generation (only permission check)
- Asset metadata cached in repository layer
- Log timing metrics for monitoring

**Zero-Proxy Architecture:**
- Clients download/upload directly to MinIO
- API only generates URLs, doesn't handle file data
- Reduces API CPU/RAM usage (NFR-P5, NFR-P6)

### MinIO Signed URL Anatomy

**Download URL Example:**
```
https://minio.example.com/assets/publishers/uuid/asset-id/file.pdf
?X-Amz-Algorithm=AWS4-HMAC-SHA256
&X-Amz-Credential=minioadmin/20251217/us-east-1/s3/aws4_request
&X-Amz-Date=20251217T100000Z
&X-Amz-Expires=3600
&X-Amz-SignedHeaders=host
&X-Amz-Signature=abc123...
```

**Upload URL Example:**
```
https://minio.example.com/assets/publishers/uuid/asset-id/file.pdf
?X-Amz-Algorithm=AWS4-HMAC-SHA256
&X-Amz-Credential=minioadmin/20251217/us-east-1/s3/aws4_request
&X-Amz-Date=20251217T100000Z
&X-Amz-Expires=900
&X-Amz-SignedHeaders=host
&X-Amz-Signature=def456...
```

## References

- [Source: docs/epics.md#Story-3.2] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Signed-URL-Generation] - Signed URL specifications
- [Source: docs/architecture/core-architectural-decisions.md#MinIO-Object-Storage-Integration] - MinIO integration
- [Source: docs/sprint-artifacts/3-1-implement-single-file-upload-with-progress-tracking.md] - Previous story patterns
- [MinIO Python SDK Documentation](https://min.io/docs/minio/linux/developers/python/API.html#presigned_get_object) - SDK reference

## Dev Agent Record

### Context Reference

Story 3.2 implementation - second story in Epic 3 (Core Asset Upload & Storage).
Implements presigned URL generation for direct MinIO access without API proxying.
Builds on MinIO client from Story 3.1, extends with presigned URL methods.
Foundation for download, streaming, and external integration stories.
Critical for zero-proxy architecture (NFR-P4, NFR-P7).

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

1. **All 9 tasks completed successfully** - Full implementation of signed URL generation for MinIO
2. **Test Results**: 370 tests passed, 12 skipped, 0 failures
3. **PostgreSQL Enum Fix**: Added both uppercase and lowercase values to auditaction enum via direct ALTER TYPE command to handle SQLAlchemy/SQLModel enum name vs value mismatch
4. **Files Created**:
   - `backend/app/services/signed_url_service.py` - Core service with permission validation
   - `backend/app/api/routes/signed_urls.py` - API endpoints for download, stream, upload URLs
   - `backend/app/schemas/signed_url.py` - Request/Response Pydantic schemas
   - `backend/app/alembic/versions/add_signed_url_audit_actions.py` - Migration for enum values
   - `backend/tests/api/routes/test_signed_urls.py` - Comprehensive endpoint tests
   - `backend/tests/services/test_signed_url_service.py` - Service layer unit tests
5. **Files Modified**:
   - `backend/app/core/config.py` - Added presigned URL TTL settings
   - `backend/app/core/minio_client.py` - Added generate_presigned_download_url() and generate_presigned_upload_url()
   - `backend/app/core/exceptions.py` - Added AssetNotFoundError and AssetAccessDeniedError
   - `backend/app/models.py` - Added SIGNED_URL_DOWNLOAD and SIGNED_URL_UPLOAD to AuditAction enum
   - `backend/app/api/main.py` - Added signed_urls router
   - `.env.example` - Documented new environment variables

### File List

- backend/app/core/config.py
- backend/app/core/minio_client.py
- backend/app/core/exceptions.py
- backend/app/models.py
- backend/app/services/signed_url_service.py
- backend/app/api/routes/signed_urls.py
- backend/app/api/main.py
- backend/app/schemas/signed_url.py
- backend/app/alembic/versions/add_signed_url_audit_actions.py
- backend/tests/api/routes/test_signed_urls.py
- backend/tests/services/test_signed_url_service.py
- docs/sprint-artifacts/sprint-status.yaml
- .env.example
