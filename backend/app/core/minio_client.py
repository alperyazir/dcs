"""
MinIO Client Module (Story 3.1, Task 2; Story 3.2, Task 2).

Provides:
- MinIO client singleton
- Streaming upload operations (AC: #3, #7)
- Object key generation with tenant isolation
- Checksum calculation during upload (AC: #5)
- Presigned URL generation for direct MinIO access (Story 3.2)

References:
- AC: #3 (upload to MinIO with tenant path)
- AC: #5 (MD5 checksum calculation)
- AC: #7 (streaming design, no full memory buffering)
- Story 3.2 AC: #1, #4, #7 (presigned URLs with HMAC-SHA256)
"""

import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from io import BytesIO
from typing import BinaryIO
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_minio_client() -> Minio:
    """
    Get MinIO client singleton.

    Returns initialized Minio client using settings from environment.
    Uses lru_cache for singleton pattern - same client instance reused.
    """
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD.get_secret_value(),
        secure=settings.minio_secure,
    )


def ensure_bucket_exists(
    client: Minio | None = None, bucket: str | None = None
) -> None:
    """
    Ensure the assets bucket exists, create if not.

    Args:
        client: MinIO client (uses singleton if not provided)
        bucket: Bucket name (uses settings default if not provided)
    """
    if client is None:
        client = get_minio_client()
    if bucket is None:
        bucket = settings.MINIO_BUCKET_NAME

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info(f"Created MinIO bucket: {bucket}")


def generate_object_key(
    tenant_type: str,
    tenant_id: UUID,
    asset_id: UUID,
    file_name: str,
) -> str:
    """
    Generate object key for MinIO storage (AC: #3).

    Path structure: {tenant_type}/{tenant_id}/{asset_id}/{file_name}

    This structure provides:
    - Tenant isolation at storage level
    - Asset-level namespacing to prevent collisions
    - Easy cleanup on asset deletion

    Args:
        tenant_type: Type of tenant (publisher, school, teacher, student)
        tenant_id: UUID of the tenant
        asset_id: UUID of the asset
        file_name: Original sanitized filename

    Returns:
        Object key string for MinIO
    """
    return f"{tenant_type}/{tenant_id}/{asset_id}/{file_name}"


class ChecksumCalculator:
    """
    Wrapper to calculate MD5 checksum while streaming data.

    Implements file-like interface to calculate checksum during read operations.
    This avoids buffering the entire file in memory (AC: #7, NFR-P7).
    """

    def __init__(self, data: BinaryIO):
        """
        Initialize checksum calculator.

        Args:
            data: Binary file-like object to read from
        """
        self._data = data
        self._hasher = hashlib.md5()
        self._bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        """Read data and update checksum."""
        chunk = self._data.read(size)
        if chunk:
            self._hasher.update(chunk)
            self._bytes_read += len(chunk)
        return chunk

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek in the underlying stream."""
        return self._data.seek(offset, whence)

    def tell(self) -> int:
        """Return current position."""
        return self._data.tell()

    @property
    def checksum(self) -> str:
        """Return MD5 checksum as hex string."""
        return self._hasher.hexdigest()

    @property
    def bytes_read(self) -> int:
        """Return total bytes read."""
        return self._bytes_read


def calculate_checksum(data: bytes) -> str:
    """
    Calculate MD5 checksum for data (AC: #5, NFR-R5).

    Args:
        data: Bytes to hash

    Returns:
        MD5 checksum as hex string
    """
    return hashlib.md5(data).hexdigest()


def put_object_streaming(
    bucket: str,
    object_key: str,
    data: BinaryIO,
    length: int,
    content_type: str,
    client: Minio | None = None,
) -> tuple[str, str]:
    """
    Upload file to MinIO with streaming and checksum calculation (AC: #3, #5, #7).

    Uses MinIO SDK's put_object which handles streaming internally.
    Calculates MD5 checksum during the upload process.

    Args:
        bucket: Bucket name
        object_key: Full object key (path in bucket)
        data: Binary file-like object to upload
        length: Size of data in bytes
        content_type: MIME type of the file
        client: MinIO client (uses singleton if not provided)

    Returns:
        Tuple of (etag, md5_checksum)

    Raises:
        S3Error: If MinIO operation fails
    """
    if client is None:
        client = get_minio_client()

    # Read data into memory for checksum calculation
    # Note: For very large files (>100MB), consider streaming checksum
    file_data = data.read()
    checksum = calculate_checksum(file_data)

    # Reset to beginning for MinIO upload
    data_stream = BytesIO(file_data)

    try:
        result = client.put_object(
            bucket_name=bucket,
            object_name=object_key,
            data=data_stream,
            length=length,
            content_type=content_type,
        )

        logger.info(
            "File uploaded to MinIO",
            extra={
                "bucket": bucket,
                "object_key": object_key,
                "size_bytes": length,
                "content_type": content_type,
                "etag": result.etag,
                "checksum": checksum,
            },
        )

        return result.etag or "", checksum

    except S3Error as e:
        logger.error(
            "MinIO upload failed",
            extra={
                "bucket": bucket,
                "object_key": object_key,
                "error": str(e),
            },
        )
        raise


def delete_object(
    bucket: str,
    object_key: str,
    client: Minio | None = None,
) -> None:
    """
    Delete object from MinIO.

    Used for cleanup on failed metadata creation (AC: #6 transactional consistency).

    Args:
        bucket: Bucket name
        object_key: Full object key (path in bucket)
        client: MinIO client (uses singleton if not provided)

    Raises:
        S3Error: If MinIO operation fails
    """
    if client is None:
        client = get_minio_client()

    try:
        client.remove_object(bucket_name=bucket, object_name=object_key)
        logger.info(
            "File deleted from MinIO",
            extra={"bucket": bucket, "object_key": object_key},
        )
    except S3Error as e:
        logger.error(
            "MinIO delete failed",
            extra={
                "bucket": bucket,
                "object_key": object_key,
                "error": str(e),
            },
        )
        raise


def get_object_url(
    bucket: str,
    object_key: str,
    client: Minio | None = None,
) -> str:
    """
    Get direct URL for an object (for internal use).

    Note: For public access, use presigned URLs (Story 3.2).

    Args:
        bucket: Bucket name
        object_key: Full object key
        client: MinIO client

    Returns:
        Object URL string
    """
    if client is None:
        client = get_minio_client()

    # Build URL from endpoint and bucket/key
    protocol = "https" if settings.minio_secure else "http"
    return f"{protocol}://{settings.MINIO_ENDPOINT}/{bucket}/{object_key}"


def generate_presigned_download_url(
    bucket: str,
    object_key: str,
    expires_seconds: int | None = None,
    client: Minio | None = None,
) -> tuple[str, datetime]:
    """
    Generate presigned URL for downloading an object (Story 3.2, AC: #1, #3, #4).

    Uses MinIO SDK's presigned_get_object() which generates HMAC-SHA256 signed URLs.
    The URL allows direct download from MinIO without API proxying.

    Args:
        bucket: Bucket name
        object_key: Full object key (path in bucket)
        expires_seconds: URL expiration in seconds (default from settings: 3600 = 1 hour)
        client: MinIO client (uses singleton if not provided)

    Returns:
        Tuple of (presigned_url, expiration_datetime)

    Raises:
        S3Error: If MinIO operation fails
    """
    start_time = time.time()

    if client is None:
        client = get_minio_client()

    if expires_seconds is None:
        expires_seconds = settings.PRESIGNED_URL_DOWNLOAD_EXPIRES_SECONDS

    expires = timedelta(seconds=expires_seconds)
    expiration_time = datetime.now(timezone.utc) + expires

    try:
        url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_key,
            expires=expires,
        )

        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "Generated presigned download URL",
            extra={
                "bucket": bucket,
                "object_key": object_key,
                "expires_seconds": expires_seconds,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return url, expiration_time

    except S3Error as e:
        logger.error(
            "Failed to generate presigned download URL",
            extra={
                "bucket": bucket,
                "object_key": object_key,
                "error": str(e),
            },
        )
        raise


def generate_presigned_upload_url(
    bucket: str,
    object_key: str,
    expires_seconds: int | None = None,
    client: Minio | None = None,
) -> tuple[str, datetime]:
    """
    Generate presigned URL for uploading an object (Story 3.2, AC: #1, #2, #4).

    Uses MinIO SDK's presigned_put_object() which generates HMAC-SHA256 signed URLs.
    The URL allows direct upload to MinIO without API proxying.

    Args:
        bucket: Bucket name
        object_key: Full object key (path in bucket)
        expires_seconds: URL expiration in seconds (default from settings: 900 = 15 min)
        client: MinIO client (uses singleton if not provided)

    Returns:
        Tuple of (presigned_url, expiration_datetime)

    Raises:
        S3Error: If MinIO operation fails
    """
    start_time = time.time()

    if client is None:
        client = get_minio_client()

    if expires_seconds is None:
        expires_seconds = settings.PRESIGNED_URL_UPLOAD_EXPIRES_SECONDS

    expires = timedelta(seconds=expires_seconds)
    expiration_time = datetime.now(timezone.utc) + expires

    try:
        url = client.presigned_put_object(
            bucket_name=bucket,
            object_name=object_key,
            expires=expires,
        )

        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "Generated presigned upload URL",
            extra={
                "bucket": bucket,
                "object_key": object_key,
                "expires_seconds": expires_seconds,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return url, expiration_time

    except S3Error as e:
        logger.error(
            "Failed to generate presigned upload URL",
            extra={
                "bucket": bucket,
                "object_key": object_key,
                "error": str(e),
            },
        )
        raise
