# Story 3.4: Implement File Type and Size Validation

Status: done

## Story

As a system,
I want to validate all uploaded files for type and size with comprehensive security checks,
So that malicious or inappropriate files are rejected (FR9).

## Context

**Note:** Basic file validation was implemented in Story 3.1 as part of the upload flow. Story 3.4 enhances this foundation with:
- File extension validation (cross-check Content-Type vs extension)
- Validation rules API endpoint for frontend pre-flight checks
- Audio file size limits
- Dangerous filename pattern detection
- Enhanced magic bytes signatures
- Comprehensive validation test coverage

## Acceptance Criteria

1. **Given** a file is being uploaded, **When** the upload API receives the file, **Then** the file MIME type is extracted from both the Content-Type header AND validated against the file extension

2. **Given** the Content-Type and file extension, **When** validation occurs, **Then** the system cross-validates that they match (prevents Content-Type spoofing)

3. **Given** the MIME type whitelist, **When** validation occurs, **Then** allowed MIME types include: application/pdf, video/mp4, video/webm, audio/mp3, audio/wav, image/jpeg, image/png, image/gif, application/zip, application/json (already configured)

4. **Given** an upload with a MIME type not in the allowed list, **When** validation fails, **Then** upload is rejected with 400 Bad Request and error_code "INVALID_FILE_TYPE"

5. **Given** file size limits, **When** validation occurs, **Then** limits are enforced: max 10GB for videos, max 500MB for images, max 100MB for audio, max 5GB for other files

6. **Given** an upload that exceeds size limits, **When** validation fails, **Then** upload is rejected with 400 Bad Request and error_code "FILE_TOO_LARGE"

7. **Given** validation fails, **When** the error is returned, **Then** error includes helpful messages like "File type 'application/exe' is not allowed. Supported types: pdf, mp4, mp3, jpg, png, zip"

8. **Given** the frontend needs validation rules, **When** it calls GET `/api/v1/upload/validation-rules`, **Then** it receives allowed types, size limits per type, and extension mappings

9. **Given** a file with dangerous patterns, **When** validation occurs, **Then** files matching dangerous patterns are rejected: double extensions (.pdf.exe), null bytes, path separators, unicode tricks

10. **Given** a file upload, **When** magic bytes validation occurs, **Then** additional signatures are checked for: SVG (XSS risk), HTML (XSS risk), executable formats (PE/ELF/Mach-O)

11. **Given** all validation passes, **When** the upload proceeds, **Then** validation completes within 50ms for files up to 100MB

## Tasks / Subtasks

- [x] Task 1: Add Audio File Size Configuration (AC: #5)
  - [x] 1.1 UPDATE `backend/app/core/config.py` to add `MAX_FILE_SIZE_AUDIO: int = 100 * 1024 * 1024` (100MB)
  - [x] 1.2 UPDATE `get_size_limit_for_mime_type()` in `file_validation_service.py` to return audio limit for `audio/*` types
  - [x] 1.3 DOCUMENT audio size limit in `.env.example`

- [x] Task 2: Implement File Extension Validation (AC: #1, #2)
  - [x] 2.1 CREATE extension-to-MIME type mapping dictionary in `file_validation_service.py`
  - [x] 2.2 IMPLEMENT `validate_extension_matches_mime()` function
  - [x] 2.3 ADD extension extraction from filename
  - [x] 2.4 IMPLEMENT cross-validation between Content-Type and extension
  - [x] 2.5 REJECT files where extension doesn't match Content-Type (e.g., .exe with application/pdf)
  - [x] 2.6 UPDATE `validate_file()` to include extension check

- [x] Task 3: Implement Dangerous Pattern Detection (AC: #9)
  - [x] 3.1 CREATE `validate_dangerous_patterns()` function in `file_validation_service.py`
  - [x] 3.2 DETECT double extensions: `.pdf.exe`, `.jpg.php`, `.png.js`
  - [x] 3.3 DETECT null bytes in filename: `file.pdf\x00.exe`
  - [x] 3.4 DETECT path separators in filename (already in get_safe_filename, ensure validation rejects)
  - [x] 3.5 DETECT unicode tricks: right-to-left override (U+202E), zero-width chars
  - [x] 3.6 ADD `DANGEROUS_PATTERN_DETECTED` error code to exceptions
  - [x] 3.7 UPDATE `validate_file()` to include dangerous pattern check

- [x] Task 4: Enhance Magic Bytes Signatures (AC: #10)
  - [x] 4.1 ADD SVG detection in `MAGIC_SIGNATURES`: check for `<?xml` or `<svg` prefix
  - [x] 4.2 ADD HTML detection: `<!DOCTYPE`, `<html`, `<HTML`
  - [x] 4.3 ADD Windows PE executable detection: `MZ` header (bytes 0-1)
  - [x] 4.4 ADD Linux ELF executable detection: `\x7fELF` header
  - [x] 4.5 ADD Mach-O executable detection: `\xfe\xed\xfa\xce` and `\xfe\xed\xfa\xcf`
  - [x] 4.6 CREATE `validate_not_executable()` function that rejects these signatures
  - [x] 4.7 UPDATE `validate_file()` to check for executable formats

- [x] Task 5: Create Validation Rules API Endpoint (AC: #8)
  - [x] 5.1 CREATE `backend/app/schemas/validation_rules.py` with response schema
  - [x] 5.2 CREATE `backend/app/api/routes/validation.py` with `GET /upload/validation-rules`
  - [x] 5.3 RETURN allowed MIME types list
  - [x] 5.4 RETURN size limits per category (video, image, audio, default)
  - [x] 5.5 RETURN extension-to-MIME mapping for frontend validation
  - [x] 5.6 REGISTER router in `backend/app/api/main.py`
  - [x] 5.7 ADD OpenAPI documentation for endpoint

- [x] Task 6: Improve Error Messages (AC: #7)
  - [x] 6.1 UPDATE `InvalidFileTypeError` to include human-readable type suggestions
  - [x] 6.2 ADD category-based messages: "For videos, use: MP4, WebM. For images: JPEG, PNG, GIF, WebP"
  - [x] 6.3 ADD extension hints: "Rename your file with .pdf extension for PDF files"
  - [x] 6.4 UPDATE `FileTooLargeError` to include limit and type category
  - [x] 6.5 CREATE `DangerousFileError` exception for pattern violations

- [x] Task 7: Update Existing Validation Integration (AC: #1-#6)
  - [x] 7.1 UPDATE `AssetService.create_asset()` to use enhanced validation
  - [x] 7.2 UPDATE `ZipExtractionService` (Story 3.3) to use enhanced validation per file
  - [x] 7.3 ENSURE validation order: dangerous patterns → extension → MIME type → magic bytes → size
  - [x] 7.4 ADD validation timing metrics (log validation duration)

- [x] Task 8: Write Comprehensive Tests (AC: #1-#11)
  - [x] 8.1 CREATE `backend/tests/services/test_file_validation_enhanced.py`
  - [x] 8.2 CREATE `backend/tests/api/routes/test_validation_rules.py`
  - [x] 8.3 TEST extension mismatch rejection (file.exe with application/pdf Content-Type)
  - [x] 8.4 TEST double extension rejection (.pdf.exe)
  - [x] 8.5 TEST null byte rejection (file.pdf\x00.exe)
  - [x] 8.6 TEST unicode trick rejection (RTL override characters)
  - [x] 8.7 TEST executable format rejection (PE, ELF, Mach-O headers)
  - [x] 8.8 TEST SVG and HTML rejection when not in allowed list
  - [x] 8.9 TEST audio size limit enforcement (100MB)
  - [x] 8.10 TEST validation rules endpoint returns correct data
  - [x] 8.11 TEST validation performance (<50ms for 100MB files)
  - [x] 8.12 TEST all allowed MIME types pass validation
  - [x] 8.13 TEST error messages are helpful and actionable

- [x] Task 9: Performance Optimization (AC: #11)
  - [x] 9.1 ENSURE magic bytes check only reads first 8KB of file
  - [x] 9.2 ADD early exit on first validation failure
  - [x] 9.3 CACHE compiled regex patterns for dangerous pattern detection
  - [x] 9.4 BENCHMARK validation time and add metrics logging
  - [x] 9.5 TEST validation completes in <50ms for files up to 100MB

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Security Implementation:**
- Implement signed URL generation with HMAC-SHA256 signatures and configurable TTL
- Create custom exceptions for domain errors (InvalidFileTypeError)
- File type validation is critical security boundary - prevents malicious file uploads

**Validation Strategy (implementation-patterns-consistency-rules.md):**
- Schema-level: Pydantic validates types, required fields, formats
- Business-level: Service layer validates business rules
- **Boundary validation is critical** - File validation happens at API boundary

### Existing Code Assets (EXTEND from Story 3.1)

**`backend/app/services/file_validation_service.py`** - Current implementation:
```python
# Current functions to EXTEND:
validate_mime_type()           # MIME type whitelist check
validate_file_size()           # Type-specific size limits
validate_magic_bytes()         # Magic bytes for MIME spoofing prevention
validate_filename()            # Basic filename validation
validate_file()                # Orchestration function
get_safe_filename()            # Filename sanitization
get_allowed_mime_types()       # Returns whitelist
get_size_limit_for_mime_type() # Returns size limit

# Current MAGIC_SIGNATURES dict - ADD more signatures
MAGIC_SIGNATURES = {
    "application/pdf": [(0, b"%PDF")],
    "image/jpeg": [(0, b"\xff\xd8\xff")],
    "image/png": [(0, b"\x89PNG\r\n\x1a\n")],
    # ... etc
}

# ADD for Story 3.4:
EXTENSION_MIME_MAP              # Extension-to-MIME mapping
DANGEROUS_SIGNATURES            # Executable format headers
DANGEROUS_PATTERNS              # Regex for dangerous filenames
validate_extension_matches_mime()
validate_dangerous_patterns()
validate_not_executable()
```

**`backend/app/core/config.py`** - Current settings:
```python
# Current settings:
ALLOWED_MIME_TYPES: list[str]   # Already comprehensive
MAX_FILE_SIZE_VIDEO: int        # 10GB
MAX_FILE_SIZE_IMAGE: int        # 500MB
MAX_FILE_SIZE_DEFAULT: int      # 5GB

# ADD for Story 3.4:
MAX_FILE_SIZE_AUDIO: int        # 100MB (new)
```

**`backend/app/core/exceptions.py`** - Current exceptions:
```python
# Current exceptions:
InvalidFileTypeError
FileTooLargeError
InvalidFilenameError
UploadError

# ADD for Story 3.4:
DangerousFileError              # For dangerous pattern detection
ExtensionMismatchError          # For Content-Type vs extension mismatch
```

### Technical Implementation Details

**Extension-to-MIME Type Mapping:**

```python
# backend/app/services/file_validation_service.py (additions)

EXTENSION_MIME_MAP: dict[str, list[str]] = {
    # Documents
    ".pdf": ["application/pdf"],
    ".json": ["application/json"],
    ".txt": ["text/plain"],

    # Videos
    ".mp4": ["video/mp4"],
    ".webm": ["video/webm"],
    ".mov": ["video/quicktime"],

    # Audio
    ".mp3": ["audio/mpeg", "audio/mp3"],
    ".wav": ["audio/wav", "audio/x-wav"],
    ".ogg": ["audio/ogg"],

    # Images
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".png": ["image/png"],
    ".gif": ["image/gif"],
    ".webp": ["image/webp"],

    # Archives
    ".zip": ["application/zip", "application/x-zip-compressed"],
}

def validate_extension_matches_mime(
    filename: str,
    mime_type: str,
) -> FileValidationResult:
    """
    Validate that file extension matches claimed MIME type.

    Prevents attacks like uploading malware.exe with Content-Type: application/pdf.
    """
    ext = os.path.splitext(filename.lower())[1]

    if not ext:
        # No extension - allow but log warning
        logger.warning(f"File without extension: {filename}")
        return FileValidationResult(is_valid=True)

    if ext not in EXTENSION_MIME_MAP:
        # Unknown extension - allow if MIME type is in whitelist
        return FileValidationResult(is_valid=True)

    allowed_mimes = EXTENSION_MIME_MAP[ext]
    normalized_mime = mime_type.lower().strip()

    if normalized_mime not in allowed_mimes:
        logger.warning(
            "Extension-MIME mismatch detected",
            extra={
                "filename": filename,
                "extension": ext,
                "claimed_mime": mime_type,
                "expected_mimes": allowed_mimes,
            },
        )
        return FileValidationResult(
            is_valid=False,
            error_code="EXTENSION_MISMATCH",
            error_message=f"File extension '{ext}' does not match Content-Type '{mime_type}'. "
                          f"Expected types for {ext}: {', '.join(allowed_mimes)}",
            details={
                "extension": ext,
                "claimed_mime": mime_type,
                "expected_mimes": allowed_mimes,
            },
        )

    return FileValidationResult(is_valid=True)
```

**Dangerous Pattern Detection:**

```python
import re
from typing import Pattern

# Compile patterns once for performance
DANGEROUS_PATTERNS: list[tuple[Pattern[str], str]] = [
    # Double extensions (potential for bypassing extension filters)
    (re.compile(r'\.(exe|bat|cmd|com|msi|scr|pif|vbs|js|jar|ps1|sh)\s*$', re.I),
     "executable_extension"),

    # Double extension tricks
    (re.compile(r'\.[a-z]{2,4}\.(exe|bat|cmd|com|msi|scr|pif|vbs|js|jar|ps1|sh)\s*$', re.I),
     "double_extension"),

    # Null byte injection
    (re.compile(r'\x00'),
     "null_byte"),

    # Unicode tricks - Right-to-left override
    (re.compile(r'[\u202e\u200e\u200f\u202a\u202b\u202c\u202d\u2066\u2067\u2068\u2069]'),
     "unicode_direction_override"),

    # Zero-width characters that could hide malicious content
    (re.compile(r'[\u200b\u200c\u200d\ufeff]'),
     "zero_width_chars"),

    # PHP/JSP/ASP extensions embedded
    (re.compile(r'\.(php|jsp|asp|aspx|cgi)\s*$', re.I),
     "server_script_extension"),
]

def validate_dangerous_patterns(filename: str) -> FileValidationResult:
    """
    Check filename for dangerous patterns that could indicate an attack.

    Detects:
    - Double extensions (.pdf.exe)
    - Null bytes
    - Unicode direction overrides (RTL tricks)
    - Zero-width characters
    - Server-side script extensions
    """
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(filename):
            logger.warning(
                "Dangerous filename pattern detected",
                extra={
                    "filename": filename,
                    "pattern_type": reason,
                },
            )
            return FileValidationResult(
                is_valid=False,
                error_code="DANGEROUS_FILENAME",
                error_message=f"Filename contains dangerous pattern: {reason}",
                details={
                    "filename": filename,
                    "pattern_type": reason,
                },
            )

    return FileValidationResult(is_valid=True)
```

**Executable Format Detection:**

```python
# Dangerous executable signatures to ALWAYS reject
EXECUTABLE_SIGNATURES: list[tuple[int, bytes, str]] = [
    # Windows PE executable
    (0, b"MZ", "Windows executable (PE)"),

    # Linux ELF executable
    (0, b"\x7fELF", "Linux executable (ELF)"),

    # macOS Mach-O 32-bit
    (0, b"\xfe\xed\xfa\xce", "macOS executable (Mach-O 32-bit)"),

    # macOS Mach-O 64-bit
    (0, b"\xfe\xed\xfa\xcf", "macOS executable (Mach-O 64-bit)"),

    # macOS Mach-O Universal Binary
    (0, b"\xca\xfe\xba\xbe", "macOS executable (Universal Binary)"),

    # Java class file
    (0, b"\xca\xfe\xba\xbe", "Java class file"),

    # Windows shortcut (LNK)
    (0, b"\x4c\x00\x00\x00", "Windows shortcut (LNK)"),

    # Microsoft Cabinet (CAB) - can contain executables
    (0, b"MSCF", "Microsoft Cabinet archive"),
]

# XSS-dangerous formats (if HTML/SVG not in allowed list)
XSS_DANGEROUS_PATTERNS: list[tuple[bytes, str]] = [
    (b"<!DOCTYPE", "HTML document"),
    (b"<html", "HTML document"),
    (b"<HTML", "HTML document"),
    (b"<?xml", "XML/SVG document"),
    (b"<svg", "SVG image (potential XSS)"),
    (b"<SVG", "SVG image (potential XSS)"),
    (b"<script", "Script tag (XSS)"),
    (b"<SCRIPT", "Script tag (XSS)"),
]

def validate_not_executable(
    file_content: bytes,
    mime_type: str,
) -> FileValidationResult:
    """
    Ensure file is not an executable format regardless of claimed MIME type.

    ALWAYS rejects executable formats (PE, ELF, Mach-O) even if Content-Type
    claims it's something else. This is a critical security check.
    """
    # Check for executable signatures
    for offset, signature, format_name in EXECUTABLE_SIGNATURES:
        if len(file_content) >= offset + len(signature):
            if file_content[offset:offset + len(signature)] == signature:
                logger.error(
                    "Executable format detected - REJECTING",
                    extra={
                        "format": format_name,
                        "claimed_mime": mime_type,
                    },
                )
                return FileValidationResult(
                    is_valid=False,
                    error_code="EXECUTABLE_DETECTED",
                    error_message=f"File appears to be an executable ({format_name}). "
                                  "Executable files are not allowed.",
                    details={
                        "format": format_name,
                        "claimed_mime": mime_type,
                    },
                )

    # Check for XSS-dangerous content if HTML/SVG not explicitly allowed
    allowed_types = get_allowed_mime_types()
    html_allowed = any(t in allowed_types for t in ["text/html", "image/svg+xml"])

    if not html_allowed:
        for pattern, format_name in XSS_DANGEROUS_PATTERNS:
            # Check first 1KB for these patterns
            if pattern.lower() in file_content[:1024].lower():
                logger.warning(
                    "XSS-dangerous content detected",
                    extra={
                        "format": format_name,
                        "claimed_mime": mime_type,
                    },
                )
                return FileValidationResult(
                    is_valid=False,
                    error_code="XSS_CONTENT_DETECTED",
                    error_message=f"File contains potentially dangerous content ({format_name}). "
                                  "This content type is not allowed.",
                    details={
                        "format": format_name,
                        "claimed_mime": mime_type,
                    },
                )

    return FileValidationResult(is_valid=True)
```

**Validation Rules API Response:**

```python
# backend/app/schemas/validation_rules.py
from pydantic import BaseModel, Field

class SizeLimitInfo(BaseModel):
    """Size limit for a file category."""
    category: str = Field(description="File category (video, image, audio, default)")
    max_size_bytes: int = Field(description="Maximum file size in bytes")
    max_size_human: str = Field(description="Human-readable size limit")

class ExtensionMapping(BaseModel):
    """Extension to MIME type mapping."""
    extension: str = Field(description="File extension (e.g., '.pdf')")
    mime_types: list[str] = Field(description="Allowed MIME types for this extension")

class ValidationRulesResponse(BaseModel):
    """Response containing all file validation rules."""

    allowed_mime_types: list[str] = Field(
        description="List of allowed MIME types"
    )
    size_limits: list[SizeLimitInfo] = Field(
        description="Size limits per file category"
    )
    extension_mappings: list[ExtensionMapping] = Field(
        description="Extension to MIME type mappings for validation"
    )
    max_filename_length: int = Field(
        description="Maximum allowed filename length"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "allowed_mime_types": ["application/pdf", "video/mp4", "image/jpeg"],
                "size_limits": [
                    {"category": "video", "max_size_bytes": 10737418240, "max_size_human": "10 GB"},
                    {"category": "image", "max_size_bytes": 524288000, "max_size_human": "500 MB"},
                    {"category": "audio", "max_size_bytes": 104857600, "max_size_human": "100 MB"},
                    {"category": "default", "max_size_bytes": 5368709120, "max_size_human": "5 GB"},
                ],
                "extension_mappings": [
                    {"extension": ".pdf", "mime_types": ["application/pdf"]},
                    {"extension": ".mp4", "mime_types": ["video/mp4"]},
                ],
                "max_filename_length": 255,
            }
        }
```

**Validation Rules Endpoint:**

```python
# backend/app/api/routes/validation.py
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.validation_rules import (
    ValidationRulesResponse,
    SizeLimitInfo,
    ExtensionMapping,
)
from app.services.file_validation_service import EXTENSION_MIME_MAP

router = APIRouter(prefix="/upload", tags=["validation"])

def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.0f} PB"

@router.get(
    "/validation-rules",
    response_model=ValidationRulesResponse,
    summary="Get file validation rules",
    description="""
    Returns the current file validation rules for client-side pre-validation.

    Use this endpoint to:
    - Show allowed file types in upload UI
    - Validate files before upload attempt
    - Display size limits to users
    - Build file type filters

    This endpoint does not require authentication.
    """,
)
async def get_validation_rules() -> ValidationRulesResponse:
    """Return current file validation rules."""
    size_limits = [
        SizeLimitInfo(
            category="video",
            max_size_bytes=settings.MAX_FILE_SIZE_VIDEO,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_VIDEO),
        ),
        SizeLimitInfo(
            category="image",
            max_size_bytes=settings.MAX_FILE_SIZE_IMAGE,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_IMAGE),
        ),
        SizeLimitInfo(
            category="audio",
            max_size_bytes=settings.MAX_FILE_SIZE_AUDIO,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_AUDIO),
        ),
        SizeLimitInfo(
            category="default",
            max_size_bytes=settings.MAX_FILE_SIZE_DEFAULT,
            max_size_human=format_bytes(settings.MAX_FILE_SIZE_DEFAULT),
        ),
    ]

    extension_mappings = [
        ExtensionMapping(extension=ext, mime_types=mimes)
        for ext, mimes in EXTENSION_MIME_MAP.items()
    ]

    return ValidationRulesResponse(
        allowed_mime_types=settings.ALLOWED_MIME_TYPES,
        size_limits=size_limits,
        extension_mappings=extension_mappings,
        max_filename_length=255,
    )
```

**Updated validate_file() Orchestration:**

```python
def validate_file(
    filename: str,
    mime_type: str,
    size: int,
    file_content: bytes | None = None,
) -> FileValidationResult:
    """
    Perform comprehensive file validation (Story 3.4 enhanced).

    Validation order (fail-fast):
    1. Dangerous filename patterns (null bytes, unicode tricks, double extensions)
    2. Extension matches MIME type
    3. MIME type in whitelist
    4. Not an executable format (PE/ELF/Mach-O)
    5. Magic bytes match MIME type
    6. File size within limits

    Args:
        filename: Original filename
        mime_type: MIME type from upload
        size: File size in bytes
        file_content: Optional file content for magic bytes validation

    Returns:
        FileValidationResult with first validation failure or success
    """
    # 1. Check for dangerous filename patterns
    dangerous_result = validate_dangerous_patterns(filename)
    if not dangerous_result.is_valid:
        return dangerous_result

    # 2. Validate filename format
    filename_result = validate_filename(filename)
    if not filename_result.is_valid:
        return filename_result

    # 3. Validate extension matches MIME type
    extension_result = validate_extension_matches_mime(filename, mime_type)
    if not extension_result.is_valid:
        return extension_result

    # 4. Validate MIME type in whitelist
    mime_result = validate_mime_type(mime_type)
    if not mime_result.is_valid:
        return mime_result

    # 5. If content provided, run content-based checks
    if file_content is not None:
        # 5a. Check for executable formats (ALWAYS reject)
        exec_result = validate_not_executable(file_content, mime_type)
        if not exec_result.is_valid:
            return exec_result

        # 5b. Validate magic bytes match claimed type
        magic_result = validate_magic_bytes(file_content, mime_type)
        if not magic_result.is_valid:
            return magic_result

    # 6. Validate size
    size_result = validate_file_size(size, mime_type)
    if not size_result.is_valid:
        return size_result

    logger.debug(
        "File validation passed (enhanced)",
        extra={
            "file_name": filename,
            "mime_type": mime_type,
            "size_bytes": size,
            "content_validated": file_content is not None,
        },
    )

    return FileValidationResult(is_valid=True)
```

### Dependencies

**Already Available (no new dependencies):**
```
Python standard library:
  - re (regex for pattern matching)
  - os (path operations)
```

### Git Workflow

**Branch:** `story/3-4-file-type-validation`

**Commit Pattern:**
```
feat(story-3.4): Implement enhanced file type and size validation
```

### Testing Standards

**Test Commands:**
```bash
# Run validation tests
uv run pytest backend/tests/services/test_file_validation_enhanced.py -v
uv run pytest backend/tests/api/routes/test_validation_rules.py -v

# Run with coverage
uv run pytest backend/tests/ -v -k "validation" --cov=backend/app

# Performance test
uv run pytest backend/tests/services/test_file_validation_enhanced.py -v -k "performance"
```

**Key Test Cases:**

```python
# backend/tests/services/test_file_validation_enhanced.py

class TestExtensionValidation:
    def test_extension_matches_mime_valid(self):
        """Valid extension-MIME combinations pass."""
        result = validate_extension_matches_mime("document.pdf", "application/pdf")
        assert result.is_valid

    def test_extension_mismatch_rejected(self):
        """Mismatched extension and MIME type is rejected."""
        result = validate_extension_matches_mime("malware.exe", "application/pdf")
        assert not result.is_valid
        assert result.error_code == "EXTENSION_MISMATCH"

    def test_no_extension_allowed(self):
        """Files without extensions are allowed but logged."""
        result = validate_extension_matches_mime("README", "text/plain")
        assert result.is_valid


class TestDangerousPatterns:
    def test_double_extension_rejected(self):
        """Double extensions are rejected."""
        result = validate_dangerous_patterns("document.pdf.exe")
        assert not result.is_valid
        assert result.error_code == "DANGEROUS_FILENAME"

    def test_null_byte_rejected(self):
        """Null bytes in filename are rejected."""
        result = validate_dangerous_patterns("file.pdf\x00.exe")
        assert not result.is_valid

    def test_unicode_rtl_rejected(self):
        """Right-to-left override characters are rejected."""
        result = validate_dangerous_patterns("file\u202efdp.exe")  # Displays as "fileexe.pdf"
        assert not result.is_valid

    def test_normal_filename_passes(self):
        """Normal filenames pass validation."""
        result = validate_dangerous_patterns("my-document_v2.pdf")
        assert result.is_valid


class TestExecutableDetection:
    def test_pe_executable_rejected(self):
        """Windows PE executables are rejected."""
        pe_header = b"MZ" + b"\x00" * 100
        result = validate_not_executable(pe_header, "application/pdf")
        assert not result.is_valid
        assert result.error_code == "EXECUTABLE_DETECTED"

    def test_elf_executable_rejected(self):
        """Linux ELF executables are rejected."""
        elf_header = b"\x7fELF" + b"\x00" * 100
        result = validate_not_executable(elf_header, "application/pdf")
        assert not result.is_valid

    def test_macho_executable_rejected(self):
        """macOS Mach-O executables are rejected."""
        macho_header = b"\xfe\xed\xfa\xce" + b"\x00" * 100
        result = validate_not_executable(macho_header, "application/pdf")
        assert not result.is_valid

    def test_pdf_passes(self):
        """Valid PDF content passes."""
        pdf_content = b"%PDF-1.4 test content"
        result = validate_not_executable(pdf_content, "application/pdf")
        assert result.is_valid


class TestValidationRulesEndpoint:
    def test_returns_allowed_types(self, client):
        """Endpoint returns allowed MIME types."""
        response = client.get("/api/v1/upload/validation-rules")
        assert response.status_code == 200
        data = response.json()
        assert "application/pdf" in data["allowed_mime_types"]

    def test_returns_size_limits(self, client):
        """Endpoint returns size limits per category."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()
        categories = [s["category"] for s in data["size_limits"]]
        assert "video" in categories
        assert "image" in categories
        assert "audio" in categories

    def test_returns_extension_mappings(self, client):
        """Endpoint returns extension to MIME mappings."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()
        extensions = [m["extension"] for m in data["extension_mappings"]]
        assert ".pdf" in extensions
        assert ".mp4" in extensions


class TestValidationPerformance:
    def test_validation_under_50ms(self):
        """Validation completes in under 50ms."""
        import time
        # Create 100MB of test content
        content = b"%PDF-1.4 " + b"x" * (100 * 1024 * 1024)

        start = time.time()
        result = validate_file(
            filename="large-document.pdf",
            mime_type="application/pdf",
            size=len(content),
            file_content=content[:8192],  # Only check first 8KB
        )
        duration_ms = (time.time() - start) * 1000

        assert result.is_valid
        assert duration_ms < 50, f"Validation took {duration_ms}ms, expected <50ms"
```

### Security Considerations

**Critical Security Requirements:**
- ALWAYS reject executable formats (PE/ELF/Mach-O) regardless of Content-Type
- Detect and reject MIME type spoofing (extension ≠ Content-Type)
- Detect dangerous filename patterns (null bytes, double extensions)
- Block XSS vectors (SVG/HTML if not in allowed list)
- Log all validation failures for security monitoring

**OWASP Compliance:**
- A3:2021 - Injection: Filename sanitization, dangerous pattern detection
- A4:2021 - Insecure Design: Comprehensive file validation at boundary
- A5:2021 - Security Misconfiguration: Explicit whitelist, strict validation

### Project Structure Updates

**CREATE Files:**
```
backend/app/schemas/validation_rules.py           # Validation rules response schema
backend/app/api/routes/validation.py              # Validation rules endpoint
backend/tests/services/test_file_validation_enhanced.py  # Enhanced validation tests
backend/tests/api/routes/test_validation_rules.py # Endpoint tests
```

**UPDATE Files:**
```
backend/app/core/config.py                        # ADD MAX_FILE_SIZE_AUDIO
backend/app/core/exceptions.py                    # ADD DangerousFileError
backend/app/services/file_validation_service.py   # ADD all new validation functions
backend/app/api/main.py                           # REGISTER validation router
.env.example                                      # ADD new config vars
```

### Integration with Story 3.3

Story 3.3 (ZIP extraction) should use the enhanced validation from this story for each extracted file. Ensure:
- Each file from ZIP goes through `validate_file()` with all enhanced checks
- Extension validation catches malicious files hidden in ZIP
- Executable detection catches disguised executables

## References

- [Source: docs/epics.md#Story-3.4] - Original story requirements
- [Source: docs/architecture/implementation-patterns-consistency-rules.md] - Validation patterns
- [Source: backend/app/services/file_validation_service.py] - Existing validation
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [Python zipfile security](https://docs.python.org/3/library/zipfile.html#zipfile-objects)

## Dev Agent Record

### Context Reference

Story 3.4 implementation - fourth story in Epic 3 (Core Asset Upload & Storage).
Enhances file validation implemented in Story 3.1 with comprehensive security checks.
Critical security boundary - prevents malicious file uploads.
Builds on existing file_validation_service.py with new detection capabilities.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List
