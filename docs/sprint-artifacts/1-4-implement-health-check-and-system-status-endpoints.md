# Story 1.4: Implement Health Check and System Status Endpoints

Status: done

## Story

As a developer,
I want health check endpoints that verify all system components are operational,
So that monitoring tools can detect issues and ensure platform availability (FR61, NFR-M1).

## Acceptance Criteria

1. **Given** the backend API is running, **When** I send a GET request to `/health`, **Then** I receive a 200 OK response with JSON: `{"status": "healthy", "database": "ok", "minio": "ok", "timestamp": "ISO-8601"}`

2. **Given** the backend API is running, **When** the endpoint checks PostgreSQL connectivity, **Then** it executes a simple query (e.g., `SELECT 1`) to verify the database is responsive

3. **Given** the backend API is running, **When** the endpoint checks MinIO connectivity, **Then** it calls the MinIO health check or lists buckets to verify object storage is available

4. **Given** PostgreSQL is unavailable, **When** I send a GET request to `/health`, **Then** the response is 503 with `{"status": "unhealthy", "database": "error", "minio": "ok", "timestamp": "ISO-8601"}`

5. **Given** MinIO is unavailable, **When** I send a GET request to `/health`, **Then** the response is 503 with `{"status": "unhealthy", "database": "ok", "minio": "error", "timestamp": "ISO-8601"}`

6. **Given** the backend API is running under normal conditions, **When** I send a GET request to `/health`, **Then** the endpoint responds within 100ms (NFR-P1)

7. **Given** Traefik is configured as reverse proxy, **When** health checks are performed, **Then** Traefik uses this endpoint for service health checks (already configured in docker-compose.yml)

## Tasks / Subtasks

- [x] Task 1: Add MinIO settings to backend configuration (AC: #2, #3)
  - [x] 1.1 Update `backend/app/core/config.py` to add MinIO environment variables
  - [x] 1.2 Add `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_USE_SSL`, `MINIO_BUCKET_NAME` settings
  - [x] 1.3 Add computed property for MinIO secure mode (`minio_secure: bool`)

- [x] Task 2: Create MinIO client utility (AC: #3, #5)
  - [x] 2.1 Add `minio` package to backend dependencies (`pyproject.toml`)
  - [x] 2.2 Create `backend/app/core/minio_client.py` with client initialization
  - [x] 2.3 Implement `get_minio_client()` function returning initialized Minio client
  - [x] 2.4 Add client singleton or dependency injection pattern for reuse

- [x] Task 3: Create health check Pydantic schemas (AC: #1, #4, #5)
  - [x] 3.1 Create `backend/app/schemas/health.py` with `HealthCheckResponse` schema
  - [x] 3.2 Define response model with `status`, `database`, `minio`, `timestamp` fields
  - [x] 3.3 Use `Literal["healthy", "unhealthy"]` for status field
  - [x] 3.4 Use `Literal["ok", "error"]` for component status fields

- [x] Task 4: Implement health check endpoint (AC: #1, #2, #3, #4, #5, #6)
  - [x] 4.1 Create `backend/app/api/routes/health.py` with health router
  - [x] 4.2 Implement `GET /health` endpoint (not under `/api/v1/` - root level for monitoring)
  - [x] 4.3 Add database health check: execute `SELECT 1` with timeout handling
  - [x] 4.4 Add MinIO health check: call `client.bucket_exists()` or list operation
  - [x] 4.5 Return 200 if all healthy, 503 if any component unhealthy
  - [x] 4.6 Include ISO-8601 UTC timestamp in response
  - [x] 4.7 Add async implementation for non-blocking checks

- [x] Task 5: Register health router in main app (AC: #1, #7)
  - [x] 5.1 Update `backend/app/main.py` to include health router at root level
  - [x] 5.2 Ensure `/health` is accessible without authentication
  - [x] 5.3 Verify docker-compose healthcheck path works (update if needed)

- [x] Task 6: Write tests for health check endpoint (AC: #1-6)
  - [x] 6.1 Create `backend/tests/standalone/test_health.py`
  - [x] 6.2 Test healthy response when all components available
  - [x] 6.3 Test unhealthy response when database unavailable (mock)
  - [x] 6.4 Test unhealthy response when MinIO unavailable (mock)
  - [x] 6.5 Test response format matches schema
  - [x] 6.6 Test no authentication required

- [x] Task 7: Update docker-compose healthcheck if needed (AC: #7)
  - [x] 7.1 Verify backend healthcheck in `docker-compose.yml` points to `/health`
  - [x] 7.2 Update from `/api/v1/utils/health-check/` to `/health`

## Dev Notes

### Architecture Compliance

**Layered Architecture Pattern:**
- Routes layer: `backend/app/api/routes/health.py`
- No service/repository needed - health check is infrastructure concern
- Direct database and MinIO client access acceptable for health checks

**Error Response Format (from Architecture):**
```json
{
  "status": "unhealthy",
  "database": "error",
  "minio": "ok",
  "timestamp": "2025-12-15T10:30:00Z"
}
```

**Naming Conventions:**
- File names: snake_case (`health.py`, `minio_client.py`)
- Functions: snake_case (`check_database_health`, `get_health_status`)
- Classes: PascalCase (`HealthCheckResponse`)
- Constants: UPPER_SNAKE_CASE (`HEALTH_CHECK_TIMEOUT_SECONDS`)

### Technical Requirements

**MinIO SDK Integration:**
- Package: `minio` version 7.2.x (latest stable)
- Initialize with: `Minio(endpoint, access_key, secret_key, secure=False)`
- Health check: Use `client.bucket_exists(bucket_name)` or `client.list_buckets()`
- Timeout: Set 5-second timeout for health checks

**Database Health Check:**
- Use SQLModel/SQLAlchemy session
- Execute: `session.exec(text("SELECT 1"))`
- Wrap in try/except with timeout
- Return "ok" on success, "error" on exception

**Performance Requirement:**
- NFR-P1: Response time < 100ms under normal conditions
- Use async/await for non-blocking checks
- Consider running DB and MinIO checks concurrently with `asyncio.gather()`

### Current Codebase Context

**Existing Health Check (to replace/enhance):**
- Location: `backend/app/api/routes/utils.py`
- Current endpoint: `GET /api/v1/utils/health-check/` returns `True`
- Docker healthcheck uses: `http://localhost:8000/api/v1/utils/health-check/`

**Configuration (from docker-compose.yml):**
- MinIO endpoint: `minio:9000` (internal Docker network)
- Environment variables already defined:
  - `MINIO_ENDPOINT`
  - `MINIO_ROOT_USER`
  - `MINIO_ROOT_PASSWORD`
  - `MINIO_USE_SSL`
  - `MINIO_BUCKET_NAME`

**Settings Location:**
- `backend/app/core/config.py` - Add MinIO settings here
- Use Pydantic Settings pattern matching existing configuration

### File Structure Notes

**New Files to Create:**
```
backend/app/
├── api/routes/
│   └── health.py           # NEW: Health check endpoint
├── core/
│   └── minio_client.py     # NEW: MinIO client utility
└── schemas/
    └── health.py           # NEW: Health response schemas
```

**Files to Modify:**
```
backend/app/
├── core/
│   └── config.py           # ADD: MinIO settings
├── main.py                 # ADD: Health router registration
└── pyproject.toml          # ADD: minio dependency
```

### References

- [Source: docs/epics.md#Story-1.4] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Health-Checks] - Health endpoint spec: `GET /health` returns `{"status": "healthy", "database": "ok", "minio": "ok"}`
- [Source: docs/architecture/core-architectural-decisions.md#MinIO-Integration] - MinIO SDK version 7.2.x, single bucket config
- [Source: docs/architecture/implementation-patterns-consistency-rules.md#API-Naming] - Endpoint naming conventions
- [Source: docs/architecture/project-structure-boundaries.md#Health-Metrics] - `api/routes/health.py` structure

### Previous Story Intelligence

**Story 1.3 Patterns (Database Models):**
- Used SQLModel for all database models
- Models in single `backend/app/models.py` file (FastAPI template pattern)
- UUID primary keys with `Field(default_factory=uuid.uuid4)`
- Proper type hints throughout

**Git Commit Patterns:**
- Conventional commits: `feat(story-X.Y): Description`
- PR-based workflow to main branch

### Testing Standards

**Test Location:** `backend/tests/standalone/test_health.py`

**Test Patterns:**
- Use pytest-asyncio for async endpoint testing
- Mock external services (MinIO, optionally DB) for isolation
- Test both success and failure scenarios
- Verify response schema compliance

**Coverage Target:** 80% minimum per CI/CD pipeline

### Security Considerations

- Health endpoint MUST be unauthenticated (for monitoring systems)
- Do NOT expose sensitive information in health response
- Do NOT include connection strings, credentials, or detailed error messages
- Only return "ok" or "error" status for components

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Task 1: Added MinIO settings (MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_USE_SSL, MINIO_BUCKET_NAME) to config.py with computed `minio_secure` property
- Task 2: Created minio_client.py with `get_minio_client()` using @lru_cache singleton pattern
- Task 3: Created health.py schema with HealthCheckResponse using Literal types for strict validation
- Task 4: Implemented /health endpoint with async concurrent checks (asyncio.gather) for DB and MinIO. Returns 200 if healthy, 503 if unhealthy.
- Task 5: Registered health router at root level in main.py (not under /api/v1/)
- Task 6: Created 6 unit tests with mocking for health check scenarios. Tests placed in standalone directory to avoid conftest.py db fixture.
- Task 7: Updated docker-compose.yml healthcheck from /api/v1/utils/health-check/ to /health
- All mypy and ruff checks pass
- All 6 tests pass

**Code Review Fixes (2025-12-15):**
- Added timeout handling using `asyncio.wait_for()` with 5-second timeout
- Replaced deprecated `asyncio.get_event_loop()` with `asyncio.get_running_loop()`
- Added logging for health check failures
- Updated File List to include all modified files

### File List

**New Files:**
- backend/app/core/minio_client.py
- backend/app/schemas/health.py
- backend/app/api/routes/health.py
- backend/tests/standalone/test_health.py

**Modified Files:**
- backend/app/core/config.py
- backend/app/main.py
- backend/pyproject.toml
- backend/uv.lock
- docker-compose.yml
- docs/sprint-artifacts/sprint-status.yaml
