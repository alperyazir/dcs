# Project Structure & Boundaries

## Complete Project Directory Structure

```
dream-central-storage/
├── README.md
├── .gitignore
├── .env
├── .env.example
├── docker-compose.yml              # Orchestrates backend, frontend, PostgreSQL, MinIO, Traefik
├── docker-compose.override.yml     # Local development overrides
├──.github/
│   └── workflows/
│       ├── test-backend.yml        # Backend pytest + coverage
│       ├── test-frontend.yml       # Frontend Vitest + component tests
│       ├── build-images.yml        # Docker image builds
│       └── deploy.yml              # VPS deployment via SSH
│
├── backend/
│   ├── Dockerfile                  # Multi-stage build for FastAPI
│   ├── pyproject.toml              # uv package management
│   ├── .env.example
│   ├── .env
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app initialization, CORS, middleware
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Pydantic Settings (DB, MinIO, JWT secrets)
│   │   │   ├── db.py               # SQLModel engine, session factory, row-level security
│   │   │   ├── security.py         # JWT token generation/validation, password hashing
│   │   │   ├── constants.py        # MAX_FILE_SIZE, ALLOWED_MIME_TYPES, role enums
│   │   │   └── exceptions.py       # Custom exceptions (AssetNotFoundException, QuotaExceededException)
│   │   │
│   │   ├── models/                 # SQLModel ORM models (database tables)
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User, role enum (Admin, Supervisor, Publisher, School, Teacher, Student) [FR12-FR19]
│   │   │   ├── asset.py            # Asset, versioning, soft delete (is_deleted), metadata [FR1-FR11]
│   │   │   ├── asset_version.py    # AssetVersion for version history [FR5]
│   │   │   ├── asset_permission.py # AssetPermission (LMS-managed grants) [FR21-FR24]
│   │   │   ├── folder.py           # Folder (optional hierarchical organization) [FR11]
│   │   │   ├── audit_log.py        # AuditLog (immutable append-only) [FR53-FR60]
│   │   │   ├── trash.py            # Trash (soft-deleted assets tracking) [FR7-FR8]
│   │   │   └── tenant.py           # Tenant (multi-tenant isolation) [FR25-FR30]
│   │   │
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py           # PaginatedResponse, ErrorResponse, SuccessResponse
│   │   │   ├── user.py             # UserCreate, UserUpdate, UserResponse, LoginRequest
│   │   │   ├── asset.py            # AssetCreate, AssetUpdate, AssetResponse, AssetListResponse
│   │   │   ├── asset_version.py    # AssetVersionResponse, VersionListResponse
│   │   │   ├── asset_permission.py # PermissionCreate, PermissionResponse (LMS integration) [FR21]
│   │   │   ├── folder.py           # FolderCreate, FolderUpdate, FolderResponse
│   │   │   ├── audit_log.py        # AuditLogResponse, AuditLogFilter
│   │   │   ├── upload.py           # MultipartUploadInit, ChunkUploadResponse, UploadComplete [FR4]
│   │   │   └── signed_url.py       # SignedURLRequest, SignedURLResponse [FR16]
│   │   │
│   │   ├── services/               # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py     # JWT login, token refresh, password reset [FR12-FR14]
│   │   │   ├── asset_service.py    # Asset CRUD, versioning, soft delete, metadata [FR1-FR11]
│   │   │   ├── minio_service.py    # MinIO client wrapper, presigned URLs, bucket operations [FR3, FR16, FR47-FR52]
│   │   │   ├── permission_service.py # Asset permission management (LMS grants) [FR21-FR24]
│   │   │   ├── upload_service.py   # Multipart upload orchestration, chunk validation [FR4]
│   │   │   ├── download_service.py # Streaming downloads, ZIP batch downloads [FR2, FR52]
│   │   │   ├── version_service.py  # Version history, restore previous versions [FR5-FR6]
│   │   │   ├── trash_service.py    # Soft delete, trash management, restore [FR7-FR8]
│   │   │   ├── search_service.py   # Metadata search, filtering [FR41-FR46]
│   │   │   ├── audit_service.py    # Audit log creation, compliance reporting [FR53-FR60]
│   │   │   ├── quota_service.py    # Storage quota tracking, enforcement [FR29]
│   │   │   └── integration_service.py # LMS/FlowBook config.json delivery [FR31-FR40]
│   │   │
│   │   ├── repositories/           # Data access layer (CRUD operations)
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py  # Generic CRUD with tenant_id filtering
│   │   │   ├── user_repository.py  # User queries with role filtering
│   │   │   ├── asset_repository.py # Asset queries with tenant + permission checks
│   │   │   ├── asset_version_repository.py
│   │   │   ├── asset_permission_repository.py
│   │   │   ├── folder_repository.py
│   │   │   ├── audit_log_repository.py
│   │   │   └── trash_repository.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py             # API router aggregation
│   │   │   ├── deps.py             # Dependency injection (get_db, get_current_user, get_minio_client)
│   │   │   │
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py         # POST /api/v1/auth/login, /logout, /refresh [FR12-FR14]
│   │   │       ├── users.py        # CRUD /api/v1/users (role-based access) [FR15-FR19]
│   │   │       ├── assets.py       # CRUD /api/v1/assets, pagination, filtering [FR1-FR11, FR41-FR46]
│   │   │       ├── upload.py       # POST /api/v1/upload/init, /chunk, /complete [FR4]
│   │   │       ├── download.py     # GET /api/v1/download/{asset_id}, /batch-zip [FR2, FR52]
│   │   │       ├── versions.py     # GET /api/v1/assets/{id}/versions, POST /restore [FR5-FR6]
│   │   │       ├── trash.py        # GET /api/v1/trash, POST /assets/{id}/delete, /restore [FR7-FR8]
│   │   │       ├── permissions.py  # CRUD /api/v1/permissions (LMS integration) [FR21-FR24]
│   │   │       ├── folders.py      # CRUD /api/v1/folders (optional organization) [FR11]
│   │   │       ├── search.py       # GET /api/v1/search?q=...&filters=... [FR41-FR46]
│   │   │       ├── audit_logs.py   # GET /api/v1/audit-logs (admin only) [FR53-FR60]
│   │   │       ├── health.py       # GET /health (DB + MinIO status) [FR61-FR67]
│   │   │       ├── metrics.py      # GET /metrics (Prometheus format) [FR64-FR65]
│   │   │       ├── integration/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── lms.py      # POST /api/v1/integrations/lms/assignments (assign assets) [FR31-FR35]
│   │   │       │   └── flowbook.py # GET /api/v1/integrations/flowbook/config (config.json) [FR36-FR40]
│   │   │       └── signed_urls.py  # POST /api/v1/signed-urls (generate presigned URLs) [FR16]
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── request_id.py       # Inject UUID request_id into request.state
│   │   │   ├── logging.py          # Structured JSON logging with request_id
│   │   │   ├── rate_limit.py       # Token bucket rate limiting per role [FR20]
│   │   │   ├── tenant_context.py   # Inject tenant_id from JWT into request context
│   │   │   └── audit.py            # Automatic audit log creation for CRUD operations [FR53]
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validators.py       # MIME type, file size, path validation
│   │       ├── formatters.py       # Date, byte size formatting
│   │       ├── checksum.py         # SHA256 checksum calculation [FR9]
│   │       └── streaming.py        # Streaming ZIP extraction utilities [FR51]
│   │
│   ├── alembic/                    # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/               # Migration files (auto-generated from SQLModel)
│   │       ├── 001_initial_schema.py
│   │       ├── 002_add_asset_versioning.py
│   │       ├── 003_add_audit_logs.py
│   │       └── ...
│   │
│   └── tests/
│       ├── conftest.py             # Pytest fixtures (test DB, test MinIO, test users)
│       ├── __init__.py
│       ├── api/
│       │   ├── test_auth.py
│       │   ├── test_assets.py
│       │   ├── test_upload.py
│       │   ├── test_download.py
│       │   ├── test_permissions.py
│       │   └── test_integrations.py
│       ├── services/
│       │   ├── test_asset_service.py
│       │   ├── test_minio_service.py
│       │   ├── test_upload_service.py
│       │   └── test_audit_service.py
│       ├── repositories/
│       │   ├── test_asset_repository.py
│       │   └── test_user_repository.py
│       └── utils/
│           ├── test_validators.py
│           └── test_checksum.py
│
├── frontend/
│   ├── Dockerfile                  # Multi-stage build (Vite build → Nginx serve)
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts              # Vite configuration, proxy to backend
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .env.example
│   ├── .env
│   ├── index.html
│   │
│   ├── src/
│   │   ├── main.tsx                # React entry point, TanStack Query provider
│   │   ├── App.tsx                 # Root component, routing setup
│   │   ├── index.css               # Tailwind imports, global styles
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui base components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Dialog.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Select.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   ├── Tabs.tsx
│   │   │   │   ├── Toast.tsx
│   │   │   │   ├── Progress.tsx    # Upload progress bar
│   │   │   │   ├── Skeleton.tsx    # Loading skeletons
│   │   │   │   └── ...
│   │   │   │
│   │   │   └── Common/             # Shared application components
│   │   │       ├── Navbar.tsx      # Role-based navigation
│   │   │       ├── Footer.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       ├── ErrorMessage.tsx
│   │   │       ├── LoadingSpinner.tsx
│   │   │       └── ProtectedRoute.tsx # Role-based route protection
│   │   │
│   │   ├── routes/                 # Feature-based page organization
│   │   │   ├── _layout/
│   │   │   │   ├── MainLayout.tsx  # Layout with Navbar for authenticated users
│   │   │   │   └── AuthLayout.tsx  # Minimal layout for login/signup
│   │   │   │
│   │   │   ├── auth/               # Authentication pages [FR12-FR14]
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── SignupPage.tsx
│   │   │   │   └── ForgotPasswordPage.tsx
│   │   │   │
│   │   │   ├── assets/             # Asset management [FR1-FR11, FR41-FR46]
│   │   │   │   ├── AssetLibrary.tsx # Main asset list with search/filter [FR41-FR46]
│   │   │   │   ├── AssetDetail.tsx  # Single asset view with versions [FR5-FR6]
│   │   │   │   └── components/
│   │   │   │       ├── AssetCard.tsx
│   │   │   │       ├── AssetFilter.tsx # Search, filter by type, date, tags
│   │   │   │       ├── AssetPreview.tsx # Image/video preview [FR50]
│   │   │   │       ├── AssetMetadata.tsx # Display/edit metadata [FR9-FR10]
│   │   │   │       ├── VersionHistory.tsx # Version list, restore [FR5-FR6]
│   │   │   │       └── AssetActions.tsx # Delete, share, download actions
│   │   │   │
│   │   │   ├── upload/             # Upload workflows [FR4]
│   │   │   │   ├── UploadPage.tsx
│   │   │   │   └── components/
│   │   │   │       ├── UploadModal.tsx # Drag-drop or file select
│   │   │   │       ├── UploadProgress.tsx # Multipart upload progress bar
│   │   │   │       ├── ChunkedUploader.tsx # Handles chunk logic
│   │   │   │       └── BatchUploadQueue.tsx # Queue multiple uploads
│   │   │   │
│   │   │   ├── trash/              # Trash management [FR7-FR8]
│   │   │   │   ├── TrashPage.tsx   # List soft-deleted assets
│   │   │   │   └── components/
│   │   │   │       ├── TrashCard.tsx
│   │   │   │       └── TrashActions.tsx # Restore or permanent delete
│   │   │   │
│   │   │   ├── admin/              # Admin dashboard [FR15-FR19, FR53-FR60]
│   │   │   │   ├── Dashboard.tsx   # Overview: users, storage, activity
│   │   │   │   ├── UsersPage.tsx   # User management (CRUD)
│   │   │   │   ├── AuditLogsPage.tsx # Audit log viewer [FR53-FR60]
│   │   │   │   ├── SettingsPage.tsx # System settings, quotas [FR29]
│   │   │   │   └── components/
│   │   │   │       ├── UserTable.tsx
│   │   │   │       ├── UserForm.tsx
│   │   │   │       ├── AuditLogTable.tsx
│   │   │   │       ├── AuditLogFilter.tsx
│   │   │   │       └── QuotaSettings.tsx
│   │   │   │
│   │   │   ├── publisher/          # Publisher-specific views [FR25-FR30]
│   │   │   │   ├── PublisherDashboard.tsx
│   │   │   │   └── components/
│   │   │   │       ├── PublisherAssets.tsx # Assets in /publishers/{id}/
│   │   │   │       └── PublisherQuota.tsx
│   │   │   │
│   │   │   ├── teacher/            # Teacher-specific views [FR25-FR30]
│   │   │   │   ├── TeacherDashboard.tsx
│   │   │   │   └── components/
│   │   │   │       ├── TeacherAssets.tsx # Assets in /teachers/{id}/
│   │   │   │       └── AssignedAssets.tsx # Assets granted via LMS [FR21-FR24]
│   │   │   │
│   │   │   └── student/            # Student-specific views [FR25-FR30]
│   │   │       ├── StudentDashboard.tsx
│   │   │       └── components/
│   │   │           └── GrantedAssets.tsx # Read-only assets from teachers
│   │   │
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useAssets.ts        # TanStack Query wrapper for asset CRUD
│   │   │   ├── useUpload.ts        # Multipart upload logic [FR4]
│   │   │   ├── useDownload.ts      # Download with signed URLs [FR2]
│   │   │   ├── useAuth.ts          # Auth context helpers (login, logout, user)
│   │   │   ├── usePermissions.ts   # Permission management [FR21-FR24]
│   │   │   ├── useVersions.ts      # Asset version history [FR5-FR6]
│   │   │   ├── useTrash.ts         # Trash operations [FR7-FR8]
│   │   │   ├── useSearch.ts        # Search and filter [FR41-FR46]
│   │   │   ├── usePagination.ts    # Pagination logic
│   │   │   └── useAuditLogs.ts     # Audit log queries [FR53-FR60]
│   │   │
│   │   ├── client/                 # Auto-generated API client
│   │   │   ├── api.ts              # Generated from OpenAPI spec
│   │   │   ├── models.ts           # TypeScript types from Pydantic schemas
│   │   │   └── index.ts
│   │   │
│   │   ├── lib/                    # Utilities and helpers
│   │   │   ├── api.ts              # Axios instance, request/response interceptors
│   │   │   ├── formatters.ts       # formatBytes, formatDate, formatFileType
│   │   │   ├── validators.ts       # Client-side validation helpers
│   │   │   ├── queryClient.ts      # TanStack Query client configuration
│   │   │   └── auth.ts             # Token storage (localStorage), JWT decode
│   │   │
│   │   ├── types/                  # Shared TypeScript types
│   │   │   ├── asset.ts
│   │   │   ├── user.ts
│   │   │   ├── permission.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── constants/              # Application constants
│   │   │   ├── config.ts           # API_BASE_URL, MAX_UPLOAD_SIZE
│   │   │   ├── roles.ts            # Role enum matching backend
│   │   │   └── routes.ts           # Route path constants
│   │   │
│   │   └── contexts/               # React contexts
│   │       └── AuthContext.tsx     # User state, login/logout functions
│   │
│   ├── public/                     # Static assets
│   │   ├── favicon.ico
│   │   └── assets/
│   │       └── logo.svg
│   │
│   └── tests/
│       ├── setup.ts                # Vitest setup
│       ├── components/
│       │   ├── AssetCard.test.tsx
│       │   ├── UploadModal.test.tsx
│       │   └── AuthForm.test.tsx
│       └── hooks/
│           ├── useAssets.test.ts
│           └── useUpload.test.ts
│
├── docs/                           # Documentation
│   ├── prd.md                      # Product Requirements Document
│   ├── architecture.md             # This file
│   ├── api-reference.md            # API endpoint documentation (auto-generated)
│   ├── deployment.md               # Deployment instructions for VPS
│   └── developer-guide.md          # Setup, development workflow
│
└── scripts/                        # Utility scripts
    ├── init-minio.sh               # Create MinIO buckets, set policies
    ├── seed-data.py                # Seed database with test data
    ├── generate-api-client.sh      # Generate frontend TypeScript client from OpenAPI
    ├── backup-db.sh                # PostgreSQL backup script
    └── deploy.sh                   # VPS deployment script
```

## Architectural Boundaries

**API Boundaries:**

**External API (Public):**

- **Endpoint Prefix:** `/api/v1/`
- **Authentication:** Required (JWT Bearer token) except `/auth/login`, `/auth/signup`
- **Rate Limiting:** Role-based limits (Publisher: 1000/hr, Teacher: 500/hr, Student: 100/hr)
- **CORS:** Allowed origins configured via environment variable (LMS, FlowBook, Kanban domains)
- **Versioning:** URL-based (`/api/v1/`, `/api/v2/`), maintain v1 for 6 months after v2 release

**API Categories:**

1. **Authentication API** (`/api/v1/auth/*`)
   - POST `/login` → JWT access + refresh tokens
   - POST `/refresh` → New access token from refresh token
   - POST `/logout` → Invalidate refresh token

2. **Asset Management API** (`/api/v1/assets/*`)
   - GET `/assets` → Paginated asset list with filters
   - POST `/assets` → Create asset metadata (before upload)
   - GET `/assets/{asset_id}` → Asset details
   - PUT `/assets/{asset_id}` → Update metadata
   - DELETE `/assets/{asset_id}` → Soft delete

3. **Upload API** (`/api/v1/upload/*`)
   - POST `/upload/init` → Initialize multipart upload, get presigned URLs
   - POST `/upload/chunk` → Report chunk upload completion
   - POST `/upload/complete` → Finalize upload, validate ETags

4. **Download API** (`/api/v1/download/*`)
   - GET `/download/{asset_id}` → Get presigned download URL
   - POST `/download/batch-zip` → Create streaming ZIP of multiple assets

5. **Version API** (`/api/v1/assets/{asset_id}/versions/*`)
   - GET `/versions` → List all versions
   - POST `/versions/{version_id}/restore` → Restore previous version

6. **Permission API** (`/api/v1/permissions/*`)
   - POST `/permissions` → Grant asset access (LMS integration)
   - DELETE `/permissions/{permission_id}` → Revoke access
   - GET `/permissions/user/{user_id}` → List user's granted assets

7. **Integration APIs** (`/api/v1/integrations/*`)
   - POST `/integrations/lms/assignments` → LMS assigns assets to teachers
   - GET `/integrations/flowbook/config` → FlowBook config.json delivery

8. **Audit API** (`/api/v1/audit-logs/*`)
   - GET `/audit-logs` → Paginated audit logs (admin only)
   - GET `/audit-logs/export` → CSV export for compliance

9. **Health & Metrics** (`/health`, `/metrics`)
   - GET `/health` → Health check (DB + MinIO status)
   - GET `/metrics` → Prometheus metrics

**Internal Service Boundaries:**

**Service Layer:**

- **AssetService** → **AssetRepository** → PostgreSQL `assets` table
- **MinIOService** → MinIO SDK → MinIO object storage
- **UploadService** → **MinIOService** + **AssetRepository** (orchestrates multipart upload)
- **PermissionService** → **AssetPermissionRepository** → PostgreSQL `asset_permissions` table
- **AuditService** → **AuditLogRepository** → PostgreSQL `audit_logs` table (append-only)

**Service Communication:**

- **Routes** → **Services** (dependency injection via `Depends()`)
- **Services** → **Repositories** (direct instantiation or dependency injection)
- **Services** → **MinIOService** (singleton or dependency injection)
- No direct database access from routes (always through services)

**Component Boundaries:**

**Frontend Component Hierarchy:**

**Page-Level Components** (`routes/*/`)
- Own their data fetching via TanStack Query hooks
- Pass data down to child components as props
- Handle route-specific logic (pagination state, filter state)

**Feature Components** (`routes/*/components/`)
- Receive data via props
- Emit events via callback props (`onDelete`, `onUpdate`)
- Local UI state only (modal open/closed, form validation)

**Shared UI Components** (`components/ui/`)
- No data fetching (pure presentation)
- Controlled components (state managed by parent)
- Reusable across features

**State Management Boundaries:**

- **Server State:** Managed by TanStack Query (assets, users, permissions, audit logs)
- **Auth State:** Managed by AuthContext (user, isAuthenticated, login, logout)
- **UI State:** Local component state (`useState`, `useReducer`)
- **No Redux:** Not needed for this project's complexity

**Data Boundaries:**

**Database Schema Boundaries:**

**Multi-Tenant Isolation:**

- All tenant-specific tables include `tenant_id` column
- PostgreSQL row-level security (RLS) policies enforce filtering:
  ```sql
  CREATE POLICY tenant_isolation ON assets
  FOR ALL TO authenticated
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
  ```
- Middleware sets `app.current_tenant_id` session variable from JWT

**Database Access Patterns:**

**Repository Layer:**

- **BaseRepository** enforces `tenant_id` filtering on all queries
- **Specific Repositories** (AssetRepository, UserRepository) extend BaseRepository
- All queries parameterized (no string concatenation) to prevent SQL injection

**Caching Boundaries:**

**Frontend Caching (TanStack Query):**

- **Stale Time:** 5 minutes for asset metadata, 10 minutes for user data
- **Cache Time:** 10 minutes (keep in memory after query inactive)
- **Invalidation:** Mutations invalidate related queries via `queryClient.invalidateQueries()`

**Backend Caching (Future - Redis):**

- Not implemented initially (deferred to post-MVP)
- When added: Signed URL caching (1-hour TTL), rate limit counters

**External Data Integration Points:**

**MinIO Object Storage:**

- **Access:** Backend generates presigned URLs, frontend uploads/downloads directly
- **Bucket:** Single `assets` bucket with prefix-based paths
- **Operations:**
  - Upload: Backend → MinIO SDK → presigned PUT URL → Frontend uploads directly
  - Download: Backend → MinIO SDK → presigned GET URL → Frontend downloads directly
  - Versioning: MinIO versioning enabled at bucket level

**LMS Integration:**

- **Direction:** LMS → DCS (LMS assigns assets to teachers via API)
- **Endpoint:** POST `/api/v1/integrations/lms/assignments`
- **Authentication:** API key or JWT from LMS
- **Data Flow:** LMS sends `{teacher_id, asset_id, permissions}` → DCS creates `AssetPermission` rows

**FlowBook Integration:**

- **Direction:** FlowBook → DCS (FlowBook fetches config.json)
- **Endpoint:** GET `/api/v1/integrations/flowbook/config`
- **Response:** JSON config with asset URLs (presigned)

## Requirements to Structure Mapping

**Functional Requirements Mapping:**

**FR1-FR11: Asset Management**
- **Backend:**
  - `models/asset.py` → Asset table
  - `services/asset_service.py` → Asset CRUD logic
  - `repositories/asset_repository.py` → Asset queries
  - `api/routes/assets.py` → Asset API endpoints
- **Frontend:**
  - `routes/assets/AssetLibrary.tsx` → Asset list page
  - `routes/assets/AssetDetail.tsx` → Asset detail page
  - `routes/assets/components/AssetCard.tsx` → Asset card component
  - `hooks/useAssets.ts` → Asset data fetching

**FR4: Multipart Upload**
- **Backend:**
  - `services/upload_service.py` → Orchestrates multipart upload
  - `services/minio_service.py` → Generates presigned URLs for chunks
  - `api/routes/upload.py` → Upload API endpoints
  - `schemas/upload.py` → Upload request/response schemas
- **Frontend:**
  - `routes/upload/UploadPage.tsx` → Upload page
  - `routes/upload/components/ChunkedUploader.tsx` → Chunk upload logic
  - `routes/upload/components/UploadProgress.tsx` → Progress bar
  - `hooks/useUpload.ts` → Upload state management

**FR5-FR6: Versioning**
- **Backend:**
  - `models/asset_version.py` → AssetVersion table
  - `services/version_service.py` → Version history, restore
  - `repositories/asset_version_repository.py` → Version queries
  - `api/routes/versions.py` → Version API endpoints
- **Frontend:**
  - `routes/assets/components/VersionHistory.tsx` → Version list component
  - `hooks/useVersions.ts` → Version data fetching

**FR7-FR8: Soft Delete & Trash**
- **Backend:**
  - `models/trash.py` → Trash table (tracking)
  - `services/trash_service.py` → Soft delete, restore logic
  - `repositories/trash_repository.py` → Trash queries
  - `api/routes/trash.py` → Trash API endpoints
- **Frontend:**
  - `routes/trash/TrashPage.tsx` → Trash page
  - `routes/trash/components/TrashCard.tsx` → Trash item card
  - `hooks/useTrash.ts` → Trash operations

**FR12-FR14: Authentication**
- **Backend:**
  - `core/security.py` → JWT generation, password hashing
  - `services/auth_service.py` → Login, logout, token refresh
  - `api/routes/auth.py` → Auth API endpoints
- **Frontend:**
  - `routes/auth/LoginPage.tsx` → Login page
  - `contexts/AuthContext.tsx` → Auth state management
  - `hooks/useAuth.ts` → Auth helpers

**FR15-FR24: Access Control & RBAC**
- **Backend:**
  - `models/user.py` → User table with role enum
  - `models/asset_permission.py` → AssetPermission table
  - `services/permission_service.py` → Permission management
  - `repositories/asset_permission_repository.py` → Permission queries
  - `middleware/tenant_context.py` → Inject tenant context
  - `api/deps.py` → Role-based dependencies (e.g., `require_admin`)
  - `api/routes/permissions.py` → Permission API endpoints
- **Frontend:**
  - `components/Common/ProtectedRoute.tsx` → Role-based route protection
  - `hooks/usePermissions.ts` → Permission data fetching
  - `constants/roles.ts` → Role enum

**FR25-FR30: Multi-Tenant Storage**
- **Backend:**
  - `models/tenant.py` → Tenant table
  - `core/db.py` → Row-level security setup
  - `middleware/tenant_context.py` → Tenant context injection
  - `repositories/base_repository.py` → Tenant filtering in all queries
  - `services/minio_service.py` → Prefix-based paths (`/publishers/{id}/`, etc.)
- **Frontend:**
  - `routes/publisher/PublisherDashboard.tsx` → Publisher view
  - `routes/teacher/TeacherDashboard.tsx` → Teacher view
  - `routes/student/StudentDashboard.tsx` → Student view

**FR31-FR40: Integration & API Layer**
- **Backend:**
  - `api/routes/integration/lms.py` → LMS integration endpoints
  - `api/routes/integration/flowbook.py` → FlowBook integration endpoints
  - `services/integration_service.py` → Integration logic
  - `api/main.py` → OpenAPI documentation generation
- **Frontend:**
  - `client/api.ts` → Auto-generated from OpenAPI
  - `client/models.ts` → TypeScript types from Pydantic schemas

**FR41-FR46: Search & Asset Discovery**
- **Backend:**
  - `services/search_service.py` → Search logic (PostgreSQL full-text search)
  - `api/routes/search.py` → Search API endpoints
  - `repositories/asset_repository.py` → Search queries with filters
- **Frontend:**
  - `routes/assets/components/AssetFilter.tsx` → Search/filter UI
  - `hooks/useSearch.ts` → Search state management

**FR47-FR52: Streaming & Media Delivery**
- **Backend:**
  - `services/minio_service.py` → Generate presigned URLs with HTTP Range support
  - `services/download_service.py` → Streaming ZIP downloads
  - `api/routes/download.py` → Download endpoints
- **Frontend:**
  - `routes/assets/components/AssetPreview.tsx` → Video/image preview
  - `hooks/useDownload.ts` → Download logic

**FR53-FR60: Audit & Compliance**
- **Backend:**
  - `models/audit_log.py` → AuditLog table (immutable, append-only)
  - `services/audit_service.py` → Audit log creation, reporting
  - `repositories/audit_log_repository.py` → Audit queries
  - `middleware/audit.py` → Automatic audit logging for CRUD operations
  - `api/routes/audit_logs.py` → Audit API endpoints
- **Frontend:**
  - `routes/admin/AuditLogsPage.tsx` → Audit log viewer (admin only)
  - `routes/admin/components/AuditLogTable.tsx` → Audit log table
  - `hooks/useAuditLogs.ts` → Audit log data fetching

**FR61-FR67: System Operations & Monitoring**
- **Backend:**
  - `api/routes/health.py` → Health check endpoint
  - `api/routes/metrics.py` → Prometheus metrics
  - `middleware/logging.py` → Structured JSON logging
  - `middleware/request_id.py` → Request ID tracing
  - `core/config.py` → Environment-based configuration
- **Deployment:**
  - `.github/workflows/deploy.yml` → CI/CD pipeline
  - `scripts/backup-db.sh` → Backup script
  - `docker-compose.yml` → MinIO metrics exposure

**Cross-Cutting Concerns:**

**Request Tracing**
- **Backend:**
  - `middleware/request_id.py` → Generate UUID per request
  - All log entries include `request_id`
  - Error responses include `request_id`
- **Frontend:**
  - `lib/api.ts` → Axios interceptor attaches `X-Request-ID` to all requests
  - Error messages display `request_id` for support

**Error Handling**
- **Backend:**
  - `core/exceptions.py` → Custom exception classes
  - `app/main.py` → Global exception handlers
  - All errors return `{error_code, message, details, request_id, timestamp}`
- **Frontend:**
  - `components/Common/ErrorMessage.tsx` → Displays API errors
  - `lib/api.ts` → Axios interceptor transforms errors to consistent format

**Authentication Flow**
- **Backend:** `api/routes/auth.py` → `services/auth_service.py` → `core/security.py` (JWT)
- **Frontend:** `routes/auth/LoginPage.tsx` → `contexts/AuthContext.tsx` → `lib/auth.ts` (localStorage)
- **Protection:** `api/deps.py` → `get_current_user` dependency injected into all protected routes

**Tenant Isolation**
- **Backend:** Middleware → Set `tenant_id` in request context → Repository filters all queries by `tenant_id` → PostgreSQL RLS policies enforce
- **Frontend:** AuthContext stores `tenant_id` from JWT → UI filters content by tenant

## Integration Points

**Internal Communication:**

**Backend Layers:**

```
Routes (FastAPI endpoints)
   ↓ (dependency injection)
Services (business logic)
   ↓ (direct calls)
Repositories (data access)
   ↓ (SQLModel queries)
PostgreSQL Database
```

**MinIO Integration:**

```
Routes → Services → MinIOService (wrapper around minio Python SDK)
   ↓ (presigned URLs)
Frontend uploads/downloads directly to MinIO (zero-proxy)
```

**Frontend Data Flow:**

```
Component → TanStack Query Hook (useAssets, useUpload, etc.)
   ↓ (HTTP requests via auto-generated client)
Backend API
   ↓ (JSON response)
TanStack Query Cache → Component re-renders
```

**External Integrations:**

**LMS Integration:**

```
LMS → POST /api/v1/integrations/lms/assignments
   {teacher_id, asset_id, permissions: ["read", "download"]}
   ↓
Backend creates AssetPermission rows
   ↓
Teacher can now access asset in DCS frontend
```

**FlowBook Integration:**

```
FlowBook → GET /api/v1/integrations/flowbook/config?user_id={id}
   ↓
Backend queries user's granted assets
   ↓
Backend generates presigned URLs for each asset
   ↓
Returns config.json: {assets: [{id, url, ...}]}
   ↓
FlowBook downloads assets directly from MinIO using URLs
```

**Data Flow:**

**Upload Flow:**

```
1. Frontend: User selects file
2. Frontend → POST /api/v1/upload/init {file_name, file_size, mime_type}
3. Backend: Create Asset metadata row, generate presigned URLs for chunks
4. Backend → Response: {asset_id, chunk_urls: ["presigned_url_1", ...]}
5. Frontend: Upload chunks directly to MinIO using presigned URLs
6. Frontend → POST /api/v1/upload/complete {asset_id, etags: ["etag1", ...]}
7. Backend: Validate ETags, mark asset as uploaded, create audit log
8. Backend → Response: {asset: {id, url, ...}}
```

**Download Flow:**

```
1. Frontend: User clicks download button
2. Frontend → GET /api/v1/download/{asset_id}
3. Backend: Check permissions, generate presigned download URL (1-hour TTL)
4. Backend → Response: {download_url: "presigned_url"}
5. Frontend: Initiate download from MinIO using presigned URL (direct, no proxy)
6. Backend: Create audit log entry (asset.downloaded)
```

**Search Flow:**

```
1. Frontend: User types search query + applies filters
2. Frontend → GET /api/v1/search?q=textbook&mime_type_filter=application/pdf&page=1
3. Backend: AssetRepository queries with PostgreSQL full-text search + filters + tenant_id
4. Backend → Response: {items: [...], total, page, page_size, total_pages}
5. Frontend: TanStack Query caches result, displays AssetCard components
```

## File Organization Patterns

**Configuration Files:**

**Root Level:**

- `.env` → Environment variables (secrets, DB connection, MinIO credentials) - **Never commit**
- `.env.example` → Template for `.env` - **Commit this**
- `docker-compose.yml` → Production configuration
- `docker-compose.override.yml` → Local development overrides

**Backend:**

- `backend/.env` → Backend-specific overrides (optional)
- `backend/pyproject.toml` → Python dependencies (uv package manager)
- `backend/alembic.ini` → Alembic migration configuration

**Frontend:**

- `frontend/.env` → Frontend-specific variables (`VITE_API_URL`)
- `frontend/vite.config.ts` → Vite build configuration
- `frontend/tailwind.config.js` → Tailwind CSS configuration
- `frontend/tsconfig.json` → TypeScript compiler options

**Source Organization:**

**Backend Layered Architecture:**

```
Routes (API layer)
   → Pydantic schemas for request/response validation
Services (Business logic layer)
   → Orchestrate multiple repositories, call MinIOService
Repositories (Data access layer)
   → SQLModel queries, enforce tenant_id filtering
Models (Database schema)
   → SQLModel ORM models (map to PostgreSQL tables)
```

**Frontend Feature-Based Organization:**

```
routes/
   {feature}/
      {Feature}Page.tsx     → Main page component, owns data fetching
      components/
         {Feature}Card.tsx  → Presentational components
         {Feature}Form.tsx
```

**Shared code:**

```
components/ui/            → shadcn/ui base components (Button, Dialog, etc.)
components/Common/        → Shared app components (Navbar, ErrorBoundary)
hooks/                    → Custom React hooks (useAssets, useAuth)
lib/                      → Utilities (formatters, validators, API client)
```

**Test Organization:**

**Backend Tests:**

```
tests/
   conftest.py            → Pytest fixtures (test DB, test MinIO, test users)
   api/
      test_assets.py      → Tests for api/routes/assets.py
   services/
      test_asset_service.py → Tests for services/asset_service.py
   repositories/
      test_asset_repository.py → Tests for repositories/asset_repository.py
```

**Frontend Tests:**

```
tests/
   setup.ts               → Vitest setup (mock API, React Testing Library)
   components/
      AssetCard.test.tsx  → Tests for routes/assets/components/AssetCard.tsx
   hooks/
      useAssets.test.ts   → Tests for hooks/useAssets.ts
```

**Asset Organization:**

**Static Assets (Frontend):**

```
frontend/public/
   favicon.ico
   assets/
      logo.svg
      images/
```

**User-Uploaded Assets (MinIO):**

```
MinIO Bucket: assets/
   publishers/{publisher_id}/
      {asset_id}/
         {version_id}/
            file.pdf
   teachers/{teacher_id}/
      {asset_id}/
         {version_id}/
            video.mp4
   students/{student_id}/
      (students typically don't upload, only read)
```

## Development Workflow Integration

**Development Server Structure:**

**Local Development (Docker Compose):**

```bash
docker-compose up
# Starts:
# - PostgreSQL on localhost:5432
# - MinIO on localhost:9000 (API), localhost:9001 (console)
# - Backend on localhost:8000 (FastAPI with hot reload)
# - Frontend on localhost:5173 (Vite dev server with HMR)
```

**Backend Hot Reload:**

- FastAPI auto-reloads on file changes in `backend/app/`
- SQLModel schema changes require manual Alembic migration:
  ```bash
  docker-compose exec backend alembic revision --autogenerate -m "Add new column"
  docker-compose exec backend alembic upgrade head
  ```

**Frontend Hot Module Replacement (HMR):**

- Vite HMR on file changes in `frontend/src/`
- Tailwind CSS recompiles on utility class changes
- TanStack Query DevTools available at `http://localhost:5173/__react-query-devtools__`

**Build Process Structure:**

**Backend Build:**

```dockerfile
# Multi-stage Dockerfile
# Stage 1: Build dependencies
FROM python:3.11 AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync

# Stage 2: Production image
FROM python:3.11-slim
COPY --from=builder /app/.venv /app/.venv
COPY app/ /app/app/
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

**Frontend Build:**

```dockerfile
# Multi-stage Dockerfile
# Stage 1: Vite build
FROM node:20 AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build  # Vite builds to dist/

# Stage 2: Nginx serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
```

**Deployment Structure:**

**VPS Deployment:**

```bash
# Deploy script (scripts/deploy.sh)
1. SSH to VPS
2. Pull latest Docker images from registry
3. Run database migrations: docker-compose exec backend alembic upgrade head
4. Blue-green deployment:
   a. Start new containers with different names (backend-blue, frontend-blue)
   b. Health check: GET /health
   c. If healthy: Update Traefik routing to new containers
   d. Stop old containers (backend-green, frontend-green)
5. Verify deployment: Check health endpoint, check logs
```

**Traefik Reverse Proxy:**

```yaml
# docker-compose.yml labels for Traefik
backend:
  labels:
    - "traefik.http.routers.backend.rule=Host(`api.dreamcentral.com`) && PathPrefix(`/api/`)"
    - "traefik.http.routers.backend.tls.certresolver=letsencrypt"

frontend:
  labels:
    - "traefik.http.routers.frontend.rule=Host(`app.dreamcentral.com`)"
    - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```

**Environment-Specific Configuration:**

```
Development:   .env.local (SQLite for quick tests, local MinIO)
Staging:       .env.staging (Separate PostgreSQL/MinIO instances)
Production:    .env.production (Production DB, production MinIO with backups)
```

**CI/CD Pipeline Structure:**

```yaml
# .github/workflows/deploy.yml
1. Test Backend (pytest with coverage > 80%)
2. Test Frontend (Vitest + component tests)
3. Build Docker Images (backend, frontend)
4. Push to GitHub Container Registry
5. Deploy to VPS:
   - SSH to VPS
   - Pull images
   - Run migrations
   - Blue-green deployment
   - Health check
   - Rollback if health check fails
```
