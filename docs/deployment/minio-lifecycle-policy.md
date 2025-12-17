# MinIO Lifecycle Policy Configuration

This document describes the required MinIO lifecycle policies for automatic cleanup of temporary files.

## Overview

The application generates temporary ZIP files for batch downloads that should be automatically deleted after 1 hour (Story 4.4, AC #5 & #8).

MinIO lifecycle policies must be configured at the bucket level to implement this requirement.

## Required Lifecycle Policies

### Policy 1: Batch Download Temporary Files

**Purpose**: Automatically delete ZIP files created by the batch download endpoint after 1 hour.

**Configuration**:
```json
{
  "Rules": [
    {
      "ID": "DeleteTempBatchDownloads",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "temp/batch-downloads/"
      },
      "Expiration": {
        "Days": 1
      }
    }
  ]
}
```

**Note**: MinIO lifecycle policies have a minimum granularity of 1 day. For true 1-hour expiry, consider implementing a background cleanup job (see Alternative Solution below).

## Setup Instructions

### Option 1: Using MinIO Console (Recommended for Development)

1. Access MinIO Console at `http://localhost:9001`
2. Login with admin credentials
3. Navigate to **Buckets** → **assets**
4. Click **Lifecycle** tab
5. Click **Add Lifecycle Rule**
6. Configure:
   - **Rule Name**: DeleteTempBatchDownloads
   - **Status**: Enabled
   - **Prefix**: temp/batch-downloads/
   - **Expiration Days**: 1
7. Save the rule

### Option 2: Using mc CLI

```bash
# Install MinIO Client
brew install minio/stable/mc

# Configure mc alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Create lifecycle.json file
cat > lifecycle.json <<EOF
{
  "Rules": [
    {
      "ID": "DeleteTempBatchDownloads",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "temp/batch-downloads/"
      },
      "Expiration": {
        "Days": 1
      }
    }
  ]
}
EOF

# Apply lifecycle policy to bucket
mc ilm import myminio/assets < lifecycle.json

# Verify lifecycle policy
mc ilm ls myminio/assets
```

### Option 3: Docker Compose Initialization

Add to `docker-compose.yml`:

```yaml
services:
  minio-lifecycle:
    image: minio/mc:latest
    depends_on:
      - minio
    entrypoint: >
      /bin/sh -c "
      until (/usr/bin/mc alias set myminio http://minio:9000 \${MINIO_ROOT_USER} \${MINIO_ROOT_PASSWORD}); do echo '...waiting for minio...' && sleep 1; done;
      /usr/bin/mc ilm add --expiry-days 1 --prefix 'temp/batch-downloads/' myminio/assets;
      "
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
```

## Alternative Solution: Background Cleanup Job

For true 1-hour expiry, implement a scheduled cleanup task:

### Python Script (Recommended)

Create `backend/app/tasks/cleanup_temp_files.py`:

```python
"""
Background task to clean up expired temporary files.

Run via cron or scheduler every hour to delete batch download ZIPs
older than 1 hour.
"""

import logging
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.minio_client import get_minio_client

logger = logging.getLogger(__name__)


def cleanup_expired_batch_downloads() -> dict:
    """
    Delete batch download ZIP files older than 1 hour.

    Returns:
        dict: Cleanup statistics (deleted_count, total_size_bytes, errors)
    """
    minio_client = get_minio_client()
    prefix = "temp/batch-downloads/"
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

    stats = {
        "deleted_count": 0,
        "total_size_bytes": 0,
        "errors": [],
    }

    try:
        # List all objects in temp/batch-downloads/
        objects = minio_client.list_objects(
            settings.MINIO_BUCKET,
            prefix=prefix,
            recursive=True
        )

        for obj in objects:
            # Check if object is older than 1 hour
            if obj.last_modified < cutoff_time:
                try:
                    # Delete the object
                    minio_client.remove_object(
                        settings.MINIO_BUCKET,
                        obj.object_name
                    )

                    stats["deleted_count"] += 1
                    stats["total_size_bytes"] += obj.size

                    logger.info(
                        f"Deleted expired batch download: {obj.object_name}",
                        extra={
                            "object_name": obj.object_name,
                            "size_bytes": obj.size,
                            "age_hours": (datetime.now(timezone.utc) - obj.last_modified).total_seconds() / 3600,
                        }
                    )
                except Exception as e:
                    error_msg = f"Failed to delete {obj.object_name}: {str(e)}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)

        logger.info(
            "Batch download cleanup completed",
            extra=stats
        )

    except Exception as e:
        error_msg = f"Batch download cleanup failed: {str(e)}"
        stats["errors"].append(error_msg)
        logger.error(error_msg)

    return stats


if __name__ == "__main__":
    # For manual testing
    result = cleanup_expired_batch_downloads()
    print(f"Cleanup completed: {result}")
```

### Cron Configuration

Add to system crontab or use a task scheduler:

```bash
# Run cleanup every hour at minute 0
0 * * * * cd /app && uv run python -m app.tasks.cleanup_temp_files
```

### Celery Task (Production)

If using Celery for background tasks:

```python
from celery import shared_task
from app.tasks.cleanup_temp_files import cleanup_expired_batch_downloads

@shared_task(name="cleanup_expired_batch_downloads")
def cleanup_temp_files_task():
    return cleanup_expired_batch_downloads()
```

## Verification

### Check Lifecycle Policy

```bash
mc ilm ls myminio/assets
```

Expected output:
```
     ID          | Status  | Prefix                    | Expiration
DeleteTempBatchDownloads | Enabled | temp/batch-downloads/ | 1 day(s)
```

### Test Cleanup

1. Create a test file:
```bash
echo "test" | mc pipe myminio/assets/temp/batch-downloads/test.zip
```

2. Wait for lifecycle policy to run (or run cleanup script manually)

3. Verify deletion:
```bash
mc ls myminio/assets/temp/batch-downloads/
```

## Monitoring

### CloudWatch/Prometheus Metrics

Track cleanup operations:
- Number of files deleted per run
- Total bytes freed
- Cleanup job execution time
- Cleanup failures

### Logs

Monitor application logs for:
- `Deleted expired batch download` - successful deletions
- `Batch download cleanup failed` - errors

## Production Considerations

1. **MinIO Lifecycle vs Background Job**:
   - MinIO Lifecycle: Simpler, built-in, but 1-day minimum
   - Background Job: True 1-hour expiry, but requires scheduler setup

2. **Recommended Approach**:
   - **Development**: Use MinIO lifecycle with 1-day expiry (acceptable for dev)
   - **Production**: Implement background cleanup job for true 1-hour expiry

3. **Monitoring**: Set up alerts for:
   - Cleanup job failures
   - Excessive temp file accumulation
   - Disk space usage in temp prefix

## References

- [MinIO Lifecycle Management](https://min.io/docs/minio/linux/administration/object-management/object-lifecycle-management.html)
- Story 4.4 AC #5: ZIP stored temporarily with 1-hour expiry
- Story 4.4 AC #8: Temporary ZIP automatically deleted after 1 hour
