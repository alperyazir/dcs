"""
File Validation Service (Story 3.1, Task 3; Story 3.4 Enhanced).

Provides:
- MIME type validation against configurable whitelist (AC: #2)
- Magic bytes validation to prevent MIME spoofing (Security requirement)
- File size validation with type-specific limits (AC: #1, NFR-P3)
- Filename sanitization for security (OWASP A3:2021)

Story 3.4 Enhancements:
- Extension-MIME cross-validation (AC: #1, #2)
- Dangerous filename pattern detection (AC: #9)
- Executable format detection (AC: #10)
- Audio file size limits (AC: #5)
- Performance optimization (<50ms for 100MB files) (AC: #11)

References:
- AC: #1 (max 10GB per file)
- AC: #2 (MIME type whitelist validation)
- AC: #10 (reject invalid file type with INVALID_FILE_TYPE)
- AC: #11 (reject oversized file with FILE_TOO_LARGE)
- Story 3.4 AC: #9 (dangerous patterns)
- Story 3.4 AC: #10 (executable detection)
"""

import logging
import os
import re
from re import Pattern
from typing import Any, NamedTuple

from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# MAGIC BYTES SIGNATURES (Security: prevent MIME spoofing)
# =============================================================================

# Format: {mime_type: [(offset, bytes), ...]}
MAGIC_SIGNATURES: dict[str, list[tuple[int, bytes]]] = {
    # PDF files start with %PDF
    "application/pdf": [(0, b"%PDF")],
    # JPEG files start with FFD8FF
    "image/jpeg": [(0, b"\xff\xd8\xff")],
    # PNG files have specific signature
    "image/png": [(0, b"\x89PNG\r\n\x1a\n")],
    # GIF files start with GIF87a or GIF89a
    "image/gif": [(0, b"GIF87a"), (0, b"GIF89a")],
    # WebP files have RIFF header with WEBP
    "image/webp": [(0, b"RIFF"), (8, b"WEBP")],
    # ZIP files (and derivatives like DOCX, XLSX)
    "application/zip": [(0, b"PK\x03\x04"), (0, b"PK\x05\x06"), (0, b"PK\x07\x08")],
    "application/x-zip-compressed": [
        (0, b"PK\x03\x04"),
        (0, b"PK\x05\x06"),
        (0, b"PK\x07\x08"),
    ],
    # MP4/M4V video files (ftyp box)
    "video/mp4": [(4, b"ftyp")],
    "video/quicktime": [(4, b"ftyp")],
    # WebM video files (EBML header)
    "video/webm": [(0, b"\x1a\x45\xdf\xa3")],
    # MP3 audio (ID3 tag or sync bits)
    "audio/mpeg": [(0, b"ID3"), (0, b"\xff\xfb"), (0, b"\xff\xfa"), (0, b"\xff\xf3")],
    "audio/mp3": [(0, b"ID3"), (0, b"\xff\xfb"), (0, b"\xff\xfa"), (0, b"\xff\xf3")],
    # WAV audio (RIFF header with WAVE)
    "audio/wav": [(0, b"RIFF"), (8, b"WAVE")],
    "audio/x-wav": [(0, b"RIFF"), (8, b"WAVE")],
    # OGG audio/video
    "audio/ogg": [(0, b"OggS")],
    # JSON files - start with { or [ (with optional whitespace)
    "application/json": [],  # JSON validated differently (text-based)
    # Plain text - no magic bytes, validated differently
    "text/plain": [],
}

# =============================================================================
# EXTENSION-TO-MIME MAPPING (Story 3.4, AC: #1, #2)
# =============================================================================

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

# =============================================================================
# DANGEROUS PATTERNS (Story 3.4, AC: #9)
# =============================================================================

# Compile patterns once at module load for performance (AC: #11)
# IMPORTANT: Order matters - more specific patterns checked first
DANGEROUS_FILENAME_PATTERNS: list[tuple[Pattern[str], str, str]] = [
    # Null byte injection (MOST DANGEROUS - can bypass path checks)
    (
        re.compile(r"\x00"),
        "null_byte",
        "Filename contains null byte",
    ),
    # Unicode direction overrides (RTL override attack)
    (
        re.compile(
            r"[\u202e\u200e\u200f\u202a\u202b\u202c\u202d\u2066\u2067\u2068\u2069]"
        ),
        "unicode_direction_override",
        "Filename contains unicode direction override characters",
    ),
    # Zero-width characters that could hide content
    (
        re.compile(r"[\u200b\u200c\u200d\ufeff]"),
        "zero_width_chars",
        "Filename contains zero-width characters",
    ),
    # Double extension tricks (e.g., .pdf.exe, .jpg.php) - check BEFORE single extension
    (
        re.compile(
            r"\.[a-z0-9]{2,5}\.(exe|bat|cmd|com|msi|scr|pif|vbs|vbe|js|jse|ws|wsf|wsc|wsh|php|jsp|asp|aspx|cgi|pl|py|rb|sh)$",
            re.I,
        ),
        "double_extension",
        "File has suspicious double extension",
    ),
    # Server-side script extensions (PHP, JSP, ASP, etc.)
    (
        re.compile(r"\.(php[0-9]?|phtml|jsp|jspx|asp|aspx|cgi|pl|py|rb|sh)$", re.I),
        "server_script_extension",
        "File has server-side script extension",
    ),
    # Executable extensions (ALWAYS block) - checked last (most general)
    (
        re.compile(
            r"\.(exe|bat|cmd|com|msi|scr|pif|vbs|vbe|js|jse|ws|wsf|wsc|wsh)$", re.I
        ),
        "executable_extension",
        "File has executable extension",
    ),
]

# =============================================================================
# EXECUTABLE FORMAT SIGNATURES (Story 3.4, AC: #10)
# =============================================================================

# ALWAYS reject these - no matter what Content-Type claims
EXECUTABLE_SIGNATURES: list[tuple[int, bytes, str]] = [
    # Windows PE executable (MZ header)
    (0, b"MZ", "Windows PE executable"),
    # Linux ELF executable
    (0, b"\x7fELF", "Linux ELF executable"),
    # macOS Mach-O 32-bit (little endian)
    (0, b"\xce\xfa\xed\xfe", "macOS Mach-O 32-bit"),
    # macOS Mach-O 64-bit (little endian)
    (0, b"\xcf\xfa\xed\xfe", "macOS Mach-O 64-bit"),
    # macOS Mach-O 32-bit (big endian)
    (0, b"\xfe\xed\xfa\xce", "macOS Mach-O 32-bit BE"),
    # macOS Mach-O 64-bit (big endian)
    (0, b"\xfe\xed\xfa\xcf", "macOS Mach-O 64-bit BE"),
    # macOS Universal Binary / Java class file
    (0, b"\xca\xfe\xba\xbe", "macOS Universal Binary / Java class"),
    # Windows shortcut (LNK) - can execute arbitrary commands
    (0, b"\x4c\x00\x00\x00\x01\x14\x02\x00", "Windows shortcut (LNK)"),
    # Microsoft Cabinet (CAB)
    (0, b"MSCF", "Microsoft Cabinet archive"),
]

# XSS-dangerous content patterns (if HTML/SVG not explicitly allowed)
XSS_DANGEROUS_PATTERNS: list[tuple[bytes, str]] = [
    (b"<!doctype html", "HTML document"),
    (b"<!DOCTYPE html", "HTML document"),
    (b"<html", "HTML document"),
    (b"<HTML", "HTML document"),
    (b"<?xml", "XML document (potential SVG)"),
    (b"<svg", "SVG image (XSS risk)"),
    (b"<SVG", "SVG image (XSS risk)"),
    (b"<script", "Script tag (XSS)"),
    (b"<SCRIPT", "Script tag (XSS)"),
    (b"javascript:", "JavaScript URL"),
]


# =============================================================================
# VALIDATION RESULT TYPE
# =============================================================================


class FileValidationResult(NamedTuple):
    """Result of file validation."""

    is_valid: bool
    error_code: str | None = None
    error_message: str | None = None
    details: dict[str, Any] | None = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_allowed_mime_types() -> list[str]:
    """
    Get allowed MIME types from configuration.

    Returns:
        List of allowed MIME type strings
    """
    return settings.ALLOWED_MIME_TYPES


def get_size_limit_for_mime_type(mime_type: str) -> int:
    """
    Get file size limit based on MIME type (AC: #1, NFR-P3, Story 3.4 AC: #5).

    Size limits:
    - Video: 10GB (video/* types)
    - Image: 500MB (image/* types)
    - Audio: 100MB (audio/* types) - Story 3.4
    - Default: 5GB (all other types)

    Args:
        mime_type: MIME type string

    Returns:
        Maximum file size in bytes
    """
    if mime_type.startswith("video/"):
        return settings.MAX_FILE_SIZE_VIDEO
    elif mime_type.startswith("image/"):
        return settings.MAX_FILE_SIZE_IMAGE
    elif mime_type.startswith("audio/"):
        return settings.MAX_FILE_SIZE_AUDIO
    return settings.MAX_FILE_SIZE_DEFAULT


def get_extension_mime_map() -> dict[str, list[str]]:
    """
    Get extension-to-MIME type mapping.

    Returns:
        Dictionary mapping file extensions to allowed MIME types
    """
    return EXTENSION_MIME_MAP.copy()


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_mime_type(mime_type: str) -> FileValidationResult:
    """
    Validate MIME type against whitelist (AC: #2, #10).

    Args:
        mime_type: MIME type to validate

    Returns:
        FileValidationResult with validation status
    """
    allowed_types = get_allowed_mime_types()

    if not mime_type:
        return FileValidationResult(
            is_valid=False,
            error_code="INVALID_FILE_TYPE",
            error_message="No MIME type provided",
            details={"mime_type": None, "allowed_types": allowed_types},
        )

    # Normalize MIME type (lowercase, strip whitespace)
    normalized_mime = mime_type.lower().strip()

    if normalized_mime not in allowed_types:
        # Build helpful error message (Story 3.4, AC: #7)
        type_hints = _get_type_category_hints(normalized_mime)

        logger.warning(
            "Invalid MIME type rejected",
            extra={
                "mime_type": mime_type,
                "allowed_types": allowed_types,
            },
        )
        return FileValidationResult(
            is_valid=False,
            error_code="INVALID_FILE_TYPE",
            error_message=f"File type '{mime_type}' is not allowed. {type_hints}",
            details={"mime_type": mime_type, "allowed_types": allowed_types},
        )

    return FileValidationResult(is_valid=True)


def _get_type_category_hints(mime_type: str) -> str:
    """Generate helpful hints based on MIME type category (Story 3.4, AC: #7)."""
    if mime_type.startswith("video/"):
        return "Supported video formats: MP4, WebM, MOV"
    elif mime_type.startswith("audio/"):
        return "Supported audio formats: MP3, WAV, OGG"
    elif mime_type.startswith("image/"):
        return "Supported image formats: JPEG, PNG, GIF, WebP"
    elif mime_type.startswith("application/"):
        return "Supported document formats: PDF, JSON, ZIP"
    return "Supported types: PDF, MP4, WebM, MP3, JPEG, PNG, GIF, WebP, ZIP"


def validate_extension_matches_mime(
    filename: str,
    mime_type: str,
) -> FileValidationResult:
    """
    Validate that file extension matches claimed MIME type (Story 3.4, AC: #1, #2).

    Prevents attacks like uploading malware.exe with Content-Type: application/pdf.

    Args:
        filename: Original filename
        mime_type: MIME type from Content-Type header

    Returns:
        FileValidationResult with validation status
    """
    ext = os.path.splitext(filename.lower())[1]

    if not ext:
        # No extension - allow but log warning
        logger.warning(
            "File without extension uploaded",
            extra={"file_name": filename, "mime_type": mime_type},
        )
        return FileValidationResult(is_valid=True)

    if ext not in EXTENSION_MIME_MAP:
        # Unknown extension - allow if MIME type is in whitelist
        # This handles cases like custom extensions
        return FileValidationResult(is_valid=True)

    allowed_mimes = EXTENSION_MIME_MAP[ext]
    normalized_mime = mime_type.lower().strip()

    if normalized_mime not in allowed_mimes:
        logger.warning(
            "Extension-MIME mismatch detected (possible spoofing attempt)",
            extra={
                "file_name": filename,
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
                "filename": filename,
                "extension": ext,
                "claimed_mime": mime_type,
                "expected_mimes": allowed_mimes,
            },
        )

    return FileValidationResult(is_valid=True)


def validate_dangerous_patterns(filename: str) -> FileValidationResult:
    """
    Check filename for dangerous patterns (Story 3.4, AC: #9).

    Detects:
    - Executable extensions (.exe, .bat, .cmd, etc.)
    - Double extensions (.pdf.exe, .jpg.php)
    - Null bytes (file.pdf\\x00.exe)
    - Unicode direction overrides (RTL tricks)
    - Zero-width characters
    - Server-side script extensions

    Args:
        filename: Filename to check

    Returns:
        FileValidationResult with validation status
    """
    for pattern, pattern_type, reason in DANGEROUS_FILENAME_PATTERNS:
        if pattern.search(filename):
            logger.warning(
                "Dangerous filename pattern detected",
                extra={
                    "file_name": filename,
                    "pattern_type": pattern_type,
                },
            )
            return FileValidationResult(
                is_valid=False,
                error_code="DANGEROUS_FILENAME",
                error_message=f"Filename rejected: {reason}",
                details={
                    "file_name": filename,
                    "pattern_type": pattern_type,
                },
            )

    return FileValidationResult(is_valid=True)


def validate_not_executable(
    file_content: bytes,
    mime_type: str,
) -> FileValidationResult:
    """
    Ensure file is not an executable format (Story 3.4, AC: #10).

    ALWAYS rejects executable formats (PE, ELF, Mach-O) even if Content-Type
    claims it's something else. This is a critical security check.

    Also checks for XSS-dangerous content (HTML, SVG, scripts) if not explicitly allowed.

    Args:
        file_content: File content (at least first 1KB recommended)
        mime_type: Claimed MIME type

    Returns:
        FileValidationResult with validation status
    """
    # Check for executable signatures (first 8 bytes is enough)
    check_bytes = file_content[:16] if len(file_content) >= 16 else file_content

    for offset, signature, format_name in EXECUTABLE_SIGNATURES:
        if len(check_bytes) >= offset + len(signature):
            if check_bytes[offset : offset + len(signature)] == signature:
                logger.error(
                    "SECURITY: Executable format detected - REJECTING",
                    extra={
                        "format": format_name,
                        "claimed_mime": mime_type,
                        "signature_hex": signature.hex(),
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
    html_svg_allowed = any(
        t in allowed_types
        for t in ["text/html", "image/svg+xml", "application/xhtml+xml"]
    )

    if not html_svg_allowed:
        # Check first 1KB for XSS patterns
        check_content = file_content[:1024].lower()
        for pattern, format_name in XSS_DANGEROUS_PATTERNS:
            if pattern.lower() in check_content:
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


def validate_magic_bytes(file_content: bytes, mime_type: str) -> FileValidationResult:
    """
    Validate file content against magic bytes signature (Security: prevent MIME spoofing).

    This prevents attackers from uploading malicious files (e.g., executables)
    disguised with a safe Content-Type header (e.g., application/pdf).

    Args:
        file_content: First bytes of the file (at least 16 bytes recommended)
        mime_type: Claimed MIME type to validate against

    Returns:
        FileValidationResult with validation status
    """
    normalized_mime = mime_type.lower().strip()

    # Check if we have magic signatures for this MIME type
    if normalized_mime not in MAGIC_SIGNATURES:
        # No signatures defined - allow (for text-based types like JSON, text/plain)
        return FileValidationResult(is_valid=True)

    signatures = MAGIC_SIGNATURES[normalized_mime]

    # Empty signatures list means text-based validation or no magic check needed
    if not signatures:
        return FileValidationResult(is_valid=True)

    # Check if any signature matches
    for offset, magic in signatures:
        if len(file_content) >= offset + len(magic):
            if file_content[offset : offset + len(magic)] == magic:
                return FileValidationResult(is_valid=True)

    # No signature matched - file content doesn't match claimed MIME type
    logger.warning(
        "Magic bytes validation failed - possible MIME spoofing",
        extra={
            "claimed_mime_type": mime_type,
            "file_header": file_content[:16].hex() if file_content else "empty",
        },
    )

    return FileValidationResult(
        is_valid=False,
        error_code="INVALID_FILE_TYPE",
        error_message=f"File content does not match claimed type '{mime_type}'. "
        "File may be corrupted or incorrectly labeled.",
        details={
            "mime_type": mime_type,
            "reason": "magic_bytes_mismatch",
        },
    )


def validate_file_size(size: int, mime_type: str) -> FileValidationResult:
    """
    Validate file size based on type (AC: #1, #11, NFR-P3, Story 3.4 AC: #5).

    Args:
        size: File size in bytes
        mime_type: MIME type for determining limit

    Returns:
        FileValidationResult with validation status
    """
    if size < 0:
        return FileValidationResult(
            is_valid=False,
            error_code="INVALID_FILE_SIZE",
            error_message="File size cannot be negative",
            details={"size": size},
        )

    if size == 0:
        return FileValidationResult(
            is_valid=False,
            error_code="EMPTY_FILE",
            error_message="File is empty",
            details={"size": size},
        )

    max_size = get_size_limit_for_mime_type(mime_type)

    if size > max_size:
        # Format sizes for user-friendly message
        size_mb = size / (1024 * 1024)
        max_size_mb = max_size / (1024 * 1024)

        # Determine category for message (Story 3.4, AC: #7)
        if mime_type.startswith("video/"):
            category = "video"
        elif mime_type.startswith("image/"):
            category = "image"
        elif mime_type.startswith("audio/"):
            category = "audio"
        else:
            category = "this type of"

        logger.warning(
            "File size exceeded limit",
            extra={
                "size_bytes": size,
                "max_size_bytes": max_size,
                "mime_type": mime_type,
            },
        )

        return FileValidationResult(
            is_valid=False,
            error_code="FILE_TOO_LARGE",
            error_message=f"File size ({size_mb:.1f} MB) exceeds maximum "
            f"allowed size ({max_size_mb:.1f} MB) for {category} files",
            details={
                "size_bytes": size,
                "max_size_bytes": max_size,
                "mime_type": mime_type,
                "category": category,
            },
        )

    return FileValidationResult(is_valid=True)


def get_safe_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and injection attacks (Task 3.5).

    Security measures:
    - Remove path separators (/ and \\)
    - Remove parent directory references (..)
    - Remove null bytes
    - Limit length
    - Remove potentially dangerous characters

    Args:
        filename: Original filename from upload

    Returns:
        Sanitized filename safe for storage
    """
    if not filename:
        return "unnamed_file"

    # Get just the filename part, removing any path
    safe_name = os.path.basename(filename)

    # Remove path traversal attempts
    safe_name = safe_name.replace("..", "")
    safe_name = safe_name.replace("/", "")
    safe_name = safe_name.replace("\\", "")

    # Remove null bytes
    safe_name = safe_name.replace("\x00", "")

    # Remove potentially dangerous characters (keep alphanumeric, dots, hyphens, underscores)
    safe_name = re.sub(r"[^\w\.\-]", "_", safe_name)

    # Collapse multiple underscores
    safe_name = re.sub(r"_+", "_", safe_name)

    # Limit length (255 is typical filesystem limit)
    if len(safe_name) > 255:
        # Keep extension, truncate name
        name, ext = os.path.splitext(safe_name)
        max_name_len = 255 - len(ext)
        safe_name = name[:max_name_len] + ext

    # Ensure we have a valid name
    if not safe_name or safe_name in (".", ".."):
        return "unnamed_file"

    return safe_name


def validate_filename(filename: str) -> FileValidationResult:
    """
    Validate filename for safety (Task 7.3).

    Args:
        filename: Filename to validate

    Returns:
        FileValidationResult with validation status
    """
    if not filename:
        return FileValidationResult(
            is_valid=False,
            error_code="INVALID_FILENAME",
            error_message="Filename is required",
            details={"filename": filename},
        )

    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        logger.warning(
            "Path traversal attempt detected",
            extra={"file_name": filename},
        )
        return FileValidationResult(
            is_valid=False,
            error_code="INVALID_FILENAME",
            error_message="Filename contains invalid characters",
            details={"file_name": filename},
        )

    # Check length
    if len(filename) > 255:
        return FileValidationResult(
            is_valid=False,
            error_code="FILENAME_TOO_LONG",
            error_message="Filename exceeds maximum length of 255 characters",
            details={"filename": filename, "length": len(filename)},
        )

    return FileValidationResult(is_valid=True)


def validate_file(
    filename: str,
    mime_type: str,
    size: int,
    file_content: bytes | None = None,
) -> FileValidationResult:
    """
    Perform comprehensive file validation (Story 3.4 enhanced).

    Validation order (fail-fast for performance, AC: #11):
    1. Dangerous filename patterns (null bytes, unicode tricks, double extensions)
    2. Basic filename validation (path traversal, length)
    3. Extension matches MIME type (Content-Type spoofing prevention)
    4. MIME type in whitelist
    5. Not an executable format (PE/ELF/Mach-O - ALWAYS blocked)
    6. Magic bytes match MIME type (file content verification)
    7. File size within limits

    Args:
        filename: Original filename
        mime_type: MIME type from upload
        size: File size in bytes
        file_content: Optional file content for content-based validation
                     (at least first 1KB recommended for XSS check)

    Returns:
        FileValidationResult with first validation failure or success
    """
    # 1. Check for dangerous filename patterns (Story 3.4, AC: #9)
    dangerous_result = validate_dangerous_patterns(filename)
    if not dangerous_result.is_valid:
        return dangerous_result

    # 2. Validate filename format (path traversal, length)
    filename_result = validate_filename(filename)
    if not filename_result.is_valid:
        return filename_result

    # 3. Validate extension matches MIME type (Story 3.4, AC: #1, #2)
    extension_result = validate_extension_matches_mime(filename, mime_type)
    if not extension_result.is_valid:
        return extension_result

    # 4. Validate MIME type in whitelist
    mime_result = validate_mime_type(mime_type)
    if not mime_result.is_valid:
        return mime_result

    # 5-6. If content provided, run content-based checks
    if file_content is not None:
        # 5. Check for executable formats (Story 3.4, AC: #10 - ALWAYS reject)
        exec_result = validate_not_executable(file_content, mime_type)
        if not exec_result.is_valid:
            return exec_result

        # 6. Validate magic bytes match claimed type
        magic_result = validate_magic_bytes(file_content, mime_type)
        if not magic_result.is_valid:
            return magic_result

    # 7. Validate size (Story 3.4, AC: #5 includes audio limits)
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
