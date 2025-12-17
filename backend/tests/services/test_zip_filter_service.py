"""
Tests for ZIP File Filter Service (Story 3.3, Task 9.3).

Tests:
- System file filtering (AC: #4)
- Directory filtering
- Path traversal prevention (security)
- Case-insensitive matching for Windows compatibility

References:
- Task 2.6: TEST all filter patterns with various path formats
"""

import pytest

from app.services.zip_filter_service import (
    SkipReason,
    ZipFilterService,
    get_zip_filter_service,
    sanitize_zip_path,
)


class TestZipFilterServiceSystemFiles:
    """Tests for system file filtering (AC: #4)."""

    def test_ds_store_filtered(self) -> None:
        """.DS_Store files are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry(".DS_Store")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_ds_store_in_subfolder_filtered(self) -> None:
        """.DS_Store in subfolders are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("documents/.DS_Store")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_macosx_folder_filtered(self) -> None:
        """__MACOSX/ folder contents are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("__MACOSX/._document.pdf")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_macosx_nested_filtered(self) -> None:
        """Nested __MACOSX/ paths are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("folder/__MACOSX/._file.txt")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_thumbs_db_filtered(self) -> None:
        """Thumbs.db files are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("Thumbs.db")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_git_folder_filtered(self) -> None:
        """.git/ folder contents are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry(".git/config")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_desktop_ini_filtered(self) -> None:
        """desktop.ini files are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("desktop.ini")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_tmp_files_filtered(self) -> None:
        """*.tmp files are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("document.tmp")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_office_temp_files_filtered(self) -> None:
        """Office temp files (~$*) are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("~$document.docx")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_vim_swap_files_filtered(self) -> None:
        """Vim swap files (*.swp, *.swo) are filtered."""
        service = ZipFilterService()

        result = service.should_skip_entry("document.txt.swp")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

        result = service.should_skip_entry("document.txt.swo")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_node_modules_filtered(self) -> None:
        """node_modules/ contents are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("node_modules/package/index.js")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_pycache_filtered(self) -> None:
        """__pycache__/ contents are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("__pycache__/module.cpython-310.pyc")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE

    def test_pyc_files_filtered(self) -> None:
        """*.pyc files are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("module.pyc")
        assert result.should_skip
        assert result.reason == SkipReason.SYSTEM_FILE


class TestZipFilterServiceCaseInsensitive:
    """Tests for case-insensitive matching (Windows compatibility)."""

    def test_ds_store_case_insensitive(self) -> None:
        """.DS_Store matching is case-insensitive."""
        service = ZipFilterService()

        result = service.should_skip_entry(".ds_store")
        assert result.should_skip

        result = service.should_skip_entry(".DS_STORE")
        assert result.should_skip

    def test_thumbs_db_case_insensitive(self) -> None:
        """Thumbs.db matching is case-insensitive."""
        service = ZipFilterService()

        result = service.should_skip_entry("thumbs.db")
        assert result.should_skip

        result = service.should_skip_entry("THUMBS.DB")
        assert result.should_skip

    def test_desktop_ini_case_insensitive(self) -> None:
        """desktop.ini matching is case-insensitive."""
        service = ZipFilterService()

        result = service.should_skip_entry("DESKTOP.INI")
        assert result.should_skip

        result = service.should_skip_entry("Desktop.ini")
        assert result.should_skip


class TestZipFilterServiceDirectories:
    """Tests for directory filtering."""

    def test_directory_entry_filtered(self) -> None:
        """Directory entries (ending with /) are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("documents/")
        assert result.should_skip
        assert result.reason == SkipReason.DIRECTORY

    def test_nested_directory_filtered(self) -> None:
        """Nested directory entries are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("level1/level2/level3/")
        assert result.should_skip
        assert result.reason == SkipReason.DIRECTORY


class TestZipFilterServiceSecurity:
    """Tests for security-related filtering."""

    def test_path_traversal_filtered(self) -> None:
        """Path traversal attempts are filtered."""
        service = ZipFilterService()

        result = service.should_skip_entry("../../../etc/passwd")
        assert result.should_skip
        assert result.reason == SkipReason.PATH_TRAVERSAL

        result = service.should_skip_entry("folder/../../../secret.txt")
        assert result.should_skip
        assert result.reason == SkipReason.PATH_TRAVERSAL

    def test_absolute_path_filtered(self) -> None:
        """Absolute paths are filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("/etc/passwd")
        assert result.should_skip
        assert result.reason == SkipReason.PATH_TRAVERSAL

    def test_empty_name_filtered(self) -> None:
        """Empty entry names are filtered."""
        service = ZipFilterService()

        result = service.should_skip_entry("")
        assert result.should_skip
        assert result.reason == SkipReason.EMPTY_NAME

        result = service.should_skip_entry("   ")
        assert result.should_skip
        assert result.reason == SkipReason.EMPTY_NAME

    def test_backslash_path_normalized(self) -> None:
        """Windows-style backslash paths are normalized."""
        service = ZipFilterService()
        # The path traversal check works after normalization
        result = service.should_skip_entry("..\\..\\secret.txt")
        assert result.should_skip
        assert result.reason == SkipReason.PATH_TRAVERSAL


class TestZipFilterServiceValidFiles:
    """Tests for valid files that should NOT be filtered."""

    def test_valid_pdf_not_filtered(self) -> None:
        """Valid PDF files are not filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("document.pdf")
        assert not result.should_skip

    def test_valid_image_not_filtered(self) -> None:
        """Valid image files are not filtered."""
        service = ZipFilterService()

        result = service.should_skip_entry("photo.jpg")
        assert not result.should_skip

        result = service.should_skip_entry("diagram.png")
        assert not result.should_skip

    def test_valid_video_not_filtered(self) -> None:
        """Valid video files are not filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("lecture.mp4")
        assert not result.should_skip

    def test_valid_nested_file_not_filtered(self) -> None:
        """Valid nested files are not filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("books/grade-8/math/chapter1.pdf")
        assert not result.should_skip

    def test_valid_file_with_special_chars_not_filtered(self) -> None:
        """Valid files with special characters in name are not filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("chapter_1-intro.pdf")
        assert not result.should_skip

    def test_file_named_store_not_filtered(self) -> None:
        """Files with 'store' in name (not .DS_Store) are not filtered."""
        service = ZipFilterService()
        result = service.should_skip_entry("my_data_store.json")
        assert not result.should_skip


class TestZipFilterServiceFilterEntries:
    """Tests for bulk filtering of entries."""

    def test_filter_mixed_entries(self) -> None:
        """Filtering a mix of valid and invalid entries works correctly."""
        service = ZipFilterService()

        entries = [
            "document.pdf",
            ".DS_Store",
            "images/photo.jpg",
            "__MACOSX/._document.pdf",
            "data/report.json",
            "Thumbs.db",
            "videos/",
        ]

        valid, skipped = service.filter_entries(entries)

        assert len(valid) == 3
        assert "document.pdf" in valid
        assert "images/photo.jpg" in valid
        assert "data/report.json" in valid

        assert len(skipped) == 4
        skipped_names = [name for name, _ in skipped]
        assert ".DS_Store" in skipped_names
        assert "__MACOSX/._document.pdf" in skipped_names
        assert "Thumbs.db" in skipped_names
        assert "videos/" in skipped_names

    def test_filter_all_valid_entries(self) -> None:
        """Filtering all valid entries returns all as valid."""
        service = ZipFilterService()

        entries = ["doc1.pdf", "doc2.pdf", "images/photo.jpg"]
        valid, skipped = service.filter_entries(entries)

        assert len(valid) == 3
        assert len(skipped) == 0

    def test_filter_all_invalid_entries(self) -> None:
        """Filtering all invalid entries returns all as skipped."""
        service = ZipFilterService()

        entries = [".DS_Store", "__MACOSX/._file", "Thumbs.db"]
        valid, skipped = service.filter_entries(entries)

        assert len(valid) == 0
        assert len(skipped) == 3


class TestSanitizeZipPath:
    """Tests for ZIP path sanitization."""

    def test_simple_path_unchanged(self) -> None:
        """Simple paths are unchanged."""
        assert sanitize_zip_path("document.pdf") == "document.pdf"

    def test_nested_path_preserved(self) -> None:
        """Nested folder structure is preserved."""
        assert sanitize_zip_path("books/math/chapter1.pdf") == "books/math/chapter1.pdf"

    def test_backslash_normalized(self) -> None:
        """Windows backslash paths are normalized to forward slashes."""
        assert (
            sanitize_zip_path("books\\math\\chapter1.pdf") == "books/math/chapter1.pdf"
        )

    def test_parent_refs_removed(self) -> None:
        """Parent directory references are removed."""
        assert sanitize_zip_path("folder/../file.pdf") == "folder/file.pdf"

    def test_absolute_path_made_relative(self) -> None:
        """Absolute paths are made relative."""
        result = sanitize_zip_path("/root/file.pdf")
        assert not result.startswith("/")
        assert result == "root/file.pdf"

    def test_dot_segment_removed(self) -> None:
        """Single dot segments are removed."""
        assert sanitize_zip_path("./folder/./file.pdf") == "folder/file.pdf"

    def test_empty_path_raises(self) -> None:
        """Empty path raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_zip_path("")

    def test_traversal_only_path_raises(self) -> None:
        """Path with only traversal components raises ValueError."""
        with pytest.raises(ValueError, match="empty path after sanitization"):
            sanitize_zip_path("../../..")


class TestGetZipFilterService:
    """Tests for the module-level service getter."""

    def test_returns_service_instance(self) -> None:
        """get_zip_filter_service returns a ZipFilterService instance."""
        service = get_zip_filter_service()
        assert isinstance(service, ZipFilterService)

    def test_returns_same_instance(self) -> None:
        """get_zip_filter_service returns the same instance (singleton)."""
        service1 = get_zip_filter_service()
        service2 = get_zip_filter_service()
        assert service1 is service2


class TestCustomPatterns:
    """Tests for custom filter patterns."""

    def test_custom_patterns_used(self) -> None:
        """Custom patterns override defaults."""
        custom_patterns = [r"\.custom$", r"ignore_me/"]

        service = ZipFilterService(patterns=custom_patterns)

        # Custom pattern should match
        result = service.should_skip_entry("file.custom")
        assert result.should_skip

        # Default pattern should NOT match (not in custom list)
        result = service.should_skip_entry(".DS_Store")
        assert not result.should_skip
