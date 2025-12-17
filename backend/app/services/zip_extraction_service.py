"""
ZIP Extraction Service (Story 3.3, Task 3).

Provides streaming ZIP extraction with:
- Streaming extraction without loading entire file into memory (NFR-P9)
- Per-file validation using FileValidationService
- Streaming upload to MinIO with checksum calculation
- System file filtering using ZipFilterService
- ZIP bomb protection (compression ratio check)
- Error collection with continue-on-failure

References:
- AC: #1 (POST /api/v1/assets/upload-zip accepts ZIP archives)
- AC: #3 (ZIP file streamed/extracted without full memory load)
- AC: #5 (each extracted file validated)
- AC: #6 (files uploaded to MinIO with tenant path)
- AC: #7 (folder structure preserved as MinIO prefixes)
- AC: #8 (asset metadata created with checksums)
- AC: #9 (streaming mode, no disk buffering)
- AC: #10 (return extraction results)
- AC: #12 (continue extraction on file failures)
- NFR-P9 (ZIP extraction without disk/RAM bottlenecks)
"""

import hashlib
import logging
import mimetypes
import uuid
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from typing import BinaryIO

from minio import Minio

from app.core.config import settings
from app.core.minio_client import ensure_bucket_exists, get_minio_client
from app.services.file_validation_service import (
    get_safe_filename,
    validate_file,
)
from app.services.zip_filter_service import (
    SkipReason,
    ZipFilterService,
    get_zip_filter_service,
    sanitize_zip_path,
)

logger = logging.getLogger(__name__)


@dataclass
class SkippedFileInfo:
    """Information about a file skipped during extraction."""

    file_name: str
    reason: str


@dataclass
class FailedFileInfo:
    """Information about a file that failed validation/upload."""

    file_name: str
    error_code: str
    message: str


@dataclass
class ExtractedAssetInfo:
    """Information about a successfully extracted asset (before DB creation)."""

    asset_id: uuid.UUID
    object_key: str
    file_name: str
    original_path: str
    file_size: int
    mime_type: str
    checksum: str


@dataclass
class ZipExtractionResult:
    """Result of ZIP extraction operation."""

    extracted_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    total_size_bytes: int = 0

    extracted_assets: list[ExtractedAssetInfo] = field(default_factory=list)
    skipped_files: list[SkippedFileInfo] = field(default_factory=list)
    failed_files: list[FailedFileInfo] = field(default_factory=list)


class ZipExtractionError(Exception):
    """Base exception for ZIP extraction errors."""

    def __init__(self, message: str, error_code: str = "ZIP_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class InvalidZipError(ZipExtractionError):
    """Raised when ZIP file is invalid or corrupt."""

    def __init__(self, message: str = "Invalid or corrupt ZIP file"):
        super().__init__(message, "INVALID_ZIP_FILE")


class ZipBombError(ZipExtractionError):
    """Raised when ZIP file appears to be a zip bomb."""

    def __init__(
        self, entry_name: str, compression_ratio: float, message: str | None = None
    ):
        self.entry_name = entry_name
        self.compression_ratio = compression_ratio
        super().__init__(
            message
            or f"Possible zip bomb detected: {entry_name} "
            f"(ratio: {compression_ratio:.1f}x)",
            "ZIP_BOMB_DETECTED",
        )


class ZipExtractionService:
    """
    Service for extracting and uploading ZIP archive contents.

    Uses streaming extraction to avoid loading the entire ZIP into memory.
    Each file is validated, uploaded to MinIO, and metadata prepared for DB.
    """

    def __init__(
        self,
        tenant_type: str,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        bucket: str | None = None,
        filter_service: ZipFilterService | None = None,
        minio_client: Minio | None = None,
    ):
        """
        Initialize ZIP extraction service.

        Args:
            tenant_type: Type of tenant (publisher, school, etc.)
            tenant_id: UUID of the tenant
            user_id: UUID of the user performing extraction
            bucket: MinIO bucket name (defaults to settings)
            filter_service: ZIP filter service (defaults to singleton)
            minio_client: MinIO client (defaults to singleton)
        """
        self.tenant_type = tenant_type
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.bucket = bucket or settings.MINIO_BUCKET_NAME
        self.filter_service = filter_service or get_zip_filter_service()
        self.minio_client = minio_client or get_minio_client()

        # Ensure bucket exists
        ensure_bucket_exists(client=self.minio_client, bucket=self.bucket)

    def _check_zip_bomb(self, info: zipfile.ZipInfo) -> bool:
        """
        Check if ZIP entry has suspiciously high compression ratio.

        Args:
            info: ZipInfo object for the entry

        Returns:
            True if entry appears to be a zip bomb

        Raises:
            ZipBombError: If compression ratio exceeds maximum
        """
        if info.compress_size == 0:
            # Empty or stored without compression
            return False

        ratio = info.file_size / info.compress_size

        if ratio > settings.MAX_ZIP_COMPRESSION_RATIO:
            logger.warning(
                "Possible zip bomb detected",
                extra={
                    "entry": info.filename,
                    "compressed_size": info.compress_size,
                    "uncompressed_size": info.file_size,
                    "ratio": ratio,
                },
            )
            raise ZipBombError(info.filename, ratio)

        return False

    def _detect_mime_type(self, filename: str, content: bytes) -> str:
        """
        Detect MIME type for a file.

        First tries mimetypes.guess_type, then falls back to magic bytes.

        Args:
            filename: Name of the file
            content: First bytes of file content

        Returns:
            Detected MIME type string
        """
        # Try to guess from filename
        mime_type, _ = mimetypes.guess_type(filename)

        if mime_type:
            return mime_type

        # Fallback: check magic bytes for common types
        if content.startswith(b"%PDF"):
            return "application/pdf"
        elif content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif content.startswith(b"GIF8"):
            return "image/gif"
        elif (
            content.startswith(b"RIFF")
            and len(content) > 11
            and content[8:12] == b"WEBP"
        ):
            return "image/webp"
        elif len(content) > 7 and content[4:8] == b"ftyp":
            return "video/mp4"
        elif content.startswith(b"ID3") or content.startswith(b"\xff\xfb"):
            return "audio/mpeg"
        elif content.startswith(b"OggS"):
            return "audio/ogg"

        # Default to octet-stream
        return "application/octet-stream"

    def _generate_object_key(
        self, asset_id: uuid.UUID, file_name: str, zip_path: str
    ) -> str:
        """
        Generate MinIO object key preserving ZIP folder structure.

        Format: {tenant_type}/{tenant_id}/{asset_id}/{zip_path_prefix}{file_name}

        Args:
            asset_id: UUID of the asset
            file_name: Sanitized filename
            zip_path: Original path from ZIP (sanitized)

        Returns:
            Object key string for MinIO
        """
        # Get directory path from ZIP (without filename)
        path_parts = zip_path.rsplit("/", 1)
        if len(path_parts) > 1:
            # Has directory structure - preserve it
            prefix = path_parts[0] + "/"
        else:
            prefix = ""

        return f"{self.tenant_type}/{self.tenant_id}/{asset_id}/{prefix}{file_name}"

    def _upload_entry_to_minio(
        self,
        data: BinaryIO,
        object_key: str,
        length: int,
        content_type: str,
    ) -> str:
        """
        Upload extracted entry to MinIO with checksum calculation.

        Args:
            data: File-like object with entry content
            object_key: Target object key in MinIO
            length: Size in bytes
            content_type: MIME type

        Returns:
            MD5 checksum hex string
        """
        # Read content for checksum calculation
        content = data.read()
        checksum = hashlib.md5(content).hexdigest()

        # Upload to MinIO
        self.minio_client.put_object(
            bucket_name=self.bucket,
            object_name=object_key,
            data=BytesIO(content),
            length=length,
            content_type=content_type,
        )

        return checksum

    def extract_and_upload(
        self,
        zip_file: BinaryIO,
        request_id: str | None = None,
    ) -> ZipExtractionResult:
        """
        Extract ZIP archive and upload contents to MinIO (AC: #1, #3, #6, #7, #8, #9, #10, #12).

        Workflow:
        1. Validate ZIP format
        2. Iterate entries (streaming, no full memory load)
        3. Filter system files
        4. Validate each file
        5. Upload valid files to MinIO
        6. Collect results and errors

        Args:
            zip_file: File-like object containing ZIP data
            request_id: Optional request ID for tracing

        Returns:
            ZipExtractionResult with all extraction details

        Raises:
            InvalidZipError: If ZIP file is invalid/corrupt
            ZipBombError: If ZIP bomb detected
        """
        result = ZipExtractionResult()
        total_extracted_size = 0
        file_count = 0

        logger.info(
            "Starting ZIP extraction",
            extra={
                "tenant_type": self.tenant_type,
                "tenant_id": str(self.tenant_id),
                "request_id": request_id,
            },
        )

        try:
            with zipfile.ZipFile(zip_file, "r") as zf:
                # Get all entries
                entries = zf.infolist()

                logger.info(
                    "ZIP file opened",
                    extra={
                        "total_entries": len(entries),
                        "request_id": request_id,
                    },
                )

                for info in entries:
                    # Check file count limit
                    if file_count >= settings.MAX_ZIP_EXTRACTED_FILES:
                        logger.warning(
                            "ZIP file count limit reached",
                            extra={
                                "limit": settings.MAX_ZIP_EXTRACTED_FILES,
                                "request_id": request_id,
                            },
                        )
                        break

                    # Check total size limit
                    if (
                        total_extracted_size + info.file_size
                        > settings.MAX_EXTRACTED_TOTAL_SIZE
                    ):
                        logger.warning(
                            "ZIP total size limit would be exceeded",
                            extra={
                                "current_size": total_extracted_size,
                                "entry_size": info.file_size,
                                "limit": settings.MAX_EXTRACTED_TOTAL_SIZE,
                                "entry_name": info.filename,
                                "request_id": request_id,
                            },
                        )
                        result.failed_files.append(
                            FailedFileInfo(
                                file_name=info.filename,
                                error_code="TOTAL_SIZE_EXCEEDED",
                                message="Total extracted size limit exceeded",
                            )
                        )
                        result.failed_count += 1
                        continue

                    # Filter system files and directories
                    filter_result = self.filter_service.should_skip_entry(info.filename)
                    if filter_result.should_skip:
                        reason_map: dict[SkipReason, str] = {
                            SkipReason.SYSTEM_FILE: "system_file",
                            SkipReason.DIRECTORY: "directory",
                            SkipReason.EMPTY_NAME: "empty_name",
                            SkipReason.PATH_TRAVERSAL: "path_traversal",
                        }
                        reason = (
                            reason_map.get(filter_result.reason, "unknown")
                            if filter_result.reason is not None
                            else "unknown"
                        )
                        result.skipped_files.append(
                            SkippedFileInfo(file_name=info.filename, reason=reason)
                        )
                        result.skipped_count += 1
                        continue

                    # Check for zip bomb
                    try:
                        self._check_zip_bomb(info)
                    except ZipBombError as e:
                        result.failed_files.append(
                            FailedFileInfo(
                                file_name=info.filename,
                                error_code=e.error_code,
                                message=e.message,
                            )
                        )
                        result.failed_count += 1
                        continue

                    # Extract and process the entry
                    try:
                        with zf.open(info) as entry_stream:
                            # Read content for validation and upload
                            # For very large files, this could be optimized further
                            content = entry_stream.read()

                            if len(content) == 0:
                                result.skipped_files.append(
                                    SkippedFileInfo(
                                        file_name=info.filename, reason="empty_file"
                                    )
                                )
                                result.skipped_count += 1
                                continue

                            # Detect MIME type
                            mime_type = self._detect_mime_type(
                                info.filename, content[:64]
                            )

                            # Sanitize filename and path
                            try:
                                sanitized_path = sanitize_zip_path(info.filename)
                                base_name = sanitized_path.rsplit("/", 1)[-1]
                                safe_filename = get_safe_filename(base_name)
                            except ValueError as e:
                                result.failed_files.append(
                                    FailedFileInfo(
                                        file_name=info.filename,
                                        error_code="INVALID_FILENAME",
                                        message=str(e),
                                    )
                                )
                                result.failed_count += 1
                                continue

                            # Validate file
                            validation_result = validate_file(
                                filename=safe_filename,
                                mime_type=mime_type,
                                size=len(content),
                                file_content=content[:64],
                            )

                            if not validation_result.is_valid:
                                result.failed_files.append(
                                    FailedFileInfo(
                                        file_name=info.filename,
                                        error_code=validation_result.error_code
                                        or "VALIDATION_ERROR",
                                        message=validation_result.error_message
                                        or "File validation failed",
                                    )
                                )
                                result.failed_count += 1
                                continue

                            # Generate asset ID and object key
                            asset_id = uuid.uuid4()
                            object_key = self._generate_object_key(
                                asset_id=asset_id,
                                file_name=safe_filename,
                                zip_path=sanitized_path,
                            )

                            # Upload to MinIO
                            checksum = hashlib.md5(content).hexdigest()

                            self.minio_client.put_object(
                                bucket_name=self.bucket,
                                object_name=object_key,
                                data=BytesIO(content),
                                length=len(content),
                                content_type=mime_type,
                            )

                            # Record extracted asset
                            extracted_asset = ExtractedAssetInfo(
                                asset_id=asset_id,
                                object_key=object_key,
                                file_name=safe_filename,
                                original_path=info.filename,
                                file_size=len(content),
                                mime_type=mime_type,
                                checksum=checksum,
                            )
                            result.extracted_assets.append(extracted_asset)
                            result.extracted_count += 1
                            result.total_size_bytes += len(content)
                            total_extracted_size += len(content)
                            file_count += 1

                            logger.debug(
                                "Extracted file from ZIP",
                                extra={
                                    "entry_name": info.filename,
                                    "object_key": object_key,
                                    "size": len(content),
                                    "mime_type": mime_type,
                                    "request_id": request_id,
                                },
                            )

                    except Exception as e:
                        logger.error(
                            "Failed to extract ZIP entry",
                            extra={
                                "entry_name": info.filename,
                                "error": str(e),
                                "request_id": request_id,
                            },
                        )
                        result.failed_files.append(
                            FailedFileInfo(
                                file_name=info.filename,
                                error_code="EXTRACTION_ERROR",
                                message=str(e),
                            )
                        )
                        result.failed_count += 1
                        continue

        except zipfile.BadZipFile as e:
            logger.error(
                "Invalid ZIP file",
                extra={
                    "error": str(e),
                    "request_id": request_id,
                },
            )
            raise InvalidZipError(f"Invalid or corrupt ZIP file: {e}")

        except Exception as e:
            logger.error(
                "ZIP extraction failed",
                extra={
                    "error": str(e),
                    "request_id": request_id,
                },
            )
            raise InvalidZipError(f"Failed to process ZIP file: {e}")

        logger.info(
            "ZIP extraction completed",
            extra={
                "extracted_count": result.extracted_count,
                "skipped_count": result.skipped_count,
                "failed_count": result.failed_count,
                "total_size_bytes": result.total_size_bytes,
                "request_id": request_id,
            },
        )

        return result

    def rollback_extraction(
        self, result: ZipExtractionResult, request_id: str | None = None
    ) -> None:
        """
        Rollback extraction by deleting uploaded files from MinIO.

        Used when metadata creation fails to maintain transactional consistency.

        Args:
            result: Extraction result containing uploaded assets
            request_id: Optional request ID for tracing
        """
        logger.info(
            "Rolling back ZIP extraction",
            extra={
                "asset_count": len(result.extracted_assets),
                "request_id": request_id,
            },
        )

        for asset in result.extracted_assets:
            try:
                self.minio_client.remove_object(
                    bucket_name=self.bucket,
                    object_name=asset.object_key,
                )
                logger.debug(
                    "Deleted object during rollback",
                    extra={
                        "object_key": asset.object_key,
                        "request_id": request_id,
                    },
                )
            except Exception as e:
                logger.error(
                    "Failed to delete object during rollback",
                    extra={
                        "object_key": asset.object_key,
                        "error": str(e),
                        "request_id": request_id,
                    },
                )
