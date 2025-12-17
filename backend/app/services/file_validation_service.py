"""
File Validation Service (Story 3.1, Task 3).

Provides:
- MIME type validation against configurable whitelist (AC: #2)
- Magic bytes validation to prevent MIME spoofing (Security requirement)
- File size validation with type-specific limits (AC: #1, NFR-P3)
- Filename sanitization for security (OWASP A3:2021)

References:
- AC: #1 (max 10GB per file)
- AC: #2 (MIME type whitelist validation)
- AC: #10 (reject invalid file type with INVALID_FILE_TYPE)
- AC: #11 (reject oversized file with FILE_TOO_LARGE)
"""

import logging
import os
import re
from typing import Any, NamedTuple

from app.core.config import settings

logger = logging.getLogger(__name__)

# Magic bytes signatures for common file types (Security: prevent MIME spoofing)
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
    # OGG audio/video
    "audio/ogg": [(0, b"OggS")],
    # JSON files - start with { or [ (with optional whitespace)
    "application/json": [],  # JSON validated differently (text-based)
    # Plain text - no magic bytes, validated differently
    "text/plain": [],
}


class FileValidationResult(NamedTuple):
    """Result of file validation."""

    is_valid: bool
    error_code: str | None = None
    error_message: str | None = None
    details: dict[str, Any] | None = None


def get_allowed_mime_types() -> list[str]:
    """
    Get allowed MIME types from configuration.

    Returns:
        List of allowed MIME type strings
    """
    return settings.ALLOWED_MIME_TYPES


def get_size_limit_for_mime_type(mime_type: str) -> int:
    """
    Get file size limit based on MIME type (AC: #1, NFR-P3).

    Size limits:
    - Video: 10GB (video/* types)
    - Image: 500MB (image/* types)
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
    return settings.MAX_FILE_SIZE_DEFAULT


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
            error_message=f"File type '{mime_type}' is not allowed. "
            f"Supported types: {', '.join(allowed_types)}",
            details={"mime_type": mime_type, "allowed_types": allowed_types},
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
    Validate file size based on type (AC: #1, #11, NFR-P3).

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
            f"allowed size ({max_size_mb:.1f} MB) for {mime_type} files",
            details={
                "size_bytes": size,
                "max_size_bytes": max_size,
                "mime_type": mime_type,
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
    Perform complete file validation (AC: #1, #2, #10, #11).

    Validates in order:
    1. Filename (for security)
    2. MIME type (against whitelist)
    3. Magic bytes (if file_content provided - prevents MIME spoofing)
    4. File size (against type-specific limits)

    Args:
        filename: Original filename
        mime_type: MIME type from upload
        size: File size in bytes
        file_content: Optional file content for magic bytes validation (first 16+ bytes)

    Returns:
        FileValidationResult with first validation failure or success
    """
    # Validate filename
    filename_result = validate_filename(filename)
    if not filename_result.is_valid:
        return filename_result

    # Validate MIME type
    mime_result = validate_mime_type(mime_type)
    if not mime_result.is_valid:
        return mime_result

    # Validate magic bytes if content provided (Security: prevent MIME spoofing)
    if file_content is not None:
        magic_result = validate_magic_bytes(file_content, mime_type)
        if not magic_result.is_valid:
            return magic_result

    # Validate size
    size_result = validate_file_size(size, mime_type)
    if not size_result.is_valid:
        return size_result

    logger.debug(
        "File validation passed",
        extra={
            "file_name": filename,
            "mime_type": mime_type,
            "size_bytes": size,
            "magic_validated": file_content is not None,
        },
    )

    return FileValidationResult(is_valid=True)
