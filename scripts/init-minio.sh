#!/bin/bash
# MinIO Bucket Initialization Script
# Creates the 'assets' bucket and enables versioning for soft delete support (FR7)

set -e

MINIO_HOST="${MINIO_HOST:-minio:9000}"
MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"
BUCKET_NAME="${MINIO_BUCKET_NAME:-assets}"

echo "Waiting for MinIO to be ready..."
until curl -sf "http://${MINIO_HOST}/minio/health/live" > /dev/null 2>&1; do
    echo "MinIO is not ready yet. Waiting..."
    sleep 2
done

echo "MinIO is ready. Setting up mc alias..."
mc alias set local "http://${MINIO_HOST}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"

echo "Creating bucket '${BUCKET_NAME}' if not exists..."
mc mb "local/${BUCKET_NAME}" --ignore-existing

echo "Enabling versioning on bucket '${BUCKET_NAME}'..."
mc version enable "local/${BUCKET_NAME}"

echo "Verifying bucket configuration..."
mc ls local/
mc version info "local/${BUCKET_NAME}"

echo "MinIO initialization complete!"
echo "  - Bucket: ${BUCKET_NAME}"
echo "  - Versioning: enabled"
