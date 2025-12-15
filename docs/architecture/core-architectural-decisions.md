# Core Architectural Decisions

## Decision Priority Analysis

**Critical Decisions (Block Implementation):**

These decisions must be made before development can begin:

1. **MinIO Integration Strategy** - Core storage layer configuration
2. **Multi-Tenant Authorization Pattern** - Security and data isolation foundation
3. **API Versioning Strategy** - Stability across LMS/FlowBook/Kanban integrations
4. **Signed URL Generation** - Zero-proxy architecture implementation
5. **Database Multi-Tenancy Pattern** - Row-level security and query isolation

**Important Decisions (Shape Architecture):**

These decisions significantly impact architecture but can evolve:

1. **Rate Limiting Strategy** - Performance and abuse prevention per role
2. **Error Handling Standards** - Developer experience and debugging
3. **Frontend State Management** - Client architecture patterns
4. **Monitoring & Logging Approach** - Operational visibility
5. **CI/CD Pipeline Structure** - Deployment automation

**Deferred Decisions (Post-MVP):**

These can be addressed after initial launch:

1. **Advanced caching strategies** - Begin with TanStack Query defaults
2. **Horizontal scaling patterns** - VPS single-instance adequate for 3-month targets
3. **Advanced search capabilities** - Basic PostgreSQL full-text search sufficient initially
4. **CDN integration** - Direct MinIO access adequate for initial scale

## Data Architecture

**Database: PostgreSQL 14+ with SQLModel**

- **Decision:** Use PostgreSQL as provided by starter template
- **Version:** PostgreSQL 14+ (latest stable LTS)
- **ORM:** SQLModel (combines SQLAlchemy 2.0 + Pydantic V2)
- **Rationale:** Starter template provides production-ready configuration; SQLModel offers type safety and async support
- **Affects:** All backend data operations, API schemas, database migrations

**Multi-Tenant Data Isolation:**

- **Decision:** Row-level security with tenant_id columns on all tables
- **Pattern:** Middleware injects user context into database queries; PostgreSQL RLS policies enforce isolation
- **Rationale:** Aligns with PRD requirement for prefix-based multi-tenancy and compliance (COPPA/FERPA)
- **Affects:** Database schema design, API middleware, all CRUD operations

**Data Validation Strategy:**

- **Decision:** Pydantic V2 for all request/response validation
- **Implementation:** Pydantic models for API schemas, SQLModel for database models
- **Rationale:** Type safety across API boundaries, automatic OpenAPI documentation, runtime validation
- **Affects:** API routes, database models, frontend TypeScript client generation

**Database Migration Approach:**

- **Decision:** Alembic with auto-generation from SQLModel changes
- **Pattern:** Migration files in version control, tested in staging before production
- **Rationale:** Starter template provides Alembic integration; supports zero-downtime migrations
- **Affects:** Deployment process, database schema evolution, rollback procedures

**Caching Strategy:**

- **Decision:** Start with TanStack Query on frontend, Redis for backend session cache (future)
- **Initial Scope:** Client-side caching via TanStack Query (5-minute stale time for asset metadata)
- **Future Enhancement:** Redis for signed URL caching and rate limit counters (deferred to post-MVP)
- **Rationale:** TanStack Query provides sufficient caching for initial scale; Redis adds complexity without immediate need
- **Affects:** Frontend data fetching, API response times, infrastructure complexity

**MinIO Object Storage Integration:**

- **Decision:** Official `minio` Python SDK with single-bucket, prefix-based multi-tenancy
- **SDK Version:** `minio` 7.2.x (latest stable as of 2025)
- **Deployment:** MinIO container in Docker Compose alongside backend/frontend
- **Bucket Strategy:** Single `assets` bucket with tenant-specific prefixes:
  - `/publishers/{publisher_id}/...`
  - `/teachers/{teacher_id}/...`
  - `/students/{student_id}/...`
  - `/schools/{school_id}/...`
- **Signed URL Generation:**
  - FastAPI backend generates presigned URLs via MinIO SDK
  - Default TTL: 1 hour (configurable per request type)
  - Upload URLs: 15 minutes TTL for security
  - Download URLs: 1 hour TTL for classroom usage
- **Versioning:** MinIO versioning enabled at bucket level for soft delete/restore (FR7)
- **Rationale:**
  - Official SDK provides MinIO-specific features (versioning control, admin operations)
  - Single bucket reduces management overhead at current scale
  - Prefix-based paths align with PRD multi-tenancy requirements
  - Presigned URLs enable zero-proxy architecture (NFR-P4)
- **Affects:** Upload/download workflows, soft delete implementation, asset versioning, trash management

**MinIO Configuration:**

- **Storage Mode:** Single-node (development), distributed mode ready for production scaling
- **Encryption:** Server-side encryption enabled (AES-256) for compliance (NFR-S7)
- **Metrics:** Prometheus endpoint exposed for monitoring (NFR-M7)
- **Backup Strategy:** MinIO `mc mirror` replication to backup bucket (daily schedule)

## Authentication & Security

**Authentication Method:**

- **Decision:** JWT tokens with bcrypt password hashing (from starter template)
- **Token Algorithm:** RS256 (asymmetric signing)
- **Token Expiry:** Access token 30 minutes, refresh token 7 days
- **Rationale:** Industry standard, starter template provides production-ready implementation
- **Affects:** API authentication, frontend session management, mobile app integration

**Multi-Tenant Authorization Pattern:**

- **Decision:** Role-based access control (RBAC) with row-level security
- **Implementation:**
  - PostgreSQL row-level security (RLS) policies on all tenant-specific tables
  - Middleware injects `current_user_id` and `tenant_id` into all database queries
  - Ownership validation: Users write only to their own prefix (publishers/{id}/, teachers/{id}/, etc.)
  - Read access: Managed via `asset_permissions` table populated by LMS assignment workflow
- **Role Hierarchy:**
  - **Admin/Supervisor:** Full access to all tenants (bypass RLS)
  - **Publisher:** Write to `/publishers/{id}/`, read own assets + granted assets
  - **Teacher:** Write to `/teachers/{id}/`, read granted assets from publishers + own creations
  - **Student:** Read-only access to assets granted by teacher via LMS
  - **School:** Organizational role, manages teacher accounts
- **Rationale:** Aligns with PRD access control requirements (FR12-FR24), supports LMS-driven permission model
- **Affects:** Database schema, API middleware, MinIO prefix validation, frontend route protection

**API Security Enhancements:**

- **Rate Limiting:**
  - **Strategy:** Token bucket algorithm per user ID + role
  - **Limits:**
    - Publisher: 1000 requests/hour (bulk upload workflows)
    - Teacher: 500 requests/hour (classroom operations)
    - Student: 100 requests/hour (individual browsing)
    - Admin/Supervisor: Unlimited
  - **Implementation:** In-memory rate limiter (Python library: `slowapi`)
  - **Future:** Move to Redis for distributed rate limiting
  - **Rationale:** Prevent abuse while accommodating different user patterns (FR20)
  - **Affects:** API middleware, error responses, client retry logic

- **CORS Configuration:**
  - **Allowed Origins:** LMS domain, FlowBook desktop app, Kanban domain (configurable via env)
  - **Credentials:** Allowed (for JWT cookies)
  - **Rationale:** Secure cross-origin access for integrated applications
  - **Affects:** API middleware, frontend deployment, mobile app CORS

- **Signed URL Validation:**
  - **Strategy:** HMAC-SHA256 signatures generated by backend, validated by MinIO
  - **Expiry:** Embedded in URL, enforced by MinIO
  - **One-time URLs:** Not implemented initially (deferred to post-MVP)
  - **Rationale:** Zero-proxy architecture requires client-to-MinIO direct access with security (FR16)
  - **Affects:** Upload/download workflows, URL sharing, security audit logs

**Data Encryption:**

- **At Rest:**
  - MinIO server-side encryption enabled (SSE-S3 mode with AES-256)
  - PostgreSQL transparent data encryption (TDE) optional (deferred to production hardening)
  - **Rationale:** COPPA/FERPA compliance for educational content (NFR-S7)

- **In Transit:**
  - TLS 1.3 for all API communication (Traefik handles HTTPS termination)
  - MinIO TLS enabled for client-to-storage communication
  - **Rationale:** Industry standard, protect student/teacher data (NFR-S2)

- **Secrets Management:**
  - Docker secrets for database passwords, MinIO credentials
  - Environment variables for non-sensitive configuration
  - **Rationale:** Prevent credentials in git, support different environments
  - **Affects:** Deployment process, Docker Compose configuration, CI/CD pipeline

**Audit Logging for Security:**

- **Decision:** Immutable append-only audit table in PostgreSQL
- **Logged Events:** All CRUD operations on assets, permission changes, authentication events
- **Schema:** `audit_log(id, timestamp, user_id, action, resource_type, resource_id, metadata_json)`
- **Retention:** Configurable (default 90 days per NFR compliance)
- **Rationale:** COPPA/FERPA compliance, security incident investigation (FR53-FR60)
- **Affects:** API middleware, database schema, compliance reporting

## API & Communication Patterns

**API Design Pattern:**

- **Decision:** RESTful API with OpenAPI 3.1 documentation
- **Standard:** JSON request/response bodies, HTTP status codes for semantics
- **Documentation:** Automatic generation via FastAPI at `/docs` (Swagger UI) and `/redoc`
- **Rationale:** Industry standard, starter template provides excellent OpenAPI support
- **Affects:** All API endpoints, frontend client generation, external integrations

**API Versioning Strategy:**

- **Decision:** URL-based versioning (`/api/v1/...`)
- **Pattern:** Major version in URL path, minor changes backward-compatible
- **Rationale:**
  - LMS/FlowBook/Kanban require stable contracts across updates
  - Clear version visibility for debugging
  - Supports running multiple versions during transitions
- **Migration Path:** New version at `/api/v2/...` while maintaining `/api/v1/...` for 6 months
- **Affects:** API routing, client libraries, deprecation notices, integration contracts

**Multipart Upload Support:**

- **Decision:** Chunked upload for files >100MB
- **Implementation:**
  - Backend generates multiple presigned PUT URLs for MinIO (one per chunk)
  - Client uploads chunks in parallel, signals completion to backend
  - Backend validates all chunks via MinIO ETags before marking upload complete
- **Chunk Size:** 10MB (configurable)
- **Rationale:** Large video/ZIP files for publishers (FR4), avoid memory buffering (NFR-P4)
- **Affects:** Upload API endpoints, frontend upload component, progress tracking

**Streaming Responses:**

- **Decision:** FastAPI StreamingResponse for large data operations
- **Use Cases:**
  - ZIP file downloads (stream from MinIO without full buffering)
  - Large asset lists (paginated JSON streaming)
  - Audit log exports
- **Rationale:** Meet NFR-P4 (no file buffering in memory), support large datasets
- **Affects:** Download endpoints, ZIP generation, memory usage patterns

**Error Handling Standards:**

- **Decision:** Standardized error response format with request tracing
- **Format:**
  ```json
  {
    "error_code": "ASSET_NOT_FOUND",
    "message": "Asset with ID 12345 does not exist or you lack permission",
    "details": {"asset_id": 12345, "user_id": 67890},
    "request_id": "uuid-v4-request-id",
    "timestamp": "2025-12-15T10:30:00Z"
  }
  ```
- **Error Codes:** Enum-based codes for client handling (e.g., `ASSET_NOT_FOUND`, `PERMISSION_DENIED`, `QUOTA_EXCEEDED`)
- **Request ID:** UUID per request, included in all logs for tracing
- **Client Guidance:** Human-readable messages with actionable next steps
- **Rationale:** Developer experience for integrations, debugging production issues (NFR-M8)
- **Affects:** Exception handling middleware, logging, frontend error UI, API documentation

**Request ID Tracing:**

- **Decision:** UUID v4 per request, propagated across all logs and errors
- **Implementation:** Middleware generates request_id at API entry, attaches to all log entries
- **Rationale:** Critical for debugging distributed issues across API + MinIO + Database (NFR-M8)
- **Affects:** Logging configuration, error responses, monitoring dashboards

**Communication Between Services:**

- **Decision:** Direct HTTP calls for backend-to-MinIO, future message queue for async operations
- **Current Scope:** Synchronous HTTP for MinIO SDK calls
- **Future Enhancement:** Redis pub/sub or RabbitMQ for background jobs (ZIP generation, thumbnail creation)
- **Rationale:** Keep initial architecture simple, add async processing when needed
- **Affects:** Service deployment, background job processing, scalability patterns

## Frontend Architecture

**State Management Approach:**

- **Decision:** TanStack Query for server state, React Context for auth, local state for UI
- **Server State:** TanStack Query with 5-minute stale time for asset metadata
- **Auth State:** React Context + localStorage for JWT token persistence
- **UI State:** useState/useReducer for component-local concerns (modals, form inputs)
- **No Redux:** Project complexity doesn't warrant Redux overhead
- **Rationale:**
  - TanStack Query provides excellent caching, optimistic updates, invalidation
  - React Context sufficient for global auth state
  - Keeps bundle size small, developer experience simple
- **Affects:** Frontend data fetching, cache invalidation, component architecture

**Component Architecture:**

- **Decision:** Feature-based folder structure with shared UI components
- **Structure:**
  ```
  frontend/src/
  ├── components/
  │   ├── ui/              # shadcn/ui base components (Button, Dialog, etc.)
  │   └── Common/          # Shared app components (Navbar, Footer)
  ├── routes/
  │   ├── assets/          # Asset management pages + components
  │   ├── upload/          # Upload workflow pages + components
  │   ├── admin/           # Admin dashboard pages + components
  │   └── _layout/         # Layout wrappers
  ├── hooks/
  │   ├── useAssets.ts     # Asset CRUD operations
  │   ├── useUpload.ts     # Multipart upload logic
  │   └── useAuth.ts       # Authentication helpers
  ```
- **Rationale:** Co-locate feature logic for maintainability, share UI components for consistency
- **Affects:** Code organization, import paths, component reusability

**Routing Strategy:**

- **Decision:** React Router v6 with protected routes for role-based access
- **Protection Pattern:**
  ```tsx
  <ProtectedRoute allowedRoles={['publisher', 'admin']}>
    <PublisherDashboard />
  </ProtectedRoute>
  ```
- **Rationale:** Starter template provides React Router; role-based route protection aligns with RBAC
- **Affects:** Route configuration, navigation guards, unauthorized access handling

**Performance Optimization:**

- **Code Splitting:**
  - Automatic route-based splitting via Vite (lazy loading)
  - Manual splitting for large components (asset preview modals)
  - **Rationale:** Reduce initial bundle size, faster page loads

- **Virtual Scrolling:**
  - Use `react-window` for long asset lists (>100 items)
  - **Rationale:** Maintain 60fps scrolling with thousands of assets (NFR-P1)

- **Image Optimization:**
  - MinIO thumbnail generation for preview images
  - Lazy loading images with `loading="lazy"`
  - **Rationale:** Reduce bandwidth, improve perceived performance

- **Bundle Optimization:**
  - Tree shaking via Vite
  - Import only used shadcn/ui components
  - **Rationale:** Keep bundle size under 500KB for fast load times

- **Affects:** Build configuration, component design, user experience

**TypeScript Type Safety:**

- **Decision:** Auto-generated API client from OpenAPI spec
- **Generation:** `openapi-typescript-codegen` generates client at build time
- **Benefit:** End-to-end type safety from backend Pydantic models to frontend React components
- **Rationale:** Catch API contract mismatches at compile time, excellent DX
- **Affects:** Frontend build process, API integration, refactoring safety

## Infrastructure & Deployment

**Hosting Strategy:**

- **Decision:** VPS deployment with Docker Compose orchestration
- **Provider:** Flexible (Hetzner, DigitalOcean, Linode - user choice)
- **Resources:** 4 vCPU, 8GB RAM, 100GB SSD (initial), scalable to 16 vCPU/32GB RAM
- **Rationale:** User preference for VPS, cost-effective for initial scale, simple operations
- **Affects:** Deployment scripts, infrastructure cost, scaling approach

**Container Orchestration:**

- **Decision:** Docker Compose for development and production
- **Services:**
  - `backend` (FastAPI app)
  - `frontend` (Nginx serving Vite build)
  - `db` (PostgreSQL 14)
  - `minio` (MinIO object storage)
  - `traefik` (Reverse proxy + HTTPS)
- **Rationale:** Starter template provides production-ready Compose config, adequate for VPS deployment
- **Future:** Migrate to Kubernetes if multi-region scaling needed (deferred)
- **Affects:** Deployment process, service configuration, local development parity

**Reverse Proxy & HTTPS:**

- **Decision:** Traefik with automatic Let's Encrypt certificates
- **Configuration:** Traefik routes `/api/*` to backend, `/*` to frontend, handles HTTPS termination
- **Certificate Renewal:** Automatic via Let's Encrypt ACME protocol
- **Rationale:** Starter template provides Traefik setup, zero-configuration HTTPS
- **Affects:** Domain configuration, SSL certificate management, HTTP/2 support

**CI/CD Pipeline:**

- **Decision:** GitHub Actions for automated testing, building, and deployment
- **Pipeline Stages:**
  1. **Test:** Run pytest (backend) + Vitest (frontend) on every PR
  2. **Build:** Docker image builds for backend + frontend
  3. **Push:** Push images to registry (GitHub Container Registry)
  4. **Deploy:** SSH to VPS, pull images, docker-compose up with zero downtime
- **Zero-Downtime Strategy:**
  - Blue-green deployment: Start new containers, health check, swap Traefik routing, stop old containers
  - Database migrations run before container swap
- **Rationale:** Starter template provides GitHub Actions workflows, meets NFR-M2 (zero-downtime updates)
- **Affects:** Deployment speed, rollback procedures, production stability

**Environment Configuration:**

- **Decision:** Environment-specific `.env` files managed via Pydantic Settings
- **Environments:**
  - **Development:** `.env.local` with local MinIO, debug logging
  - **Staging:** `.env.staging` with staging MinIO instance, test data
  - **Production:** `.env.production` with production MinIO, error-only logging
- **Secrets:** Stored in VPS environment, never in git
- **Rationale:** Pydantic Settings provides type-safe config, supports multiple environments
- **Affects:** Configuration management, deployment process, secret handling

**Monitoring & Logging:**

- **Structured Logging:**
  - Python `logging` with JSON formatter
  - Log format: `{"timestamp": "...", "level": "...", "request_id": "...", "user_id": "...", "message": "..."}`
  - **Rationale:** Machine-parseable logs for analysis, request_id tracing (NFR-M8)

- **MinIO Metrics:**
  - Prometheus endpoint exposed by MinIO at `:9000/minio/v2/metrics/cluster`
  - Metrics: Storage usage, request rates, error rates
  - **Rationale:** Operational visibility into storage layer (NFR-M7)

- **Health Checks:**
  - API health endpoint: `GET /health` returns `{"status": "healthy", "database": "ok", "minio": "ok"}`
  - Used by Traefik for container health, external uptime monitoring
  - **Rationale:** Enable automated recovery, uptime monitoring (NFR-R1)

- **Future Monitoring:**
  - Prometheus + Grafana for metrics visualization (deferred to post-MVP)
  - Sentry for error tracking (deferred to post-MVP)
  - **Rationale:** Start simple, add observability as operational needs grow

**Backup & Disaster Recovery:**

- **Database Backups:**
  - PostgreSQL `pg_dump` daily via cron job
  - Retention: 30 days rolling backups
  - Storage: Separate MinIO bucket or S3-compatible backup service

- **MinIO Backups:**
  - `mc mirror` replication to backup bucket (daily schedule)
  - Versioning provides point-in-time recovery for individual files
  - **Rationale:** Meet NFR-R3 (zero data loss), NFR-R7 (RTO <30 minutes)

- **Disaster Recovery:**
  - Backup restoration tested quarterly
  - Recovery playbook documented in operations guide
  - **Rationale:** Ensure backups are actually restorable, meet RTO targets

**Scaling Strategy:**

- **Initial Deployment:** Single VPS with all services
- **First Scaling Step (if needed):**
  - Separate database to dedicated VPS
  - Separate MinIO to dedicated VPS with distributed mode (4+ nodes)
  - Multiple backend instances behind Traefik load balancing
- **Horizontal Scaling:**
  - Backend: Stateless, can scale horizontally behind Traefik
  - Frontend: Static files, serve via CDN if needed
  - Database: PostgreSQL read replicas for read-heavy workloads
- **Rationale:** Start simple, scale components independently as bottlenecks identified
- **Affects:** Infrastructure cost, deployment complexity, performance headroom

## Decision Impact Analysis

**Implementation Sequence:**

The following sequence ensures dependencies are satisfied during implementation:

1. **Project Initialization** (Epic 1: Foundation Setup)
   - Initialize from FastAPI Full Stack Template
   - Configure Docker Compose with MinIO service
   - Set up PostgreSQL with multi-tenant schema

2. **Authentication & Authorization** (Epic 2: Security Foundation)
   - Extend starter template auth with RBAC roles
   - Implement row-level security in PostgreSQL
   - Create user management API endpoints

3. **MinIO Integration** (Epic 3: Storage Layer)
   - Configure MinIO service in Docker Compose
   - Implement presigned URL generation
   - Create upload/download API endpoints with chunking

4. **Asset Management** (Epic 4: Core Functionality)
   - Asset CRUD operations with metadata
   - Soft delete/restore with MinIO versioning
   - Folder organization and search

5. **Frontend UI** (Epic 5: User Interface)
   - Asset library with previews
   - Upload workflow with progress tracking
   - Admin dashboard for user/asset management

6. **Integration APIs** (Epic 6: External Systems)
   - LMS assignment permission management
   - FlowBook config.json delivery endpoint
   - API documentation finalization

7. **Audit & Compliance** (Epic 7: Compliance Layer)
   - Immutable audit log implementation
   - Compliance reporting endpoints
   - Data retention policies

8. **Monitoring & Operations** (Epic 8: Production Readiness)
   - Health check endpoints
   - Structured logging implementation
   - CI/CD pipeline setup
   - Backup/restore procedures

**Cross-Component Dependencies:**

**Authentication → All Components:**
- All API endpoints require JWT authentication
- Frontend routing depends on user role
- MinIO presigned URLs embed user permissions
- **Impact:** Auth must be implemented first, all features depend on it

**MinIO Integration → Asset Features:**
- Upload/download workflows depend on presigned URL generation
- Versioning depends on MinIO bucket configuration
- Soft delete depends on MinIO versioning enabled
- **Impact:** MinIO integration must precede asset management features

**Multi-Tenant Schema → Data Operations:**
- Row-level security affects all database queries
- API middleware must inject tenant context
- Frontend must filter UI based on user's tenant
- **Impact:** Multi-tenant schema must be established early, affects all data operations

**API Versioning → External Integrations:**
- LMS/FlowBook/Kanban depend on stable API contracts
- Breaking changes require new API version
- Frontend must specify API version in client generation
- **Impact:** Versioning strategy must be established before external integrations

**Audit Logging → Compliance:**
- Compliance reporting depends on audit log data
- Retention policies depend on audit table structure
- Security investigations depend on comprehensive logging
- **Impact:** Audit logging must be implemented alongside core features, not retroactively

**Monitoring → Production Operations:**
- Health checks required for zero-downtime deployment
- Metrics required for capacity planning
- Structured logs required for debugging production issues
- **Impact:** Monitoring should be implemented incrementally with each feature, not deferred to end

**Technological Dependencies:**

- **PostgreSQL RLS → SQLModel:** Row-level security policies must work with SQLModel queries
- **Pydantic V2 → OpenAPI → TypeScript Client:** Changes to Pydantic models cascade to frontend types
- **TanStack Query → API Design:** Query keys and invalidation strategies must align with API structure
- **Traefik → Docker Compose → Services:** Reverse proxy configuration tightly coupled to service naming
- **MinIO SDK Version → Python Async:** Ensure MinIO SDK supports async operations for FastAPI
