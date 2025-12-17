"""
ZIP File Filter Service (Story 3.3, Task 2).

Provides filtering of system files during ZIP extraction (AC: #4).
- .DS_Store (macOS directory metadata)
- __MACOSX/ (macOS resource forks)
- Thumbs.db (Windows thumbnail cache)
- .git/ (Git repository data)
- desktop.ini (Windows folder settings)
- Temporary files (*.tmp, ~$*, *.swp)

References:
- AC: #4 (system files automatically filtered during extraction)
- FR3 (filter system files from ZIP archives)
"""

import logging
import re
from enum import Enum
from typing import NamedTuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class SkipReason(str, Enum):
    """Reason for skipping a ZIP entry."""

    SYSTEM_FILE = "system_file"
    DIRECTORY = "directory"
    EMPTY_NAME = "empty_name"
    PATH_TRAVERSAL = "path_traversal"


class FilterResult(NamedTuple):
    """Result of filtering a ZIP entry."""

    should_skip: bool
    reason: SkipReason | None = None
    matched_pattern: str | None = None


class ZipFilterService:
    """
    Service for filtering ZIP entries during extraction.

    Filters system files, directories, and entries with security issues.
    Uses patterns from configuration with case-insensitive matching.
    """

    def __init__(self, patterns: list[str] | None = None):
        """
        Initialize filter service with patterns.

        Args:
            patterns: List of regex patterns to filter. If None, uses config patterns.
        """
        self._patterns = patterns or settings.FILTERED_ZIP_PATTERNS
        # Compile patterns with case-insensitive flag for Windows compatibility
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self._patterns
        ]

    def should_skip_entry(self, entry_name: str) -> FilterResult:
        """
        Check if ZIP entry should be skipped during extraction.

        Filters:
        - System files matching configured patterns (case-insensitive)
        - Directory entries
        - Empty names
        - Path traversal attempts (security)

        Args:
            entry_name: Name/path of the ZIP entry

        Returns:
            FilterResult with skip decision and reason
        """
        # Empty name check
        if not entry_name or not entry_name.strip():
            logger.debug("Skipping entry with empty name")
            return FilterResult(
                should_skip=True,
                reason=SkipReason.EMPTY_NAME,
            )

        # Normalize path separators for consistent matching
        normalized_name = entry_name.replace("\\", "/")

        # Path traversal check (security)
        if ".." in normalized_name or normalized_name.startswith("/"):
            logger.warning(
                "Path traversal attempt in ZIP entry",
                extra={"entry_name": entry_name},
            )
            return FilterResult(
                should_skip=True,
                reason=SkipReason.PATH_TRAVERSAL,
            )

        # Directory check (entries ending with /)
        if normalized_name.endswith("/"):
            logger.debug(
                "Skipping directory entry",
                extra={"entry_name": entry_name},
            )
            return FilterResult(
                should_skip=True,
                reason=SkipReason.DIRECTORY,
            )

        # Pattern matching (case-insensitive)
        for pattern, compiled in zip(
            self._patterns, self._compiled_patterns, strict=True
        ):
            if compiled.search(normalized_name):
                logger.info(
                    "Skipping system file",
                    extra={
                        "entry_name": entry_name,
                        "matched_pattern": pattern,
                    },
                )
                return FilterResult(
                    should_skip=True,
                    reason=SkipReason.SYSTEM_FILE,
                    matched_pattern=pattern,
                )

        # Entry passed all filters
        return FilterResult(should_skip=False)

    def filter_entries(
        self, entry_names: list[str]
    ) -> tuple[list[str], list[tuple[str, SkipReason]]]:
        """
        Filter a list of ZIP entry names.

        Args:
            entry_names: List of entry names to filter

        Returns:
            Tuple of (valid_entries, skipped_entries_with_reasons)
        """
        valid_entries: list[str] = []
        skipped_entries: list[tuple[str, SkipReason]] = []

        for name in entry_names:
            result = self.should_skip_entry(name)
            if result.should_skip:
                skipped_entries.append((name, result.reason or SkipReason.SYSTEM_FILE))
            else:
                valid_entries.append(name)

        logger.info(
            "Filtered ZIP entries",
            extra={
                "total_entries": len(entry_names),
                "valid_count": len(valid_entries),
                "skipped_count": len(skipped_entries),
            },
        )

        return valid_entries, skipped_entries


def sanitize_zip_path(entry_name: str) -> str:
    """
    Sanitize ZIP entry path for safe storage.

    Removes path traversal attempts and normalizes path separators.
    Used after filtering to ensure safe storage paths.

    Args:
        entry_name: Original ZIP entry name

    Returns:
        Sanitized path safe for storage as MinIO prefix

    Raises:
        ValueError: If path cannot be sanitized to a valid name
    """
    if not entry_name:
        raise ValueError("Entry name cannot be empty")

    # Normalize path separators
    safe_path = entry_name.replace("\\", "/")

    # Remove any parent directory references and absolute path prefixes
    parts = safe_path.split("/")
    safe_parts = [p for p in parts if p and p != ".." and p != "."]

    if not safe_parts:
        raise ValueError(
            f"Entry name '{entry_name}' results in empty path after sanitization"
        )

    result = "/".join(safe_parts)

    logger.debug(
        "Sanitized ZIP path",
        extra={
            "original": entry_name,
            "sanitized": result,
        },
    )

    return result


# Module-level instance for convenience
_default_filter_service: ZipFilterService | None = None


def get_zip_filter_service() -> ZipFilterService:
    """
    Get the default ZIP filter service instance.

    Returns:
        Configured ZipFilterService instance
    """
    global _default_filter_service
    if _default_filter_service is None:
        _default_filter_service = ZipFilterService()
    return _default_filter_service
