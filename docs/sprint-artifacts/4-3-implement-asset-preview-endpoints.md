# Story 4.3: Implement Asset Preview Endpoints

Status: done

## Story

As a user,
I want to preview images, videos, and audio before downloading,
So that I can verify it's the correct file (FR50).

## Acceptance Criteria

1. **Given** I am viewing an asset in the web interface, **When** I request a preview for an image asset, **Then** the API returns a signed URL to the image in MinIO

2. **Given** the signed URL is returned, **When** the browser loads the URL, **Then** the image is displayed inline in the browser

3. **Given** I request a preview for a video asset, **When** the API processes my request, **Then** the API returns a signed stream URL with HTTP Range support

4. **Given** the video stream URL is loaded, **When** a video player component loads the stream URL, **Then** the video player displays the first frame as thumbnail

5. **Given** I request a preview for an audio asset, **When** the API processes my request, **Then** the API returns a signed stream URL

6. **Given** the audio stream URL is returned, **When** an audio player component is rendered, **Then** the audio player allows playing the audio inline

7. **Given** I request a preview for a PDF, **When** the API processes my request, **Then** the API returns a signed URL and the PDF renders in an iframe or PDF viewer component

8. **Given** preview URLs are generated, **When** checking expiration, **Then** preview URLs have 1-hour TTL and are regenerated as needed

9. **Given** I request a preview for an unsupported file type, **When** the API processes my request, **Then** I receive a response indicating no preview is available with file metadata only

10. **Given** I request a preview for an asset I don't have access to, **When** the API checks permissions, **Then** I receive 403 Forbidden with error_code "PERMISSION_DENIED"

## Tasks / Subtasks

- [x] Task 1: Create Preview Endpoint (AC: #1, #2, #3, #4, #5, #6, #7, #8)
  - [x] 1.1 CREATE `GET /api/v1/assets/{asset_id}/preview` endpoint in `backend/app/api/routes/preview.py`
  - [x] 1.2 IMPLEMENT preview type detection based on MIME type
  - [x] 1.3 GENERATE appropriate signed URL (image/pdf: download URL, video/audio: stream URL)
  - [x] 1.4 RETURN `PreviewResponse` with URL, type, and metadata
  - [x] 1.5 ADD rate limiting using `@limiter.limit(get_dynamic_rate_limit)` decorator
  - [x] 1.6 ADD router to `backend/app/api/main.py`

- [x] Task 2: Create Preview Response Schema (AC: #1, #8, #9)
  - [x] 2.1 CREATE `backend/app/schemas/preview.py` with `PreviewResponse` schema
  - [x] 2.2 ADD fields: `preview_url: Optional[str]`, `preview_type: PreviewType`, `expires_at: Optional[datetime]`, `mime_type: str`, `file_name: str`, `file_size: int`, `supports_inline: bool`
  - [x] 2.3 CREATE `PreviewType` enum: `image`, `video`, `audio`, `pdf`, `document`, `unsupported`
  - [x] 2.4 ADD OpenAPI documentation and example responses

- [x] Task 3: Implement Preview Type Detection (AC: #1, #3, #5, #7, #9)
  - [x] 3.1 CREATE helper function `get_preview_type(mime_type: str) -> PreviewType`
  - [x] 3.2 MAP image MIME types (image/jpeg, image/png, image/gif, image/webp, image/svg+xml) to `image`
  - [x] 3.3 MAP video MIME types (video/mp4, video/webm, video/ogg) to `video`
  - [x] 3.4 MAP audio MIME types (audio/mpeg, audio/mp3, audio/wav, audio/ogg) to `audio`
  - [x] 3.5 MAP PDF MIME type (application/pdf) to `pdf`
  - [x] 3.6 MAP document types (application/json, text/plain, text/html) to `document`
  - [x] 3.7 RETURN `unsupported` for all other MIME types

- [x] Task 4: Implement Preview URL Generation (AC: #1, #2, #3, #4, #5, #6, #7, #8)
  - [x] 4.1 FOR image/pdf: Use `generate_presigned_download_url()` with Content-Disposition: inline
  - [x] 4.2 FOR video/audio: Use `generate_presigned_download_url()` (streaming handled by browser)
  - [x] 4.3 FOR document: Use `generate_presigned_download_url()` for inline viewing
  - [x] 4.4 FOR unsupported: Return null URL with metadata only
  - [x] 4.5 SET 1-hour TTL for all preview URLs

- [x] Task 5: Add Preview Audit Action (AC: #10)
  - [x] 5.1 ADD `PREVIEW` to `AuditAction` enum in `backend/app/models.py`
  - [x] 5.2 CREATE Alembic migration for new enum value
  - [x] 5.3 LOG preview requests in audit log with user_id, asset_id, preview_type
  - [x] 5.4 VERIFY audit log includes IP address and timestamp

- [x] Task 6: Write Comprehensive Tests (AC: #1-#10)
  - [x] 6.1 CREATE `backend/tests/api/routes/test_preview.py` for endpoint tests
  - [x] 6.2 TEST preview returns signed URL for image assets
  - [x] 6.3 TEST preview returns signed URL for video assets
  - [x] 6.4 TEST preview returns signed URL for audio assets
  - [x] 6.5 TEST preview returns signed URL for PDF assets
  - [x] 6.6 TEST preview returns null URL for unsupported types
  - [x] 6.7 TEST permission denied for unauthorized users (403)
  - [x] 6.8 TEST asset not found for non-existent assets (404)
  - [x] 6.9 TEST Admin can preview any tenant's asset
  - [x] 6.10 TEST audit log is created with PREVIEW action
  - [x] 6.11 TEST rate limiting applies correctly

- [x] Task 7: Documentation and Integration (AC: #1, #8)
  - [x] 7.1 ADD OpenAPI documentation for preview endpoint
  - [x] 7.2 ADD example requests/responses in endpoint docstrings
  - [x] 7.3 VERIFY endpoint appears in `/docs` Swagger UI
  - [x] 7.4 DOCUMENT supported preview types and MIME mappings
  - [x] 7.5 DOCUMENT frontend integration patterns for each preview type

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Signed URL Generation:**
- Decision: HMAC-SHA256 signatures generated by backend, validated by MinIO
- Default TTL: 1 hour for preview URLs
- Zero-proxy Architecture: Browser loads preview directly from MinIO

**Performance Requirements:**
- NFR-P2: Signed URL generation shall complete within 100ms
- NFR-P7: File operations shall not buffer entire files in memory

**Frontend Integration:**
- Images: Direct `<img src={preview_url} />` rendering
- Videos: HTML5 `<video>` element with controls
- Audio: HTML5 `<audio>` element with controls
- PDF: `<iframe>` or PDF.js viewer
- Documents: Code viewer or raw text display

### Preview Type Mapping

| MIME Type | Preview Type | Browser Rendering | Frontend Component |
|-----------|--------------|-------------------|-------------------|
| image/jpeg, image/png, image/gif, image/webp, image/svg+xml | `image` | `<img>` tag | ImagePreview |
| video/mp4, video/webm, video/ogg | `video` | `<video>` tag | VideoPlayer |
| audio/mpeg, audio/mp3, audio/wav, audio/ogg | `audio` | `<audio>` tag | AudioPlayer |
| application/pdf | `pdf` | `<iframe>` or PDF.js | PDFViewer |
| application/json, text/plain, text/html | `document` | Code viewer | DocumentViewer |
| Other | `unsupported` | Download link only | FileDownload |

### Existing Code Assets (REUSE from Stories 3.2, 4.1, 4.2)

**`backend/app/services/signed_url_service.py`** - SignedURLService:
```python
def generate_download_url(self, asset_id: UUID) -> tuple[str, datetime]:
    """Used for image, PDF, document previews."""

def generate_stream_url(self, asset_id: UUID) -> tuple[str, datetime]:
    """Used for video, audio previews (HTTP Range support)."""
```

**`backend/app/core/minio_client.py`** - MinIO operations:
```python
generate_presigned_download_url(bucket, object_key, expires_seconds)
```

### Previous Story Intelligence (Stories 4.1, 4.2)

**Patterns Established:**
- Download endpoint with file metadata (Story 4.1)
- Streaming endpoint with MIME type validation (Story 4.2)
- Permission validation and audit logging
- Rate limiting patterns

**Key Insight:**
Preview combines download (images, PDFs) and streaming (video, audio) patterns.
The preview endpoint should:
1. Detect asset type from MIME type
2. Choose appropriate URL generation method
3. Return metadata useful for frontend rendering

### Git Intelligence (Recent Commits)

**Commit Format:** `feat(story-X.Y): Description`
**Branch Format:** `story/X-Y-description`

### Project Structure (UPDATE/CREATE)

**CREATE Files:**
```
backend/app/api/routes/preview.py            # Preview endpoint
backend/app/schemas/preview.py                # Preview response schema
backend/tests/api/routes/test_preview.py      # Preview endpoint tests
backend/app/alembic/versions/xxx_add_preview_audit_action.py  # Migration
```

**UPDATE Files:**
```
backend/app/api/main.py                      # ADD preview router
backend/app/models.py                        # ADD PREVIEW to AuditAction
```

### Technical Implementation Details

**Preview Type Enum:**
```python
# backend/app/schemas/preview.py
from enum import Enum

class PreviewType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    DOCUMENT = "document"
    UNSUPPORTED = "unsupported"
```

**Preview Response Schema:**
```python
# backend/app/schemas/preview.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PreviewResponse(BaseModel):
    """Response schema for asset preview endpoint."""

    preview_url: Optional[str] = Field(
        default=None,
        description="Presigned URL for preview (null for unsupported types)"
    )
    preview_type: PreviewType = Field(
        description="Type of preview: image, video, audio, pdf, document, unsupported"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="URL expiration time (null for unsupported types)"
    )
    mime_type: str = Field(description="Original MIME type of the asset")
    file_name: str = Field(description="Original file name")
    file_size: int = Field(description="File size in bytes")
    supports_inline: bool = Field(
        description="Whether the asset can be previewed inline in browser"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "preview_url": "https://minio.example.com/assets/...",
                "preview_type": "image",
                "expires_at": "2025-12-17T12:00:00Z",
                "mime_type": "image/jpeg",
                "file_name": "photo.jpg",
                "file_size": 1234567,
                "supports_inline": True,
            }
        }
```

**Preview Type Detection:**
```python
# backend/app/api/routes/preview.py

IMAGE_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif",
    "image/webp", "image/svg+xml", "image/bmp"
}
VIDEO_MIME_TYPES = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
AUDIO_MIME_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/webm", "audio/aac"}
PDF_MIME_TYPES = {"application/pdf"}
DOCUMENT_MIME_TYPES = {"application/json", "text/plain", "text/html", "text/css", "text/javascript"}

def get_preview_type(mime_type: str) -> PreviewType:
    """Determine preview type from MIME type."""
    if mime_type in IMAGE_MIME_TYPES:
        return PreviewType.IMAGE
    elif mime_type in VIDEO_MIME_TYPES:
        return PreviewType.VIDEO
    elif mime_type in AUDIO_MIME_TYPES:
        return PreviewType.AUDIO
    elif mime_type in PDF_MIME_TYPES:
        return PreviewType.PDF
    elif mime_type in DOCUMENT_MIME_TYPES:
        return PreviewType.DOCUMENT
    else:
        return PreviewType.UNSUPPORTED
```

**Preview Endpoint:**
```python
# backend/app/api/routes/preview.py
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from app.api.deps import CurrentUser, SessionDep
from app.middleware.rate_limit import limiter, get_dynamic_rate_limit
from app.schemas.preview import PreviewResponse, PreviewType
from app.services.signed_url_service import SignedURLService
from app.repositories.asset_repository import AssetRepository
from app.core.exceptions import AssetNotFoundError

router = APIRouter(prefix="/assets", tags=["preview"])

@router.get(
    "/{asset_id}/preview",
    response_model=PreviewResponse,
)
@limiter.limit(get_dynamic_rate_limit)
async def preview_asset(
    request: Request,
    asset_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> PreviewResponse:
    """
    Get preview URL for an asset.

    Returns a presigned URL appropriate for inline preview based on asset type:
    - **Images**: Direct URL for `<img>` tag
    - **Videos**: Stream URL with HTTP Range support for `<video>` tag
    - **Audio**: Stream URL for `<audio>` tag
    - **PDFs**: URL for iframe or PDF viewer
    - **Documents**: URL for code/text viewer
    - **Unsupported**: Returns null URL with file metadata only

    Preview URLs are valid for 1 hour.

    **Permission:** User must own the asset or be Admin/Supervisor.
    """
    asset_repo = AssetRepository(session)
    asset = asset_repo.get_by_id(asset_id)

    if not asset:
        raise AssetNotFoundError(
            message="Asset not found",
            details={"asset_id": str(asset_id)},
        )

    preview_type = get_preview_type(asset.mime_type)
    supports_inline = preview_type != PreviewType.UNSUPPORTED

    preview_url = None
    expires_at = None

    if supports_inline:
        service = SignedURLService(session=session, current_user=current_user)
        # All preview types use download URL - browser handles rendering
        preview_url, expires_at = service.generate_download_url(asset_id)

        # Log preview action
        service._create_audit_log(asset.id, AuditAction.PREVIEW)

    return PreviewResponse(
        preview_url=preview_url,
        preview_type=preview_type,
        expires_at=expires_at,
        mime_type=asset.mime_type,
        file_name=asset.file_name,
        file_size=asset.file_size_bytes,
        supports_inline=supports_inline,
    )
```

### Content-Disposition Headers

**Inline vs Attachment:**
- Preview URLs should use `Content-Disposition: inline` to display in browser
- MinIO presigned URLs inherit object metadata
- Can set Content-Disposition at upload time or use response-content-disposition query param

**MinIO Presigned URL with Content-Disposition:**
```python
# For inline preview
url = client.presigned_get_object(
    bucket_name=bucket,
    object_name=object_key,
    expires=timedelta(hours=1),
    response_headers={
        "response-content-disposition": f"inline; filename=\"{file_name}\""
    }
)
```

### Dependencies

**Already Available:**
```
minio>=7.2.0,<8.0.0  # MinIO SDK
fastapi[standard]     # API framework
slowapi                # Rate limiting
```

**No New Dependencies Required**

### Git Workflow

**Branch:** `story/4-3-asset-preview`

**Commit Pattern:**
```
feat(story-4.3): Implement asset preview endpoints
```

### Testing Standards

**Test Commands:**
```bash
# Run preview tests
uv run pytest backend/tests/api/routes/test_preview.py -v

# Run with coverage
uv run pytest backend/tests/ -v -k "preview" --cov=backend/app
```

**Key Test Cases:**
```python
class TestPreviewEndpoint:
    def test_preview_image_returns_signed_url(self, authenticated_client, image_asset):
        """GET /assets/{id}/preview returns URL for image."""
        response = authenticated_client.get(f"/api/v1/assets/{image_asset.id}/preview")
        assert response.status_code == 200
        data = response.json()
        assert data["preview_type"] == "image"
        assert data["preview_url"] is not None
        assert data["supports_inline"] is True

    def test_preview_video_returns_signed_url(self, authenticated_client, video_asset):
        """GET /assets/{id}/preview returns URL for video."""

    def test_preview_unsupported_returns_null_url(self, authenticated_client, zip_asset):
        """GET /assets/{id}/preview returns null URL for unsupported type."""
        response = authenticated_client.get(f"/api/v1/assets/{zip_asset.id}/preview")
        data = response.json()
        assert data["preview_type"] == "unsupported"
        assert data["preview_url"] is None
        assert data["supports_inline"] is False

    def test_preview_permission_denied(self, tenant_a_client, tenant_b_asset):
        """GET /assets/{id}/preview returns 403 for other tenant's asset."""

    def test_preview_audit_log_created(self, authenticated_client, image_asset, session):
        """Preview creates audit log with PREVIEW action."""
```

### Security Considerations

**Critical Security Requirements:**
- Permission validation before URL generation
- 1-hour TTL limits exposure window
- Audit logging for all preview operations
- No preview for assets user doesn't own (tenant isolation)

### Integration Notes

**This story enables:**
- Story 6.3: Asset library with visual previews
- Story 9.4: Asset browser with previews
- Frontend preview modal components

**Frontend Integration Example:**
```tsx
// React component example
const AssetPreview: React.FC<{ assetId: string }> = ({ assetId }) => {
  const { data } = useQuery(['preview', assetId], () => getPreview(assetId));

  if (!data?.supports_inline) {
    return <DownloadButton assetId={assetId} />;
  }

  switch (data.preview_type) {
    case 'image':
      return <img src={data.preview_url} alt={data.file_name} />;
    case 'video':
      return <video src={data.preview_url} controls />;
    case 'audio':
      return <audio src={data.preview_url} controls />;
    case 'pdf':
      return <iframe src={data.preview_url} />;
    case 'document':
      return <CodeViewer url={data.preview_url} />;
  }
};
```

## References

- [Source: docs/epics.md#Story-4.3] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Frontend-Architecture] - Frontend component patterns
- [Source: docs/sprint-artifacts/4-1-implement-asset-download-with-signed-urls.md] - Download patterns
- [Source: docs/sprint-artifacts/4-2-implement-video-and-audio-streaming-with-http-range-support.md] - Streaming patterns

## Dev Agent Record

### Context Reference

Story 4.3 implementation - third story in Epic 4 (Asset Download & Streaming).
Implements unified preview endpoint supporting images, video, audio, PDF, and documents.
Combines download and streaming patterns from Stories 4.1 and 4.2.
Foundation for frontend asset library and preview components.

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
