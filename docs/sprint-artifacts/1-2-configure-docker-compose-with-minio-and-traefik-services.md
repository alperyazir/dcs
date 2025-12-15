# Story 1.2: Configure Docker Compose with MinIO and Traefik Services

Status: done

## Story

As a developer,
I want MinIO and Traefik services added to the Docker Compose configuration,
so that object storage and reverse proxy infrastructure are available for the platform.

## Acceptance Criteria

1. **Given** the project has been initialized from the FastAPI template
   **When** I add MinIO and Traefik service definitions to docker-compose.yml
   **Then** the MinIO service is configured with single-bucket setup and environment variables

2. **And** MinIO is accessible on port 9000 (API) with management console on port 9001

3. **And** Traefik is configured as reverse proxy routing /api/* to backend and /* to frontend

4. **And** Traefik is configured for automatic HTTPS with Let's Encrypt (production ready)

5. **And** All services (backend, frontend, PostgreSQL, MinIO, Traefik) start successfully with `docker-compose up`

6. **And** I can access MinIO console and create the initial "assets" bucket

7. **And** MinIO versioning is enabled on the assets bucket for soft delete support (FR7)

## Tasks / Subtasks

- [x] Task 1: Add MinIO service to docker-compose.yml (AC: 1, 2)
  - [x] Add MinIO service definition with official `minio/minio` image
  - [x] Configure MinIO environment variables (MINIO_ROOT_USER, MINIO_ROOT_PASSWORD)
  - [x] Configure persistent volume for MinIO data (`minio-data:/data`)
  - [x] Expose ports: 9000 (API), 9001 (Console)
  - [x] Add healthcheck for MinIO service
  - [x] Configure MinIO to use single-server single-drive mode for development

- [x] Task 2: Add MinIO environment variables to .env.example (AC: 1)
  - [x] Add MINIO_ROOT_USER placeholder
  - [x] Add MINIO_ROOT_PASSWORD placeholder
  - [x] Add MINIO_ENDPOINT variable (for backend to connect)
  - [x] Update local .env with secure generated values

- [x] Task 3: Configure MinIO for development in docker-compose.override.yml (AC: 2)
  - [x] Add MinIO service override for local development
  - [x] Set `restart: "no"` for development
  - [x] Expose console port 9001 locally
  - [x] Configure Traefik labels for MinIO console access

- [x] Task 4: Verify Traefik production configuration in docker-compose.traefik.yml (AC: 3, 4)
  - [x] Review existing Traefik configuration for Let's Encrypt setup
  - [x] Verify HTTPS entrypoint and certificate resolver configuration
  - [x] Verify routing rules for backend (/api/*) and frontend (/*)
  - [x] Add MinIO routing labels for production (minio.${DOMAIN})

- [x] Task 5: Create MinIO initialization script for bucket setup (AC: 6, 7)
  - [x] Create `scripts/init-minio.sh` to initialize assets bucket
  - [x] Configure bucket versioning using `mc` (MinIO Client)
  - [x] Set bucket policy for authenticated access
  - [x] Add MinIO client (mc) service or init container for setup

- [x] Task 6: Add MinIO service dependency to backend (AC: 5)
  - [x] Update backend service to depend on MinIO healthcheck
  - [x] Add MinIO environment variables to backend service
  - [x] Verify backend can reach MinIO at configured endpoint

- [x] Task 7: Test all services start successfully (AC: 5)
  - [x] Run `docker-compose up` and verify all services healthy
  - [x] Verify PostgreSQL starts and accepts connections
  - [x] Verify MinIO console accessible at localhost:9001
  - [x] Verify backend API accessible at localhost:8000/docs
  - [x] Verify frontend accessible at localhost:5173
  - [x] Run existing backend tests to ensure no regressions

- [x] Task 8: Document MinIO setup and configuration (AC: 6, 7)
  - [x] Update development.md with MinIO setup instructions
  - [x] Document bucket creation and versioning enablement
  - [x] Document MinIO console access for development

## Dev Notes

### Architecture References

**MinIO Integration Strategy:**
- **SDK:** Official `minio` Python SDK version 7.2.x
- **Bucket Strategy:** Single `assets` bucket with tenant-specific prefixes
- **Versioning:** MinIO versioning enabled at bucket level for soft delete/restore (FR7)

**MinIO Configuration Requirements:**
- **Storage Mode:** Single-node for development
- **Encryption:** Server-side encryption (AES-256) for compliance
- **Metrics:** Prometheus endpoint at `:9000/minio/v2/metrics/cluster`

### Technical Requirements

MinIO healthcheck uses `curl` instead of `mc ready` (mc not available in container by default).

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

- PostgreSQL auth failure after db volume recreate (fixed by resetting volume)
- minio-init successful on first run

### Completion Notes List

1. **AC1-2 Verified:** MinIO service added to docker-compose.yml with pinned version `minio/minio:RELEASE.2024-12-13T22-19-12Z`, healthcheck, and Traefik labels for both API (9000) and Console (9001)

2. **AC3-4 Verified:** Traefik already configured for HTTPS with Let's Encrypt in docker-compose.traefik.yml. MinIO Traefik labels added for production routing via minio.${DOMAIN} and minio-console.${DOMAIN}

3. **AC5 Verified:** All services start successfully with `docker compose up`. Backend depends on MinIO healthcheck. All 55 backend tests pass.

4. **AC6-7 Verified:** minio-init service automatically creates assets bucket with versioning enabled on stack startup. Verified via logs showing "local/assets versioning is enabled"

5. **Security:** .gitignore updated to exclude .env files. .env.example created with placeholder values.

6. **Documentation:** development.md updated with MinIO section including URLs, credentials, and manual operations guide.

### File List

**Created:**
- `.env.example` - Environment template with MinIO variables
- `docs/sprint-artifacts/1-2-configure-docker-compose-with-minio-and-traefik-services.md` - This story file

**Modified:**
- `docker-compose.yml` - Added MinIO service, volume, and backend MinIO dependency
- `docker-compose.override.yml` - Added MinIO dev overrides and minio-init service with bucket policy
- `.env` - Added MinIO credentials (not committed)
- `.gitignore` - Added .env patterns
- `development.md` - Added MinIO documentation section

### Tech Debt

- **MinIO Integration Test:** Add backend integration test to verify MinIO connectivity with configured credentials. Currently validated manually via docker compose logs.
