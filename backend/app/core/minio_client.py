from functools import lru_cache

from minio import Minio

from app.core.config import settings


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
