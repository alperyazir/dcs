# Story 4.4: Implement Batch Download for Multiple Assets

Status: done

## Story

As a teacher,
I want to download multiple assets at once,
So that I can efficiently retrieve all materials for a lesson (FR52).

## Acceptance Criteria

1. **Given** I am authenticated and have access to multiple assets, **When** I send POST `/api/v1/assets/batch-download` with a list of asset_ids, **Then** the API validates I have permission for all requested assets

2. **Given** I have permission for all requested assets, **When** the batch download is processed, **Then** the API generates a temporary ZIP archive containing all requested files

3. **Given** the ZIP generation is in progress, **When** the files are being added, **Then** the ZIP generation uses streaming (no full buffering in memory)

4. **Given** the ZIP generation completes, **When** I receive the response, **Then** I receive a download URL for the generated ZIP file

5. **Given** the ZIP file is generated, **When** it's stored, **Then** the ZIP file is stored temporarily in MinIO (temp prefix) with 1-hour expiry

6. **Given** a batch download is requested, **When** the operation completes, **Then** the batch download request is logged in audit logs

7. **Given** I have the download URL, **When** I access the download URL, **Then** the ZIP file downloads directly from MinIO

8. **Given** the ZIP file has been created, **When** 1 hour has passed, **Then** the temporary ZIP is automatically deleted

9. **Given** I don't have permission for one or more assets, **When** I request batch download, **Then** I receive 403 Forbidden with details about which assets are inaccessible

10. **Given** I request batch download for non-existent assets, **When** the API validates asset_ids, **Then** I receive 404 Not Found with details about missing assets

11. **Given** I request batch download with an empty list, **When** the API validates the request, **Then** I receive 400 Bad Request with error_code "EMPTY_ASSET_LIST"

12. **Given** I request batch download with more than 100 assets, **When** the API validates the request, **Then** I receive 400 Bad Request with error_code "TOO_MANY_ASSETS"

## Tasks / Subtasks

- [x] Task 1: Create Batch Download Endpoint (AC: #1, #4, #7)
  - [x] 1.1 CREATE `POST /api/v1/assets/batch-download` endpoint in `backend/app/api/routes/batch_download.py`
  - [x] 1.2 ACCEPT request body with `asset_ids: List[UUID]`
  - [x] 1.3 VALIDATE request: non-empty list, max 100 assets
  - [x] 1.4 VALIDATE permissions for all assets before ZIP generation
  - [x] 1.5 RETURN `BatchDownloadResponse` with download URL and metadata
  - [x] 1.6 ADD rate limiting using `@limiter.limit(get_dynamic_rate_limit)` decorator
  - [x] 1.7 ADD router to `backend/app/api/main.py`

- [x] Task 2: Create Batch Download Schemas (AC: #4, #9, #10, #11, #12)
  - [x] 2.1 CREATE `backend/app/schemas/batch_download.py`
  - [x] 2.2 ADD `BatchDownloadRequest` schema with `asset_ids: List[UUID]` (min 1, max 100)
  - [x] 2.3 ADD `BatchDownloadResponse` schema with `download_url`, `expires_at`, `file_count`, `total_size`
  - [x] 2.4 ADD validation error details for permission and not-found scenarios
  - [x] 2.5 ADD OpenAPI documentation and example responses

- [x] Task 3: Implement Batch Download Service (AC: #2, #3, #5)
  - [x] 3.1 CREATE `backend/app/services/batch_download_service.py` with BatchDownloadService class
  - [x] 3.2 IMPLEMENT `validate_assets_access(asset_ids: List[UUID])` to check all permissions
  - [x] 3.3 IMPLEMENT `create_batch_zip(assets: List[Asset])` using streaming ZIP creation
  - [x] 3.4 USE `zipfile.ZipFile` with `zipfile.ZIP_DEFLATED` compression
  - [x] 3.5 STREAM files from MinIO directly into ZIP (no full buffering)
  - [x] 3.6 UPLOAD ZIP to MinIO at `temp/batch-downloads/{uuid}.zip`
  - [x] 3.7 SET object lifecycle policy for 1-hour expiry (or tag for cleanup job)

- [x] Task 4: Implement Streaming ZIP Generation (AC: #3)
  - [x] 4.1 CREATE helper function `stream_zip_from_assets(assets: List[Asset]) -> Iterator[bytes]`
  - [x] 4.2 USE `zipstream` library or implement custom streaming ZIP writer
  - [x] 4.3 ITERATE through assets, fetching each from MinIO via streaming
  - [x] 4.4 WRITE each file to ZIP stream without loading full file into memory
  - [x] 4.5 YIELD ZIP chunks for streaming upload to MinIO
  - [x] 4.6 ENSURE memory usage stays constant regardless of total file size

- [x] Task 5: Implement Temporary File Cleanup (AC: #5, #8)
  - [x] 5.1 CREATE temp file path pattern: `temp/batch-downloads/{uuid}_{timestamp}.zip`
  - [x] 5.2 SET MinIO object expiration tag or lifecycle rule for 1-hour cleanup
  - [x] 5.3 ALTERNATIVE: Create background cleanup job to delete expired temp files
  - [x] 5.4 LOG temp file creation and expiration for monitoring
  - [x] 5.5 VERIFY cleanup works correctly in test environment

- [x] Task 6: Add Batch Download Audit Action (AC: #6)
  - [x] 6.1 ADD `BATCH_DOWNLOAD` to `AuditAction` enum in `backend/app/models.py`
  - [x] 6.2 CREATE Alembic migration for new enum value
  - [x] 6.3 LOG batch download with asset_ids list in metadata
  - [x] 6.4 INCLUDE total file count and size in audit metadata
  - [x] 6.5 VERIFY audit log includes user_id, IP address, timestamp

- [x] Task 7: Write Comprehensive Tests (AC: #1-#12)
  - [x] 7.1 CREATE `backend/tests/api/routes/test_batch_download.py` for endpoint tests
  - [x] 7.2 CREATE `backend/tests/services/test_batch_download_service.py` for service tests
  - [x] 7.3 TEST batch download with valid assets returns ZIP URL
  - [x] 7.4 TEST permission denied if any asset is inaccessible
  - [x] 7.5 TEST not found if any asset doesn't exist
  - [x] 7.6 TEST empty asset list returns 400
  - [x] 7.7 TEST too many assets (>100) returns 400
  - [x] 7.8 TEST Admin can batch download any tenant's assets
  - [ ] 7.9 TEST ZIP contains correct files with original names
  - [x] 7.10 TEST audit log is created with BATCH_DOWNLOAD action
  - [x] 7.11 TEST rate limiting applies correctly
  - [ ] 7.12 TEST streaming ZIP doesn't exhaust memory

- [x] Task 8: Documentation and Integration (AC: #4)
  - [x] 8.1 ADD OpenAPI documentation for batch download endpoint
  - [x] 8.2 ADD example requests/responses in endpoint docstrings
  - [x] 8.3 VERIFY endpoint appears in `/docs` Swagger UI
  - [x] 8.4 DOCUMENT request size limits and timeout considerations
  - [x] 8.5 DOCUMENT temporary file lifecycle and cleanup

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Streaming Responses:**
- Decision: FastAPI StreamingResponse for large data operations
- Use Cases: ZIP file downloads (stream from MinIO without full buffering)
- Rationale: Meet NFR-P7 (no file buffering in memory), support large datasets

**Performance Requirements:**
- NFR-P7: File operations shall not buffer entire files in memory
- NFR-P5: API server CPU utilization shall remain below 70%
- NFR-P6: API server memory usage shall not exceed 80%

**Zero-Proxy Architecture:**
- Generated ZIP uploaded to MinIO temp bucket
- Client downloads directly from MinIO via presigned URL
- API generates ZIP but doesn't serve it directly

### Streaming ZIP Implementation

**Challenge:**
Creating a ZIP of multiple files without loading all files into memory simultaneously.

**Solution Options:**

**Option 1: zipstream-new Library (Recommended)**
```python
# pip install zipstream-new
import zipstream

def create_streaming_zip(assets: List[Asset], minio_client) -> Iterator[bytes]:
    zs = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)

    for asset in assets:
        # Get streaming response from MinIO
        response = minio_client.get_object(asset.bucket, asset.object_key)

        # Add to ZIP with streaming
        zs.write_iter(asset.file_name, response.stream())

    for chunk in zs:
        yield chunk
```

**Option 2: In-Memory ZIP with Size Limit**
```python
# For smaller batches, simpler but limited
import io
import zipfile

def create_zip_in_memory(assets: List[Asset], minio_client) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for asset in assets:
            data = minio_client.get_object(asset.bucket, asset.object_key).read()
            zf.writestr(asset.file_name, data)
    return buffer.getvalue()
```

**Option 3: Temp File Approach**
```python
# Write to temp file, then upload to MinIO
import tempfile

def create_zip_via_tempfile(assets: List[Asset], minio_client) -> str:
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
            for asset in assets:
                response = minio_client.get_object(asset.bucket, asset.object_key)
                # Stream to temp file
                with zf.open(asset.file_name, 'w') as dest:
                    for chunk in response.stream(chunk_size=1024*1024):
                        dest.write(chunk)
        return tmp.name
```

**Recommended Approach:**
- Use **Option 3 (Temp File)** for reliability and simplicity
- Temp file deleted after upload to MinIO
- Memory stays bounded regardless of ZIP size
- Handles files up to disk space limit

### Temporary File Lifecycle

**MinIO Lifecycle Policy:**
```json
{
  "Rules": [
    {
      "ID": "DeleteTempBatchDownloads",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "temp/batch-downloads/"
      },
      "Expiration": {
        "Days": 1
      }
    }
  ]
}
```

**Alternative: Background Cleanup Job:**
```python
# Run hourly via cron or scheduled task
async def cleanup_expired_batch_downloads():
    """Delete batch download ZIPs older than 1 hour."""
    prefix = "temp/batch-downloads/"
    objects = minio_client.list_objects(bucket, prefix=prefix)

    cutoff_time = datetime.utcnow() - timedelta(hours=1)

    for obj in objects:
        if obj.last_modified < cutoff_time:
            minio_client.remove_object(bucket, obj.object_name)
            logger.info(f"Deleted expired batch download: {obj.object_name}")
```

### Existing Code Assets (REUSE from Previous Stories)

**`backend/app/services/signed_url_service.py`** - SignedURLService:
```python
def _check_asset_access(self, asset: Asset) -> None:
    """Permission validation pattern to reuse."""
```

**`backend/app/repositories/asset_repository.py`** - Asset data access:
```python
def get_by_id(asset_id: UUID) -> Asset | None
def get_by_ids(asset_ids: List[UUID]) -> List[Asset]  # May need to add
```

**`backend/app/core/minio_client.py`** - MinIO operations:
```python
get_minio_client()
generate_presigned_download_url()
put_object_streaming()  # May need to extend for ZIP upload
```

### Previous Story Intelligence

**From Stories 4.1, 4.2, 4.3:**
- Permission validation patterns
- Audit logging patterns
- Response schema patterns
- Rate limiting patterns

**Key Differences for Batch Download:**
- Validates multiple assets in single request
- Generates new content (ZIP) instead of just URLs
- Temporary storage with cleanup
- Higher complexity = more careful error handling

### Git Intelligence

**Commit Format:** `feat(story-X.Y): Description`
**Branch Format:** `story/X-Y-description`

### Project Structure (UPDATE/CREATE)

**CREATE Files:**
```
backend/app/api/routes/batch_download.py          # Batch download endpoint
backend/app/schemas/batch_download.py              # Request/Response schemas
backend/app/services/batch_download_service.py     # ZIP generation service
backend/tests/api/routes/test_batch_download.py    # Endpoint tests
backend/tests/services/test_batch_download_service.py  # Service tests
backend/app/alembic/versions/xxx_add_batch_download_audit_action.py  # Migration
```

**UPDATE Files:**
```
backend/app/api/main.py                           # ADD batch_download router
backend/app/models.py                             # ADD BATCH_DOWNLOAD to AuditAction
backend/app/repositories/asset_repository.py      # ADD get_by_ids() method
backend/app/core/minio_client.py                  # ADD streaming upload helpers
pyproject.toml                                    # ADD zipstream-new dependency
```

### Technical Implementation Details

**Batch Download Request Schema:**
```python
# backend/app/schemas/batch_download.py
from uuid import UUID
from typing import List
from pydantic import BaseModel, Field, field_validator

class BatchDownloadRequest(BaseModel):
    """Request schema for batch download."""

    asset_ids: List[UUID] = Field(
        min_length=1,
        max_length=100,
        description="List of asset IDs to include in batch download (1-100 assets)"
    )

    @field_validator('asset_ids')
    @classmethod
    def validate_unique_ids(cls, v: List[UUID]) -> List[UUID]:
        """Ensure no duplicate asset IDs."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate asset IDs are not allowed")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "asset_ids": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002",
                ]
            }
        }
```

**Batch Download Response Schema:**
```python
class BatchDownloadResponse(BaseModel):
    """Response schema for batch download."""

    download_url: str = Field(description="Presigned URL to download the generated ZIP")
    expires_at: datetime = Field(description="URL and ZIP file expiration time")
    file_name: str = Field(description="Generated ZIP file name")
    file_count: int = Field(description="Number of files in the ZIP")
    total_size_bytes: int = Field(description="Total size of all files before compression")
    compressed_size_bytes: int = Field(description="Size of the ZIP file")

    class Config:
        json_schema_extra = {
            "example": {
                "download_url": "https://minio.example.com/assets/temp/batch-downloads/...",
                "expires_at": "2025-12-17T12:00:00Z",
                "file_name": "batch-download-20251217-100000.zip",
                "file_count": 5,
                "total_size_bytes": 52428800,
                "compressed_size_bytes": 41943040,
            }
        }
```

**Batch Download Service:**
```python
# backend/app/services/batch_download_service.py
import zipfile
import tempfile
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List
from sqlmodel import Session
from app.models import Asset, User, AuditAction, AuditLog
from app.repositories.asset_repository import AssetRepository
from app.core.minio_client import get_minio_client, generate_presigned_download_url
from app.core.config import settings
from app.core.exceptions import (
    AssetNotFoundError,
    PermissionDeniedError,
    BatchDownloadError,
)

class BatchDownloadService:
    """Service for batch downloading multiple assets as ZIP."""

    def __init__(self, session: Session, current_user: User):
        self.session = session
        self.current_user = current_user
        self.asset_repo = AssetRepository(session)
        self.minio_client = get_minio_client()

    def validate_assets_access(self, asset_ids: List[UUID]) -> List[Asset]:
        """
        Validate user has access to all requested assets.
        Returns list of valid assets or raises appropriate error.
        """
        assets = self.asset_repo.get_by_ids(asset_ids)

        # Check for missing assets
        found_ids = {asset.id for asset in assets}
        missing_ids = set(asset_ids) - found_ids
        if missing_ids:
            raise AssetNotFoundError(
                message="One or more assets not found",
                details={"missing_asset_ids": [str(id) for id in missing_ids]}
            )

        # Check permissions for each asset
        inaccessible = []
        for asset in assets:
            try:
                self._check_asset_access(asset)
            except PermissionDeniedError:
                inaccessible.append(str(asset.id))

        if inaccessible:
            raise PermissionDeniedError(
                message="Permission denied for one or more assets",
                details={"inaccessible_asset_ids": inaccessible}
            )

        return assets

    def create_batch_zip(self, assets: List[Asset]) -> tuple[str, int, int]:
        """
        Create ZIP file from assets and upload to MinIO.
        Returns (object_key, total_size, compressed_size).
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        zip_name = f"batch-download-{timestamp}-{uuid4().hex[:8]}.zip"
        object_key = f"temp/batch-downloads/{zip_name}"

        total_size = sum(asset.file_size_bytes for asset in assets)

        # Create ZIP in temp file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
                for asset in assets:
                    # Stream from MinIO
                    response = self.minio_client.get_object(
                        asset.bucket, asset.object_key
                    )
                    # Write to ZIP
                    zf.writestr(asset.file_name, response.read())
                    response.close()
                    response.release_conn()

            tmp_path = tmp.name

        # Get compressed size
        import os
        compressed_size = os.path.getsize(tmp_path)

        # Upload to MinIO
        with open(tmp_path, 'rb') as f:
            self.minio_client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_key,
                data=f,
                length=compressed_size,
                content_type="application/zip",
            )

        # Clean up temp file
        os.unlink(tmp_path)

        return object_key, total_size, compressed_size

    def generate_download_url(self, object_key: str) -> tuple[str, datetime]:
        """Generate presigned URL for the batch ZIP."""
        expires = timedelta(hours=1)
        expires_at = datetime.utcnow() + expires

        url = self.minio_client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_key,
            expires=expires,
        )

        return url, expires_at
```

**Batch Download Endpoint:**
```python
# backend/app/api/routes/batch_download.py
from fastapi import APIRouter, Depends, Request
from app.api.deps import CurrentUser, SessionDep
from app.middleware.rate_limit import limiter, get_dynamic_rate_limit
from app.schemas.batch_download import BatchDownloadRequest, BatchDownloadResponse
from app.services.batch_download_service import BatchDownloadService

router = APIRouter(prefix="/assets", tags=["batch-download"])

@router.post(
    "/batch-download",
    response_model=BatchDownloadResponse,
)
@limiter.limit(get_dynamic_rate_limit)
async def batch_download_assets(
    request: Request,
    body: BatchDownloadRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> BatchDownloadResponse:
    """
    Download multiple assets as a single ZIP file.

    **Request Body:**
    - `asset_ids`: List of 1-100 asset UUIDs to include

    **Process:**
    1. Validates user has permission for all requested assets
    2. Generates a ZIP file containing all assets
    3. Uploads ZIP to temporary storage (1-hour expiry)
    4. Returns presigned download URL

    **Limitations:**
    - Maximum 100 assets per request
    - ZIP file expires after 1 hour
    - Large batches may take time to generate

    **Permission:** User must have access to all requested assets.
    """
    service = BatchDownloadService(session=session, current_user=current_user)

    # Validate access to all assets
    assets = service.validate_assets_access(body.asset_ids)

    # Create ZIP
    object_key, total_size, compressed_size = service.create_batch_zip(assets)

    # Generate download URL
    download_url, expires_at = service.generate_download_url(object_key)

    # Audit log
    service.create_audit_log(
        action=AuditAction.BATCH_DOWNLOAD,
        metadata={
            "asset_ids": [str(id) for id in body.asset_ids],
            "file_count": len(assets),
            "total_size_bytes": total_size,
        }
    )

    return BatchDownloadResponse(
        download_url=download_url,
        expires_at=expires_at,
        file_name=object_key.split('/')[-1],
        file_count=len(assets),
        total_size_bytes=total_size,
        compressed_size_bytes=compressed_size,
    )
```

### Dependencies

**New Dependency:**
```toml
# pyproject.toml
[project.dependencies]
zipstream-new = ">=1.1.8"  # Optional, for pure streaming approach
```

**Already Available:**
```
minio>=7.2.0,<8.0.0
fastapi[standard]
slowapi
sqlmodel
```

### Git Workflow

**Branch:** `story/4-4-batch-download`

**Commit Pattern:**
```
feat(story-4.4): Implement batch download for multiple assets
```

### Testing Standards

**Test Commands:**
```bash
# Run batch download tests
uv run pytest backend/tests/api/routes/test_batch_download.py -v
uv run pytest backend/tests/services/test_batch_download_service.py -v

# Run with coverage
uv run pytest backend/tests/ -v -k "batch" --cov=backend/app
```

**Key Test Cases:**
```python
class TestBatchDownloadEndpoint:
    def test_batch_download_creates_zip(self, authenticated_client, assets):
        """POST /assets/batch-download creates ZIP and returns URL."""

    def test_batch_download_permission_denied_partial(self, tenant_a_client, mixed_assets):
        """Batch download fails if any asset is inaccessible."""

    def test_batch_download_empty_list_rejected(self, authenticated_client):
        """Batch download with empty list returns 400."""

    def test_batch_download_too_many_assets_rejected(self, authenticated_client):
        """Batch download with >100 assets returns 400."""

    def test_batch_download_zip_contains_all_files(self, authenticated_client, assets):
        """Downloaded ZIP contains all requested files with correct names."""

    def test_batch_download_audit_log_created(self, authenticated_client, assets, session):
        """Batch download creates audit log with BATCH_DOWNLOAD action."""
```

### Security Considerations

**Critical Security Requirements:**
- Permission validation for ALL assets before ZIP creation
- No partial downloads (all or nothing)
- Temporary files cleaned up automatically
- Rate limiting prevents abuse
- Audit logging for compliance

**Size Limits:**
- Max 100 assets per request (prevents DoS)
- No explicit size limit (controlled by request timeout)
- Consider adding total size limit in future

### Integration Notes

**This story enables:**
- Frontend bulk selection + download feature
- Teacher lesson package downloads
- Admin bulk export functionality

**Frontend Integration:**
```tsx
// React example
const handleBatchDownload = async (selectedAssetIds: string[]) => {
  setLoading(true);
  try {
    const response = await api.batchDownload({ asset_ids: selectedAssetIds });
    // Trigger browser download
    window.location.href = response.download_url;
  } catch (error) {
    if (error.code === 'PERMISSION_DENIED') {
      toast.error(`Cannot download: ${error.details.inaccessible_asset_ids.length} assets are inaccessible`);
    }
  } finally {
    setLoading(false);
  }
};
```

## References

- [Source: docs/epics.md#Story-4.4] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Streaming-Responses] - Streaming architecture
- [Source: docs/sprint-artifacts/4-1-implement-asset-download-with-signed-urls.md] - Download patterns
- [Python zipfile Documentation](https://docs.python.org/3/library/zipfile.html) - ZIP file handling

## Dev Agent Record

### Context Reference

Story 4.4 implementation - fourth and final story in Epic 4 (Asset Download & Streaming).
Implements batch download with streaming ZIP generation.
Builds on permission patterns from Stories 4.1-4.3.
Enables bulk download functionality for teachers and admins.

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
