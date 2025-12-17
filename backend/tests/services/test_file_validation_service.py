"""
Tests for File Validation Service (Story 3.1, Task 9.3).

Tests:
- MIME type validation against whitelist (AC: #2, #10)
- File size validation with type-specific limits (AC: #1, #11)
- Filename sanitization for security

References:
- Task 3.6: TEST validation rejects invalid types with INVALID_FILE_TYPE
- Task 3.7: TEST validation rejects oversized files with FILE_TOO_LARGE
"""


from app.services.file_validation_service import (
    get_safe_filename,
    get_size_limit_for_mime_type,
    validate_file,
    validate_file_size,
    validate_filename,
    validate_mime_type,
)


class TestValidateMimeType:
    """Tests for MIME type validation (AC: #2, #10)."""

    def test_valid_pdf_accepted(self) -> None:
        """Valid PDF MIME type is accepted."""
        result = validate_mime_type("application/pdf")
        assert result.is_valid
        assert result.error_code is None

    def test_valid_video_mp4_accepted(self) -> None:
        """Valid video/mp4 MIME type is accepted."""
        result = validate_mime_type("video/mp4")
        assert result.is_valid

    def test_valid_image_jpeg_accepted(self) -> None:
        """Valid image/jpeg MIME type is accepted."""
        result = validate_mime_type("image/jpeg")
        assert result.is_valid

    def test_valid_audio_mpeg_accepted(self) -> None:
        """Valid audio/mpeg MIME type is accepted."""
        result = validate_mime_type("audio/mpeg")
        assert result.is_valid

    def test_valid_json_accepted(self) -> None:
        """Valid application/json MIME type is accepted."""
        result = validate_mime_type("application/json")
        assert result.is_valid

    def test_invalid_exe_rejected(self) -> None:
        """Invalid application/x-msdownload (exe) is rejected (AC: #10)."""
        result = validate_mime_type("application/x-msdownload")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_TYPE"
        assert "application/x-msdownload" in (result.error_message or "")

    def test_invalid_script_rejected(self) -> None:
        """Invalid application/javascript is rejected."""
        result = validate_mime_type("application/javascript")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_invalid_octet_stream_rejected(self) -> None:
        """Invalid application/octet-stream is rejected (generic binary)."""
        result = validate_mime_type("application/octet-stream")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_empty_mime_type_rejected(self) -> None:
        """Empty MIME type is rejected."""
        result = validate_mime_type("")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_mime_type_case_insensitive(self) -> None:
        """MIME type validation is case-insensitive."""
        result = validate_mime_type("APPLICATION/PDF")
        assert result.is_valid

    def test_mime_type_with_whitespace(self) -> None:
        """MIME type with whitespace is handled."""
        result = validate_mime_type("  application/pdf  ")
        assert result.is_valid


class TestValidateFileSize:
    """Tests for file size validation (AC: #1, #11)."""

    def test_valid_small_file_accepted(self) -> None:
        """Small file within limits is accepted."""
        result = validate_file_size(1024, "application/pdf")  # 1KB
        assert result.is_valid

    def test_video_under_limit_accepted(self) -> None:
        """Video under 10GB limit is accepted."""
        result = validate_file_size(5 * 1024 * 1024 * 1024, "video/mp4")  # 5GB
        assert result.is_valid

    def test_video_over_limit_rejected(self) -> None:
        """Video over 10GB limit is rejected (AC: #11)."""
        result = validate_file_size(11 * 1024 * 1024 * 1024, "video/mp4")  # 11GB
        assert not result.is_valid
        assert result.error_code == "FILE_TOO_LARGE"

    def test_image_under_limit_accepted(self) -> None:
        """Image under 500MB limit is accepted."""
        result = validate_file_size(100 * 1024 * 1024, "image/jpeg")  # 100MB
        assert result.is_valid

    def test_image_over_limit_rejected(self) -> None:
        """Image over 500MB limit is rejected (AC: #11)."""
        result = validate_file_size(600 * 1024 * 1024, "image/jpeg")  # 600MB
        assert not result.is_valid
        assert result.error_code == "FILE_TOO_LARGE"
        assert result.details is not None
        assert result.details["mime_type"] == "image/jpeg"

    def test_default_type_under_limit_accepted(self) -> None:
        """File under default 5GB limit is accepted."""
        result = validate_file_size(4 * 1024 * 1024 * 1024, "application/pdf")  # 4GB
        assert result.is_valid

    def test_default_type_over_limit_rejected(self) -> None:
        """File over default 5GB limit is rejected."""
        result = validate_file_size(6 * 1024 * 1024 * 1024, "application/pdf")  # 6GB
        assert not result.is_valid
        assert result.error_code == "FILE_TOO_LARGE"

    def test_zero_size_rejected(self) -> None:
        """Empty file (0 bytes) is rejected."""
        result = validate_file_size(0, "application/pdf")
        assert not result.is_valid
        assert result.error_code == "EMPTY_FILE"

    def test_negative_size_rejected(self) -> None:
        """Negative size is rejected."""
        result = validate_file_size(-1, "application/pdf")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_SIZE"


class TestGetSizeLimitForMimeType:
    """Tests for size limit calculation by MIME type."""

    def test_video_limit_is_10gb(self) -> None:
        """Video types have 10GB limit."""
        assert get_size_limit_for_mime_type("video/mp4") == 10 * 1024 * 1024 * 1024
        assert get_size_limit_for_mime_type("video/webm") == 10 * 1024 * 1024 * 1024

    def test_image_limit_is_500mb(self) -> None:
        """Image types have 500MB limit."""
        assert get_size_limit_for_mime_type("image/jpeg") == 500 * 1024 * 1024
        assert get_size_limit_for_mime_type("image/png") == 500 * 1024 * 1024

    def test_audio_limit_is_100mb(self) -> None:
        """Audio types have 100MB limit (Story 3.4, AC: #5)."""
        assert get_size_limit_for_mime_type("audio/mpeg") == 100 * 1024 * 1024
        assert get_size_limit_for_mime_type("audio/wav") == 100 * 1024 * 1024
        assert get_size_limit_for_mime_type("audio/ogg") == 100 * 1024 * 1024

    def test_default_limit_is_5gb(self) -> None:
        """Other types have 5GB default limit."""
        assert get_size_limit_for_mime_type("application/pdf") == 5 * 1024 * 1024 * 1024
        assert (
            get_size_limit_for_mime_type("application/json") == 5 * 1024 * 1024 * 1024
        )


class TestGetSafeFilename:
    """Tests for filename sanitization (OWASP A3:2021)."""

    def test_normal_filename_unchanged(self) -> None:
        """Normal filename is kept."""
        assert get_safe_filename("document.pdf") == "document.pdf"

    def test_path_traversal_removed(self) -> None:
        """Path traversal attempts are sanitized."""
        assert ".." not in get_safe_filename("../../../etc/passwd")
        assert "/" not in get_safe_filename("/etc/passwd")
        assert "\\" not in get_safe_filename("..\\..\\windows\\system32")

    def test_null_bytes_removed(self) -> None:
        """Null bytes are removed."""
        assert "\x00" not in get_safe_filename("file\x00.pdf")

    def test_special_chars_replaced(self) -> None:
        """Special characters are replaced with underscores."""
        result = get_safe_filename("file name!@#$.pdf")
        assert " " not in result or "_" in result  # Spaces handled

    def test_empty_filename_handled(self) -> None:
        """Empty filename returns default."""
        assert get_safe_filename("") == "unnamed_file"

    def test_dot_only_handled(self) -> None:
        """Single dot filename returns default."""
        assert get_safe_filename(".") == "unnamed_file"

    def test_long_filename_truncated(self) -> None:
        """Filename over 255 chars is truncated."""
        long_name = "a" * 300 + ".pdf"
        result = get_safe_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".pdf")


class TestValidateFilename:
    """Tests for filename validation."""

    def test_valid_filename_accepted(self) -> None:
        """Valid filename is accepted."""
        result = validate_filename("document.pdf")
        assert result.is_valid

    def test_empty_filename_rejected(self) -> None:
        """Empty filename is rejected."""
        result = validate_filename("")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILENAME"

    def test_path_traversal_rejected(self) -> None:
        """Path traversal attempts are rejected."""
        result = validate_filename("../../../etc/passwd")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILENAME"
        assert result.details is not None
        assert "file_name" in result.details

    def test_forward_slash_rejected(self) -> None:
        """Forward slash is rejected."""
        result = validate_filename("path/to/file.pdf")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILENAME"
        assert result.details is not None

    def test_backslash_rejected(self) -> None:
        """Backslash is rejected."""
        result = validate_filename("path\\to\\file.pdf")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILENAME"
        assert result.details is not None

    def test_long_filename_rejected(self) -> None:
        """Filename over 255 chars is rejected."""
        long_name = "a" * 300
        result = validate_filename(long_name)
        assert not result.is_valid
        assert result.error_code == "FILENAME_TOO_LONG"


class TestValidateMagicBytes:
    """Tests for magic bytes validation (Security: prevent MIME spoofing)."""

    def test_valid_pdf_magic_accepted(self) -> None:
        """Valid PDF with correct magic bytes is accepted."""
        from app.services.file_validation_service import validate_magic_bytes

        pdf_content = b"%PDF-1.4 test content"
        result = validate_magic_bytes(pdf_content, "application/pdf")
        assert result.is_valid

    def test_valid_jpeg_magic_accepted(self) -> None:
        """Valid JPEG with correct magic bytes is accepted."""
        from app.services.file_validation_service import validate_magic_bytes

        jpeg_content = b"\xff\xd8\xff\xe0 JFIF content"
        result = validate_magic_bytes(jpeg_content, "image/jpeg")
        assert result.is_valid

    def test_valid_png_magic_accepted(self) -> None:
        """Valid PNG with correct magic bytes is accepted."""
        from app.services.file_validation_service import validate_magic_bytes

        png_content = b"\x89PNG\r\n\x1a\n additional content"
        result = validate_magic_bytes(png_content, "image/png")
        assert result.is_valid

    def test_spoofed_pdf_rejected(self) -> None:
        """Executable disguised as PDF is rejected (MIME spoofing)."""
        from app.services.file_validation_service import validate_magic_bytes

        exe_content = b"MZ\x90\x00 executable content"  # EXE magic bytes
        result = validate_magic_bytes(exe_content, "application/pdf")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_TYPE"
        assert result.details is not None
        assert result.details["reason"] == "magic_bytes_mismatch"

    def test_spoofed_jpeg_rejected(self) -> None:
        """Non-JPEG disguised as JPEG is rejected."""
        from app.services.file_validation_service import validate_magic_bytes

        text_content = b"This is plain text, not an image"
        result = validate_magic_bytes(text_content, "image/jpeg")
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_json_no_magic_check(self) -> None:
        """JSON files pass without magic check (text-based)."""
        from app.services.file_validation_service import validate_magic_bytes

        json_content = b'{"key": "value"}'
        result = validate_magic_bytes(json_content, "application/json")
        assert result.is_valid

    def test_text_plain_no_magic_check(self) -> None:
        """Plain text files pass without magic check."""
        from app.services.file_validation_service import validate_magic_bytes

        text_content = b"Just some text content"
        result = validate_magic_bytes(text_content, "text/plain")
        assert result.is_valid

    def test_unknown_mime_type_passes(self) -> None:
        """Unknown MIME types without defined signatures pass."""
        from app.services.file_validation_service import validate_magic_bytes

        content = b"random content"
        result = validate_magic_bytes(content, "application/x-custom-type")
        assert result.is_valid


class TestValidateFile:
    """Tests for complete file validation (AC: #1, #2, #10, #11)."""

    def test_valid_pdf_accepted(self) -> None:
        """Valid PDF file is accepted."""
        result = validate_file("document.pdf", "application/pdf", 1024)
        assert result.is_valid

    def test_valid_video_accepted(self) -> None:
        """Valid video file is accepted."""
        result = validate_file("lecture.mp4", "video/mp4", 100 * 1024 * 1024)
        assert result.is_valid

    def test_invalid_mime_rejected_first(self) -> None:
        """Invalid MIME type is detected and rejected."""
        # Use a non-dangerous filename to test MIME validation specifically
        result = validate_file("document.xyz", "application/x-unknown-type", 1024)
        assert not result.is_valid
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_dangerous_filename_rejected_first(self) -> None:
        """Dangerous filename is rejected before MIME validation (Story 3.4, AC: #9)."""
        result = validate_file("malware.exe", "application/x-msdownload", 1024)
        assert not result.is_valid
        assert result.error_code == "DANGEROUS_FILENAME"

    def test_oversized_file_rejected(self) -> None:
        """Oversized file is rejected after MIME validation."""
        result = validate_file("huge.jpg", "image/jpeg", 600 * 1024 * 1024)
        assert not result.is_valid
        assert result.error_code == "FILE_TOO_LARGE"

    def test_invalid_filename_rejected_first(self) -> None:
        """Invalid filename is rejected before other validations."""
        result = validate_file("../../../etc/passwd", "application/pdf", 1024)
        assert not result.is_valid
        assert result.error_code == "INVALID_FILENAME"

    def test_valid_file_with_magic_bytes(self) -> None:
        """Valid file with correct magic bytes passes full validation."""
        pdf_content = b"%PDF-1.4 test content"
        result = validate_file(
            "document.pdf",
            "application/pdf",
            len(pdf_content),
            file_content=pdf_content,
        )
        assert result.is_valid

    def test_spoofed_file_with_magic_bytes_rejected(self) -> None:
        """File with executable magic bytes is rejected (Story 3.4, AC: #10)."""
        exe_content = b"MZ\x90\x00 executable content"
        result = validate_file(
            "document.pdf",
            "application/pdf",
            len(exe_content),
            file_content=exe_content,
        )
        assert not result.is_valid
        # Executable detection is a security-critical check and should be specific
        assert result.error_code == "EXECUTABLE_DETECTED"
