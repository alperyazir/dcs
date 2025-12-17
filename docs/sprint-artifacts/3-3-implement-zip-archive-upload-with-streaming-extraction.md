# Story 3.3: Implement ZIP Archive Upload with Streaming Extraction

Status: done

## Story

As a publisher,
I want to upload a ZIP archive and have it automatically extracted,
So that I can bulk upload hundreds of assets efficiently (FR2, FR3, NFR-P9).

## Acceptance Criteria

1. **Given** I am authenticated as a Publisher, **When** I send POST `/api/v1/assets/upload-zip` with a ZIP file, **Then** the API accepts and processes the ZIP archive

2. **Given** a ZIP file is uploaded, **When** validation occurs, **Then** the API validates the ZIP file size (max 10GB per NFR-P3)

3. **Given** a valid ZIP file is received, **When** extraction begins, **Then** the ZIP file is streamed and extracted without loading the entire file into memory (NFR-P9)

4. **Given** the ZIP contains system files, **When** extraction processes each entry, **Then** system files are automatically filtered: .DS_Store, __MACOSX/, Thumbs.db, .git/, desktop.ini (FR3)

5. **Given** a file is extracted from the ZIP, **When** validation occurs, **Then** each extracted file is validated for type and size against the same rules as single file upload

6. **Given** files pass validation, **When** they are stored, **Then** each valid file is uploaded to MinIO at `/{tenant_type}/{tenant_id}/{asset_id}/{file_name}`

7. **Given** the ZIP contains folders, **When** files are stored, **Then** folder structure from the ZIP is preserved as MinIO prefixes (FR10)

8. **Given** files are uploaded, **When** metadata is created, **Then** asset metadata records are created for each extracted file with correct checksums

9. **Given** all processing is complete, **When** extraction finishes, **Then** the extraction does not require disk buffering (streaming mode, NFR-P9)

10. **Given** extraction completes successfully, **When** the response is returned, **Then** I receive a response with count of files extracted, count of files skipped, and list of all created assets

11. **Given** any operation occurs, **When** it completes, **Then** all upload operations are logged in audit logs

12. **Given** a file fails validation, **When** processing continues, **Then** the failed file is skipped and reported but extraction continues for remaining files

13. **Given** a corrupt or invalid ZIP is uploaded, **When** processing fails, **Then** the API returns a clear error with INVALID_ZIP_FILE error code

## Tasks / Subtasks

- [x] Task 1: Add ZIP Upload Configuration to Settings (AC: #2)
  - [x] 1.1 UPDATE `backend/app/core/config.py` to add `MAX_ZIP_FILE_SIZE: int = 10_737_418_240` (10GB)
  - [x] 1.2 ADD `MAX_ZIP_EXTRACTED_FILES: int = 1000` (prevent zip bomb)
  - [x] 1.3 ADD `MAX_EXTRACTED_TOTAL_SIZE: int = 53_687_091_200` (50GB total extracted limit)
  - [x] 1.4 ADD `FILTERED_ZIP_PATTERNS: list[str]` for system files to skip
  - [x] 1.5 DOCUMENT environment variables in `.env.example`

- [x] Task 2: Create ZIP File Filter Service (AC: #4)
  - [x] 2.1 CREATE `backend/app/services/zip_filter_service.py` with ZipFilterService class
  - [x] 2.2 IMPLEMENT `should_skip_entry(entry_name: str) -> bool` method
  - [x] 2.3 ADD patterns: `.DS_Store`, `__MACOSX/`, `Thumbs.db`, `.git/`, `desktop.ini`, `*.tmp`, `~$*`
  - [x] 2.4 IMPLEMENT case-insensitive matching for Windows compatibility
  - [x] 2.5 ADD logging for skipped files with reasons
  - [x] 2.6 TEST all filter patterns with various path formats

- [x] Task 3: Create ZIP Extraction Service (AC: #1, #3, #6, #7, #8, #9, #10, #12)
  - [x] 3.1 CREATE `backend/app/services/zip_extraction_service.py` with ZipExtractionService class
  - [x] 3.2 IMPLEMENT `extract_and_upload(zip_file: SpooledTemporaryFile, ...) -> ZipExtractionResult`
  - [x] 3.3 USE Python's `zipfile.ZipFile` with streaming mode (no full memory load)
  - [x] 3.4 IMPLEMENT streaming extraction: iterate entries, stream each to MinIO
  - [x] 3.5 PRESERVE folder structure: extract relative paths as MinIO prefixes
  - [x] 3.6 IMPLEMENT per-file validation using existing `FileValidationService`
  - [x] 3.7 IMPLEMENT per-file checksum calculation during streaming
  - [x] 3.8 IMPLEMENT batch metadata creation with transaction rollback
  - [x] 3.9 IMPLEMENT error collection: continue on file failures, report at end
  - [x] 3.10 ADD zip bomb protection: check compressed vs uncompressed ratio
  - [x] 3.11 RETURN `ZipExtractionResult` with extracted_count, skipped_count, failed_files, created_assets

- [x] Task 4: Extend Asset Service for ZIP Upload (AC: #8, #11)
  - [x] 4.1 UPDATE `backend/app/services/asset_service.py` to add `create_assets_from_zip()` method
  - [x] 4.2 ORCHESTRATE: zip extraction -> per-file upload -> batch metadata creation
  - [x] 4.3 IMPLEMENT transactional consistency: rollback all on critical failure
  - [x] 4.4 ADD audit logging with `AuditAction.ASSET_ZIP_UPLOAD` for batch upload
  - [x] 4.5 ADD individual audit logs for each extracted file

- [x] Task 5: Create ZIP Upload API Endpoint (AC: #1, #10, #13)
  - [x] 5.1 UPDATE `backend/app/api/routes/upload.py` to add `POST /assets/upload-zip` endpoint
  - [x] 5.2 IMPLEMENT file size validation (max 10GB)
  - [x] 5.3 IMPLEMENT ZIP format validation (check magic bytes: PK\x03\x04)
  - [x] 5.4 ADD rate limiting using existing `get_dynamic_rate_limit` decorator
  - [x] 5.5 RETURN `ZipUploadResponse` schema with extraction results
  - [x] 5.6 ADD comprehensive OpenAPI documentation with examples

- [x] Task 6: Create Request/Response Schemas (AC: #10)
  - [x] 6.1 CREATE `backend/app/schemas/zip_upload.py` with `ZipUploadResponse` schema
  - [x] 6.2 ADD fields: `extracted_count: int`, `skipped_count: int`, `failed_count: int`
  - [x] 6.3 ADD `assets: list[AssetResponse]` for created assets
  - [x] 6.4 ADD `skipped_files: list[SkippedFileInfo]` with file_name and reason
  - [x] 6.5 ADD `failed_files: list[FailedFileInfo]` with file_name, error_code, message
  - [x] 6.6 CREATE `ZipExtractionResult` internal model for service layer

- [x] Task 7: Add Audit Logging Support (AC: #11)
  - [x] 7.1 ADD `ASSET_ZIP_UPLOAD` to `AuditAction` enum in `backend/app/models.py`
  - [x] 7.2 CREATE Alembic migration for new enum value
  - [x] 7.3 IMPLEMENT batch audit logging in ZipExtractionService
  - [x] 7.4 TEST audit logs are created for ZIP upload and each extracted file

- [x] Task 8: Implement Streaming MinIO Upload for ZIP Entries (AC: #3, #9)
  - [x] 8.1 UPDATE `backend/app/core/minio_client.py` to add `put_object_from_zipentry()` function
  - [x] 8.2 IMPLEMENT streaming from ZipFile entry directly to MinIO
  - [x] 8.3 CALCULATE checksum during streaming (use ChecksumCalculator wrapper)
  - [x] 8.4 AVOID loading entire file into memory
  - [x] 8.5 TEST memory usage stays constant regardless of file size

- [x] Task 9: Write Comprehensive Tests (AC: #1-#13)
  - [x] 9.1 CREATE `backend/tests/api/routes/test_upload_zip.py` for endpoint tests
  - [x] 9.2 CREATE `backend/tests/services/test_zip_extraction_service.py` for service tests
  - [x] 9.3 CREATE `backend/tests/services/test_zip_filter_service.py` for filter tests
  - [x] 9.4 TEST ZIP upload returns list of created assets
  - [x] 9.5 TEST system files (.DS_Store, __MACOSX/) are filtered
  - [x] 9.6 TEST folder structure is preserved in MinIO paths
  - [x] 9.7 TEST invalid files are skipped but extraction continues
  - [x] 9.8 TEST corrupt ZIP returns INVALID_ZIP_FILE error
  - [x] 9.9 TEST ZIP bomb protection (high compression ratio rejected)
  - [x] 9.10 TEST file count limit prevents excessive extraction
  - [x] 9.11 TEST rate limiting applies correctly
  - [x] 9.12 TEST audit logs are created for all operations
  - [x] 9.13 TEST memory usage stays bounded (streaming validation)
  - [x] 9.14 TEST tenant isolation for extracted files

- [x] Task 10: Documentation and Integration (AC: #10)
  - [x] 10.1 ADD OpenAPI documentation for ZIP upload endpoint
  - [x] 10.2 ADD example requests/responses in endpoint docstrings
  - [x] 10.3 DOCUMENT supported ZIP formats and limitations
  - [x] 10.4 VERIFY endpoint appears in `/docs` Swagger UI

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Streaming Responses:**
- Decision: FastAPI StreamingResponse for large data operations
- Use Cases: ZIP file extraction without full buffering
- Rationale: Meet NFR-P4 (no file buffering in memory), support large datasets

**Multipart Upload Support:**
- Decision: Chunked upload for files >100MB
- Implementation: Backend processes uploads, streams to MinIO
- Rationale: Large video/ZIP files for publishers (FR4), avoid memory buffering (NFR-P4)

**Performance Requirements:**
- NFR-P3: File upload operations shall not timeout for files up to 10GB
- NFR-P7: File operations shall not buffer entire files in memory (streaming design)
- NFR-P9: ZIP extraction shall process files in streaming mode without disk/RAM bottlenecks

### Existing Code Assets (REUSE from Story 3.1, 3.2)

**`backend/app/core/minio_client.py`** - MinIO operations (extend with ZIP entry streaming):
```python
# Current implementation includes:
get_minio_client()              # Singleton MinIO client
generate_object_key()           # Tenant-isolated path generation
put_object_streaming()          # Upload with checksum
delete_object()                 # Object deletion
ChecksumCalculator              # Streaming checksum wrapper

# ADD for Story 3.3:
put_object_from_stream()        # Direct streaming from file-like object
```

**`backend/app/services/asset_service.py`** - Asset upload workflow (extend):
```python
class AssetService:
    async def create_asset()       # Single file upload (reuse validation pattern)

    # ADD for Story 3.3:
    async def create_assets_from_zip()  # Batch upload from ZIP
```

**`backend/app/services/file_validation_service.py`** - File validation (reuse):
```python
validate_file()                  # Complete file validation
validate_mime_type()             # MIME type whitelist check
validate_file_size()             # Type-specific size limits
validate_magic_bytes()           # MIME spoofing prevention
get_safe_filename()              # Filename sanitization
MAGIC_SIGNATURES                 # Including ZIP: (0, b"PK\x03\x04")
```

**`backend/app/api/routes/upload.py`** - Upload endpoint pattern:
```python
@router.post("/upload")
@limiter.limit(get_dynamic_rate_limit)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session: TenantSessionDep,
    current_user: CurrentUser,
) -> AssetResponse
```

**`backend/app/models.py`** - Models and enums:
```python
class Asset                      # Asset model with tenant_id, object_key, etc.
class AssetCreate                # Pydantic model for asset creation
class AuditAction                # Enum for audit log actions
class AuditLog                   # Audit log model
```

### Previous Story Intelligence (Story 3.1, 3.2)

**Patterns Established:**
- Asset model stores `bucket`, `object_key`, `tenant_id` for MinIO reference
- Object key format: `{tenant_type}/{tenant_id}/{asset_id}/{file_name}`
- Rate limiting applied via `@limiter.limit(get_dynamic_rate_limit)` decorator
- Request object required for rate limiter: `request: Request`
- Audit logging with `AuditAction` enum and `AuditLog` model
- Error responses follow standard format with `error_code`, `message`, `details`, `request_id`
- File validation service for MIME type and size checks
- Magic bytes validation prevents MIME spoofing
- Transaction consistency: rollback operations on failure

**Learnings from Story 3.1:**
- MinIO SDK handles streaming via put_object with file-like objects
- Use `BytesIO` wrapper for in-memory streams
- Calculate checksum during read via `ChecksumCalculator` wrapper
- Audit log after successful operation, not before
- Return structured response with all metadata

**Learnings from Story 3.2:**
- Performance logging with timing metrics
- Service layer handles authorization checks
- Admin/Supervisor bypass tenant restrictions

### Git Intelligence (Recent Commits)

Recent commits show established patterns:
- `feat(story-3.2): Generate time-limited signed URLs for direct MinIO access`
- `feat(story-3.1): Implement single file upload with validation and security`
- `feat(story-2.5): Implement User Management Endpoints for Admin/Supervisor`

**Commit Format:** `feat(story-X.Y): Description`
**Branch Format:** `story/X-Y-description`

### Project Structure (UPDATE/CREATE)

**CREATE Files:**
```
backend/app/services/zip_extraction_service.py    # ZIP extraction with streaming
backend/app/services/zip_filter_service.py        # System file filtering
backend/app/schemas/zip_upload.py                 # Request/Response schemas
backend/app/alembic/versions/xxx_add_zip_upload_audit_action.py  # Migration
backend/tests/api/routes/test_upload_zip.py       # Endpoint tests
backend/tests/services/test_zip_extraction_service.py  # Service tests
backend/tests/services/test_zip_filter_service.py # Filter tests
```

**UPDATE Files:**
```
backend/app/core/config.py              # ADD ZIP upload settings
backend/app/core/minio_client.py        # ADD streaming upload from file-like object
backend/app/models.py                   # ADD ASSET_ZIP_UPLOAD to AuditAction
backend/app/services/asset_service.py   # ADD create_assets_from_zip()
backend/app/api/routes/upload.py        # ADD POST /assets/upload-zip endpoint
.env.example                            # ADD new environment variables
```

### Technical Implementation Details

**ZIP Streaming Architecture:**

The key challenge is NFR-P9 - processing ZIP files without loading them entirely into memory. Python's `zipfile` module supports this through:

1. **ZipFile with file-like object**: Accept FastAPI's `SpooledTemporaryFile` (small files in memory, large on disk)
2. **Iterate entries without extraction**: Use `zipfile.infolist()` to get entry metadata
3. **Stream each entry**: Use `zipfile.open(entry)` to get a file-like object
4. **Direct to MinIO**: Stream from ZIP entry → MinIO put_object

```python
# Streaming extraction pattern
import zipfile
from io import BytesIO

def extract_and_upload(zip_file: BinaryIO) -> list[Asset]:
    assets = []

    with zipfile.ZipFile(zip_file, 'r') as zf:
        for info in zf.infolist():
            # Skip directories
            if info.is_dir():
                continue

            # Skip system files
            if should_skip_entry(info.filename):
                continue

            # Stream entry directly to MinIO
            with zf.open(info) as entry_stream:
                # ChecksumCalculator wraps stream to calculate MD5
                checksum_stream = ChecksumCalculator(entry_stream)

                # Upload to MinIO (streaming, no full memory load)
                result = client.put_object(
                    bucket_name=bucket,
                    object_name=object_key,
                    data=checksum_stream,
                    length=info.file_size,
                    content_type=mime_type,
                )

                # Create asset metadata
                asset = create_asset_metadata(
                    object_key=object_key,
                    checksum=checksum_stream.checksum,
                    file_size=info.file_size,
                )
                assets.append(asset)

    return assets
```

**System File Filter Patterns:**

```python
# backend/app/services/zip_filter_service.py
SKIP_PATTERNS = [
    r"\.DS_Store$",           # macOS directory metadata
    r"__MACOSX/",             # macOS resource forks
    r"Thumbs\.db$",           # Windows thumbnail cache
    r"\.git/",                # Git repository data
    r"desktop\.ini$",         # Windows folder settings
    r"\.tmp$",                # Temporary files
    r"~\$",                   # Office temp files (Word, Excel)
    r"\.swp$",                # Vim swap files
    r"\.swo$",                # Vim swap files
    r"node_modules/",         # npm dependencies (if accidentally zipped)
    r"__pycache__/",          # Python cache
    r"\.pyc$",                # Python compiled files
]

def should_skip_entry(entry_name: str) -> bool:
    """Check if entry matches any skip pattern."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, entry_name, re.IGNORECASE):
            return True
    return False
```

**ZIP Bomb Protection:**

```python
# Prevent zip bombs (malicious compressed files)
MAX_COMPRESSION_RATIO = 100  # Reject if uncompressed > 100x compressed

def check_zip_bomb(info: ZipInfo) -> bool:
    """Check if entry has suspiciously high compression ratio."""
    if info.compress_size == 0:
        return True

    ratio = info.file_size / info.compress_size
    if ratio > MAX_COMPRESSION_RATIO:
        logger.warning(
            "Possible zip bomb detected",
            extra={
                "entry": info.filename,
                "compressed_size": info.compress_size,
                "uncompressed_size": info.file_size,
                "ratio": ratio,
            },
        )
        return True

    return False
```

**Response Schema:**

```python
# backend/app/schemas/zip_upload.py
from pydantic import BaseModel, Field
from app.schemas.asset import AssetResponse

class SkippedFileInfo(BaseModel):
    """Information about a skipped file."""
    file_name: str
    reason: str  # "system_file", "invalid_type", "file_too_large"

class FailedFileInfo(BaseModel):
    """Information about a failed file."""
    file_name: str
    error_code: str
    message: str

class ZipUploadResponse(BaseModel):
    """Response for ZIP archive upload."""

    extracted_count: int = Field(description="Number of files successfully extracted")
    skipped_count: int = Field(description="Number of files skipped (system files)")
    failed_count: int = Field(description="Number of files that failed validation")
    total_size_bytes: int = Field(description="Total size of extracted files")

    assets: list[AssetResponse] = Field(description="List of created assets")
    skipped_files: list[SkippedFileInfo] = Field(description="Files skipped during extraction")
    failed_files: list[FailedFileInfo] = Field(description="Files that failed validation")

    class Config:
        json_schema_extra = {
            "example": {
                "extracted_count": 15,
                "skipped_count": 3,
                "failed_count": 1,
                "total_size_bytes": 52428800,
                "assets": [{"id": "uuid", "file_name": "document.pdf", "...": "..."}],
                "skipped_files": [
                    {"file_name": ".DS_Store", "reason": "system_file"},
                    {"file_name": "__MACOSX/._document.pdf", "reason": "system_file"}
                ],
                "failed_files": [
                    {"file_name": "virus.exe", "error_code": "INVALID_FILE_TYPE", "message": "..."}
                ]
            }
        }
```

**API Endpoint:**

```python
# backend/app/api/routes/upload.py (additions)
@router.post(
    "/upload-zip",
    response_model=ZipUploadResponse,
    status_code=201,
    summary="Upload ZIP archive for extraction",
    description="""
    Upload a ZIP archive and automatically extract its contents.

    **Behavior:**
    - Extracts all files from the ZIP archive
    - Filters system files (.DS_Store, __MACOSX/, Thumbs.db, .git/)
    - Validates each file for type and size
    - Preserves folder structure as MinIO prefixes
    - Creates asset metadata for each extracted file
    - Continues extraction even if some files fail

    **Limits:**
    - ZIP file: max 10GB
    - Total extracted: max 50GB
    - Max files: 1000
    - Per-file limits: same as single upload

    **Returns:**
    - 201 Created with extraction results
    - 400 Bad Request with INVALID_ZIP_FILE if not a valid ZIP
    - 429 Too Many Requests if rate limit exceeded
    """,
)
@limiter.limit(get_dynamic_rate_limit)
async def upload_zip(
    request: Request,
    file: UploadFile = File(..., description="ZIP archive to extract"),
    session: TenantSessionDep = None,
    current_user: CurrentUser = None,
) -> ZipUploadResponse:
    """Upload and extract ZIP archive."""
    request_id = getattr(request.state, "request_id", None)
    ip_address = get_client_ip(request)

    # Validate ZIP format
    if not file.content_type in ("application/zip", "application/x-zip-compressed"):
        raise InvalidFileTypeError(
            mime_type=file.content_type,
            allowed_types=["application/zip"],
            request_id=request_id,
        )

    asset_service = AssetService(session=session, current_user=current_user)

    result = await asset_service.create_assets_from_zip(
        zip_file=file.file,
        ip_address=ip_address,
        request_id=request_id,
    )

    return ZipUploadResponse(
        extracted_count=result.extracted_count,
        skipped_count=result.skipped_count,
        failed_count=result.failed_count,
        total_size_bytes=result.total_size_bytes,
        assets=result.assets,
        skipped_files=result.skipped_files,
        failed_files=result.failed_files,
    )
```

### Dependencies

**Already Available (from pyproject.toml):**
```
fastapi[standard]     # Includes UploadFile, SpooledTemporaryFile
python-multipart      # Multipart form data parsing
minio>=7.2.0,<8.0.0   # MinIO SDK for object storage
```

**Python Standard Library (no install needed):**
```
zipfile               # ZIP archive handling (streaming support)
io.BytesIO            # In-memory binary streams
re                    # Regular expressions for pattern matching
```

**No New Dependencies Required**

### Git Workflow

**Branch:** `story/3-3-zip-archive-upload`

**Commit Pattern:**
```
feat(story-3.3): Implement ZIP archive upload with streaming extraction
```

### Testing Standards

**Test Commands:**
```bash
# Run ZIP upload tests
uv run pytest backend/tests/api/routes/test_upload_zip.py -v

# Run service tests
uv run pytest backend/tests/services/test_zip_extraction_service.py -v
uv run pytest backend/tests/services/test_zip_filter_service.py -v

# Run with coverage
uv run pytest backend/tests/ -v -k "zip" --cov=backend/app

# Test memory usage (manual verification)
# Monitor memory during upload of 1GB+ ZIP file
```

**Test Fixtures:**

```python
# backend/tests/conftest.py (additions)
import io
import zipfile
import pytest

@pytest.fixture
def sample_zip_file() -> io.BytesIO:
    """Create a sample ZIP file for testing."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('document.pdf', b'%PDF-1.4 test content...')
        zf.writestr('images/photo.jpg', b'\xff\xd8\xff test jpeg...')
        zf.writestr('.DS_Store', b'system file content')
        zf.writestr('__MACOSX/._document.pdf', b'resource fork')
    buffer.seek(0)
    return buffer

@pytest.fixture
def zip_with_invalid_files() -> io.BytesIO:
    """Create ZIP with files that should fail validation."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr('valid.pdf', b'%PDF-1.4 valid pdf')
        zf.writestr('invalid.exe', b'MZ executable content')
    buffer.seek(0)
    return buffer

@pytest.fixture
def nested_folder_zip() -> io.BytesIO:
    """Create ZIP with nested folder structure."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr('books/grade-8/math/chapter1.pdf', b'%PDF-1.4 content')
        zf.writestr('books/grade-8/math/chapter2.pdf', b'%PDF-1.4 content')
        zf.writestr('books/grade-8/science/intro.pdf', b'%PDF-1.4 content')
    buffer.seek(0)
    return buffer
```

**Key Test Cases:**

```python
# backend/tests/api/routes/test_upload_zip.py

class TestZipUploadEndpoint:
    def test_zip_upload_extracts_valid_files(
        self, authenticated_client, sample_zip_file
    ):
        """POST /assets/upload-zip extracts and creates assets."""
        response = authenticated_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("archive.zip", sample_zip_file, "application/zip")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["extracted_count"] >= 1
        assert len(data["assets"]) == data["extracted_count"]

    def test_zip_upload_filters_system_files(
        self, authenticated_client, sample_zip_file
    ):
        """System files are skipped during extraction."""
        response = authenticated_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("archive.zip", sample_zip_file, "application/zip")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["skipped_count"] >= 2  # .DS_Store, __MACOSX/
        skipped_names = [f["file_name"] for f in data["skipped_files"]]
        assert ".DS_Store" in skipped_names

    def test_zip_upload_preserves_folder_structure(
        self, authenticated_client, nested_folder_zip
    ):
        """Folder structure is preserved as MinIO prefixes."""
        response = authenticated_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("archive.zip", nested_folder_zip, "application/zip")},
        )
        assert response.status_code == 201
        data = response.json()
        # Check that paths are preserved
        object_keys = [a["object_key"] for a in data["assets"]]
        assert any("books/grade-8/math" in key for key in object_keys)

    def test_zip_upload_continues_on_invalid_files(
        self, authenticated_client, zip_with_invalid_files
    ):
        """Extraction continues even when some files fail validation."""
        response = authenticated_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("archive.zip", zip_with_invalid_files, "application/zip")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["extracted_count"] >= 1  # Valid files extracted
        assert data["failed_count"] >= 1     # Invalid files reported

    def test_zip_upload_rejects_non_zip(self, authenticated_client):
        """Non-ZIP files are rejected."""
        response = authenticated_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("notzip.txt", b"plain text", "text/plain")},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error_code"] == "INVALID_FILE_TYPE"

    def test_zip_upload_rejects_corrupt_zip(self, authenticated_client):
        """Corrupt ZIP files are rejected."""
        corrupt_zip = io.BytesIO(b"PK\x03\x04corrupted garbage data")
        response = authenticated_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("corrupt.zip", corrupt_zip, "application/zip")},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error_code"] == "INVALID_ZIP_FILE"

    def test_zip_upload_creates_audit_logs(
        self, authenticated_client, sample_zip_file, session
    ):
        """ZIP upload creates audit logs."""
        response = authenticated_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("archive.zip", sample_zip_file, "application/zip")},
        )
        assert response.status_code == 201

        from app.models import AuditLog, AuditAction
        from sqlmodel import select

        audit_logs = session.exec(
            select(AuditLog).where(
                AuditLog.action == AuditAction.ASSET_ZIP_UPLOAD
            )
        ).all()
        assert len(audit_logs) >= 1

    def test_zip_upload_enforces_rate_limit(
        self, authenticated_student_client, sample_zip_file
    ):
        """Rate limiting applies to ZIP uploads."""
        # Students have 100 req/hour limit
        # This test may need adjustment based on rate limit state
        response = authenticated_student_client.post(
            "/api/v1/assets/upload-zip",
            files={"file": ("archive.zip", sample_zip_file, "application/zip")},
        )
        # Either succeeds or rate limited
        assert response.status_code in (201, 429)
```

### Security Considerations

**Critical Security Requirements:**
- ZIP bomb protection via compression ratio checks
- System file filtering prevents execution of hidden files
- Per-file MIME type and magic bytes validation
- Tenant isolation enforced for all extracted assets
- Path traversal prevention (sanitize all filenames)
- File count limits prevent resource exhaustion

**OWASP Compliance:**
- A1:2021 - Broken Access Control: Tenant isolation for all extracted files
- A3:2021 - Injection: Filename sanitization, no path traversal
- A4:2021 - Insecure Design: ZIP bomb protection, resource limits
- A5:2021 - Security Misconfiguration: Explicit file type whitelist
- A7:2021 - Identification: JWT required for endpoint access
- A9:2021 - Security Logging: Audit logs for all extracted files

**Path Traversal Prevention:**
```python
# Entries like "../../../etc/passwd" must be blocked
def sanitize_zip_path(entry_name: str) -> str:
    """Remove path traversal attempts from ZIP entry names."""
    # Normalize path separators
    safe_path = entry_name.replace("\\", "/")

    # Remove any parent directory references
    parts = safe_path.split("/")
    safe_parts = [p for p in parts if p and p != ".."]

    return "/".join(safe_parts)
```

### Integration Notes

**This story enables:**
- Epic 6: Asset Discovery (search across ZIP-uploaded assets)
- Epic 9: Frontend bulk upload UI (drag-drop ZIP files)
- Publishers can efficiently upload entire book packages

**Backward Compatibility:**
- New endpoint, no breaking changes
- Existing single file upload unchanged
- Rate limiting applies consistently

### Performance Optimization

**Streaming Performance (NFR-P9):**
- ZipFile.open() returns file-like object for streaming
- ChecksumCalculator wraps stream without full buffering
- MinIO put_object accepts streaming data
- Memory usage bounded regardless of file size

**Batch Operations:**
- Batch metadata creation reduces database round-trips
- Single transaction for all assets in ZIP
- Audit logs batched where possible

**Resource Limits:**
- MAX_ZIP_EXTRACTED_FILES = 1000 prevents excessive iteration
- MAX_EXTRACTED_TOTAL_SIZE prevents disk exhaustion
- Compression ratio check prevents CPU abuse

### Error Handling

**Error Response Format (consistent with existing):**
```python
class InvalidZipError(BaseApplicationException):
    """Raised when ZIP file is invalid or corrupt."""

    def __init__(
        self,
        message: str = "Invalid or corrupt ZIP file",
        details: dict | None = None,
        request_id: str | None = None,
    ):
        super().__init__(
            status_code=400,
            error_code="INVALID_ZIP_FILE",
            message=message,
            details=details,
            request_id=request_id,
        )

class ZipBombError(BaseApplicationException):
    """Raised when ZIP file appears to be a zip bomb."""

    def __init__(
        self,
        entry_name: str,
        compression_ratio: float,
        request_id: str | None = None,
    ):
        super().__init__(
            status_code=400,
            error_code="ZIP_BOMB_DETECTED",
            message="File has suspiciously high compression ratio",
            details={
                "entry": entry_name,
                "compression_ratio": compression_ratio,
            },
            request_id=request_id,
        )
```

## References

- [Source: docs/epics.md#Story-3.3] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Streaming-Responses] - Streaming architecture
- [Source: docs/architecture/implementation-patterns-consistency-rules.md] - Code patterns
- [Source: docs/sprint-artifacts/3-1-implement-single-file-upload-with-progress-tracking.md] - Upload patterns
- [Source: docs/sprint-artifacts/3-2-generate-time-limited-signed-urls-for-direct-minio-access.md] - MinIO patterns
- [Python zipfile documentation](https://docs.python.org/3/library/zipfile.html) - Streaming support

## Dev Agent Record

### Context Reference

Story 3.3 implementation - third story in Epic 3 (Core Asset Upload & Storage).
Implements ZIP archive upload with streaming extraction for bulk asset uploads.
Builds on upload patterns from Story 3.1, extends AssetService with batch operations.
Critical for publisher workflows uploading entire book packages.
NFR-P9 compliance requires streaming without memory buffering.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

**Implementation completed 2025-12-17**

All 13 Acceptance Criteria fully implemented:
- AC #1: POST /api/v1/assets/upload-zip endpoint accepts ZIP archives ✓
- AC #2: ZIP file size validation (max 10GB) ✓
- AC #3: Streaming extraction without full memory load ✓
- AC #4: System files filtered (.DS_Store, __MACOSX/, Thumbs.db, .git/, desktop.ini) ✓
- AC #5: Per-file validation against MIME whitelist ✓
- AC #6: Files uploaded to MinIO at `/{tenant_type}/{tenant_id}/{asset_id}/{file_name}` ✓
- AC #7: Folder structure preserved as MinIO prefixes ✓
- AC #8: Asset metadata created for each extracted file ✓
- AC #9: Streaming mode (no disk buffering) ✓
- AC #10: Response includes extraction counts and asset list ✓
- AC #11: All operations logged to audit logs ✓
- AC #12: Failed files skipped, extraction continues ✓
- AC #13: Invalid ZIP returns INVALID_ZIP_FILE error ✓

**Test Coverage:**
- 75 total tests (42 filter service + 17 extraction service + 16 API tests)
- All tests passing

**Security Features Implemented:**
- ZIP bomb protection (compression ratio > 100x rejected)
- Path traversal prevention (../ patterns blocked)
- System file filtering (case-insensitive)
- Role-based access (publishers/teachers only)
- Tenant isolation for all extracted assets

### File List

**New Files Created:**
- `backend/app/services/zip_filter_service.py` - System file filtering
- `backend/app/services/zip_extraction_service.py` - ZIP extraction with streaming
- `backend/app/schemas/zip_upload.py` - Response schemas
- `backend/app/alembic/versions/add_zip_upload_audit_action.py` - Migration
- `backend/tests/services/test_zip_filter_service.py` - 42 unit tests
- `backend/tests/services/test_zip_extraction_service.py` - 17 unit tests
- `backend/tests/api/routes/test_upload_zip.py` - 16 API tests

**Modified Files:**
- `backend/app/core/config.py` - Added ZIP upload settings
- `backend/app/models.py` - Added ASSET_ZIP_UPLOAD to AuditAction enum
- `backend/app/services/asset_service.py` - Added create_assets_from_zip() method
- `backend/app/api/routes/upload.py` - Added POST /assets/upload-zip endpoint
- `.env.example` - Documented new environment variables
