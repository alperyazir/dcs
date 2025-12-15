---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: [
  "/Users/alperyazir/Dev/dream-central-storage/docs/prd.md",
  "/Users/alperyazir/Dev/dream-central-storage/docs/architecture/index.md",
  "/Users/alperyazir/Dev/dream-central-storage/docs/ux-design-specification/index.md"
]
workflowType: 'epics-stories'
lastStep: 4
status: 'complete'
completedAt: '2025-12-15'
totalEpics: 9
totalStories: 48
---

# dream-central-storage - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for dream-central-storage, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Asset Management (FR1-FR11):**
- FR1: Users can upload single files to their designated storage area with progress tracking
- FR2: Users can upload multiple files via ZIP archive with streaming extraction
- FR3: System can automatically filter system files (.DS_Store, __MACOSX/, Thumbs.db) during ZIP extraction
- FR4: Users can download files from storage areas they have access to
- FR5: Users can delete files from their designated storage area (soft delete to trash)
- FR6: Users can restore deleted files from trash within retention period
- FR7: System can maintain version history when files are updated
- FR8: Users can view version information for assets (version number, date)
- FR9: System can validate file types and sizes before accepting uploads
- FR10: Users can organize files within their storage area using folder/prefix structures
- FR11: Users can view asset metadata (owner, type, size, mime_type, upload date, checksum)

**Access Control & Authentication (FR12-FR24):**
- FR12: Users can authenticate using JWT-based tokens
- FR13: Admins can access all storage areas across all tenants
- FR14: Supervisors can access all storage areas across all tenants
- FR15: Publishers can write (upload/update/delete) only to their own publisher storage area
- FR16: Schools can write only to their own school storage area
- FR17: Teachers can write only to their own teacher storage area
- FR18: Students can write only to their own student storage area
- FR19: Teachers can read publisher content when granted access via LMS
- FR20: Students can read teacher materials when granted access via LMS
- FR21: System can generate time-limited signed URLs for secure file access
- FR22: System can enforce role-based authorization at the API level
- FR23: System can validate ownership before allowing write operations
- FR24: System can apply rate limiting to API endpoints

**Multi-Tenant Storage Organization (FR25-FR30):**
- FR25: System can isolate tenant storage using prefix-based paths
- FR26: System can maintain separate storage areas for publishers, schools, teachers, students, and apps
- FR27: System can track owner_type and owner_id for every asset in metadata
- FR28: System can enforce tenant isolation at the physical storage layer
- FR29: System can prevent cross-tenant write access while allowing managed read access
- FR30: System can support trash storage area for soft-deleted files

**Integration & API Layer (FR31-FR40):**
- FR31: Developers can integrate applications using RESTful API endpoints
- FR32: System can provide clear API error responses for debugging
- FR33: System can authenticate API requests using JWT tokens
- FR34: System can return asset metadata via API queries
- FR35: System can support multipart upload for large files
- FR36: System can provide API documentation for integration teams
- FR37: LMS can assign publisher books to teachers via API
- FR38: LMS can assign teacher materials to students via API
- FR39: Applications can download config.json files for FlowBook integration
- FR40: System can support API versioning for multiple application versions

**Search & Asset Discovery (FR41-FR46):**
- FR41: Users can search assets by metadata fields (name, type, owner, date)
- FR42: Users can filter asset lists by asset type (book, video, image, material)
- FR43: Users can view asset library with visual previews for supported formats
- FR44: Publishers can browse their complete asset collection organized by folders
- FR45: Teachers can browse publisher content assigned to them
- FR46: Students can browse teacher materials assigned to them

**Streaming & Media Delivery (FR47-FR52):**
- FR47: System can stream video files with HTTP Range support for seeking
- FR48: System can stream audio files with HTTP Range support
- FR49: System can provide direct MinIO access via signed URLs (no API proxying)
- FR50: Users can preview images, videos, and audio files before downloading
- FR51: System can deliver files with minimal CPU/RAM usage on API layer
- FR52: System can support batch downloads for multiple files

**Audit & Compliance (FR53-FR60):**
- FR53: System can log all user actions (upload, download, delete, restore) with user_id, asset_id, action, IP address, and timestamp
- FR54: System can maintain immutable audit logs that cannot be modified or deleted
- FR55: Admins can generate access reports for compliance reviews
- FR56: System can support configurable data retention policies
- FR57: System can retain files indefinitely until user deletion (default policy)
- FR58: System can permanently delete files after configurable trash retention period
- FR59: System can purge or anonymize user data when user is deleted
- FR60: System can track file integrity using checksums

**System Operations & Monitoring (FR61-FR67):**
- FR61: System can provide health check endpoints for monitoring
- FR62: System can expose MinIO metrics for operational visibility
- FR63: System can maintain PostgreSQL metadata in sync with object storage state
- FR64: System can support database backup and replication
- FR65: Admins can configure storage quotas per tenant (future capability)
- FR66: System can enable encryption at rest for stored files (optional configuration)
- FR67: System can enforce HTTPS/TLS for all API communications

### NonFunctional Requirements

**Performance (NFR-P1 to P9):**
- NFR-P1: Metadata operations (list, search, query) shall complete with P95 response time under 500ms
- NFR-P2: Signed URL generation shall complete within 100ms
- NFR-P3: File upload operations shall not timeout for files up to 10GB
- NFR-P4: Video/audio streaming shall support HTTP Range requests with minimal latency
- NFR-P5: API server CPU utilization shall remain below 70% under normal load
- NFR-P6: API server memory usage shall not exceed 80% of allocated resources
- NFR-P7: File operations shall not buffer entire files in memory (streaming design)
- NFR-P8: System shall support concurrent uploads from multiple users without degradation
- NFR-P9: ZIP extraction shall process files in streaming mode without disk/RAM bottlenecks

**Reliability & Availability (NFR-R1 to R12):**
- NFR-R1: System uptime shall be minimum 99% during first 3 months of operation
- NFR-R2: System uptime shall improve to 99.9% or higher by 12 months
- NFR-R3: Planned maintenance windows shall be scheduled during low-usage periods
- NFR-R4: Zero data loss tolerance - all uploaded files must be preserved
- NFR-R5: File integrity shall be verified using checksums
- NFR-R6: MinIO versioning shall be enabled to protect against accidental overwrites
- NFR-R7: System recovery time objective (RTO) shall be under 30 minutes for critical failures
- NFR-R8: Database backup shall occur daily with point-in-time recovery capability
- NFR-R9: Soft-deleted files shall be recoverable from trash for configured retention period
- NFR-R10: All API errors shall return clear, actionable error messages
- NFR-R11: Failed operations shall not leave system in inconsistent state
- NFR-R12: PostgreSQL metadata shall remain in sync with MinIO object storage state

**Security (NFR-S1 to S13):**
- NFR-S1: All API requests shall be authenticated using valid JWT tokens
- NFR-S2: JWT tokens shall expire after configurable time period (default: 24 hours)
- NFR-S3: Role-based authorization shall be enforced for every API endpoint
- NFR-S4: Signed URLs shall be time-limited (configurable, default: 1 hour)
- NFR-S5: All API communication shall use HTTPS/TLS encryption in transit
- NFR-S6: Encryption at rest shall be configurable and supported by MinIO
- NFR-S7: Sensitive credentials shall never be logged or exposed in error messages
- NFR-S8: Users shall only access storage areas they are authorized for
- NFR-S9: Cross-tenant access shall be prevented at storage and metadata layers
- NFR-S10: Rate limiting shall protect against abuse and denial-of-service attacks
- NFR-S11: Student data handling shall comply with COPPA/FERPA requirements
- NFR-S12: Audit logs shall be immutable and retained for compliance review
- NFR-S13: Data retention policies shall be configurable per compliance needs

**Scalability (NFR-SC1 to SC12):**
- NFR-SC1: System shall support growth to 1TB storage within 3 months
- NFR-SC2: System shall scale to 2TB storage by 12 months
- NFR-SC3: Storage architecture shall support horizontal scaling beyond initial capacity
- NFR-SC4: System shall support 3 integrated applications at 3 months
- NFR-SC5: System shall scale to 5 integrated applications by 12 months
- NFR-SC6: API shall handle concurrent requests from multiple applications
- NFR-SC7: System shall support 10x user growth with less than 10% performance degradation
- NFR-SC8: Multi-tenant architecture shall support adding new tenants without downtime
- NFR-SC9: Database queries shall use proper indexing for efficient multi-tenant isolation
- NFR-SC10: MinIO shall support distributed deployment for storage scaling
- NFR-SC11: API layer shall support horizontal scaling via load balancing
- NFR-SC12: PostgreSQL shall support replication for read scaling

**Maintainability & Operability (NFR-M1 to M10):**
- NFR-M1: System shall expose health check endpoints for monitoring
- NFR-M2: MinIO metrics shall be available for operational visibility
- NFR-M3: Application logs shall include request IDs for debugging and tracing
- NFR-M4: Critical errors shall be logged with sufficient context for troubleshooting
- NFR-M5: System updates shall not require downtime for dependent applications
- NFR-M6: Database migrations shall be backward compatible during deployment
- NFR-M7: API versioning shall support multiple client application versions
- NFR-M8: API documentation shall be comprehensive and up-to-date
- NFR-M9: Integration guides shall be provided for application developers
- NFR-M10: Error codes and messages shall be documented for troubleshooting

**Accessibility (NFR-A1 to A3):**
- NFR-A1: Admin and user panels shall follow WCAG 2.1 Level AA guidelines where applicable
- NFR-A2: Frontend shall be keyboard navigable for users with motor impairments
- NFR-A3: Color contrast shall meet accessibility standards for visual clarity

### Additional Requirements

**From Architecture Document:**

**Starter Template & Project Initialization:**
- **CRITICAL:** Initialize project from Official FastAPI Full Stack Template (https://github.com/fastapi/full-stack-fastapi-template)
- Use copier to generate project structure with configuration: project_name="Dream Central Storage", stack_name="dream-central-storage"
- Complete Docker Compose setup with backend, frontend, PostgreSQL, MinIO, and Traefik services
- Configure Pydantic Settings for environment-specific configuration
- Set up Alembic for database migrations
- Configure pre-commit hooks with ruff (Python) and prettier (TypeScript)

**MinIO Integration:**
- Configure MinIO service in Docker Compose with single-bucket, prefix-based multi-tenancy
- Implement official `minio` Python SDK (version 7.2.x) for object storage operations
- Enable MinIO versioning at bucket level for soft delete/restore functionality
- Configure server-side encryption (AES-256) for compliance
- Expose Prometheus endpoint for MinIO metrics monitoring
- Implement `mc mirror` replication for daily backups

**Database Multi-Tenancy:**
- Implement PostgreSQL row-level security (RLS) with tenant_id columns on all tables
- Create middleware to inject user context (user_id, tenant_id) into all database queries
- Design database schema with multi-tenant isolation: users, assets, asset_versions, asset_permissions, folders, audit_logs, trash, tenants tables
- Configure connection pooling for production workloads
- Set up proper indexing on owner_type/owner_id for fast tenant isolation queries

**API Architecture:**
- Implement URL-based API versioning (`/api/v1/...`)
- Use FastAPI dependency injection for database sessions, authentication, and MinIO client
- Implement standardized error response format with error_code, message, details, request_id, timestamp
- Create request ID tracing (UUID v4 per request) propagated across all logs
- Implement token bucket rate limiting per user ID + role using `slowapi` library

**Security Implementation:**
- Implement JWT authentication with RS256 signing algorithm (access token: 30 min, refresh: 7 days)
- Create custom exceptions for domain errors (AssetNotFoundException, PermissionDeniedException, QuotaExceededException)
- Configure CORS middleware for LMS, FlowBook, and Kanban domains
- Implement signed URL generation with HMAC-SHA256 signatures and configurable TTL (15 min uploads, 1 hour downloads)

**Frontend Architecture:**
- Implement TanStack Query for server state management with 5-minute stale time for asset metadata
- Use React Context only for authentication state (user, login, logout, isAuthenticated)
- Configure automatic OpenAPI TypeScript client generation for type-safe API calls
- Implement protected routes with role-based access using React Router v6
- Use code splitting with Vite for route-based lazy loading
- Implement virtual scrolling with `react-window` for long asset lists (>100 items)

**Infrastructure & Deployment:**
- Configure Traefik reverse proxy with automatic Let's Encrypt certificates
- Set up GitHub Actions CI/CD pipeline with test, build, push, and deploy stages
- Implement blue-green deployment strategy for zero-downtime updates
- Configure structured JSON logging with request_id tracing
- Set up health check endpoints: `GET /health` returns database and MinIO status
- Implement daily PostgreSQL pg_dump backups with 30-day retention

**Implementation Patterns:**
- Follow strict naming conventions: snake_case (Python/API/DB), camelCase (TypeScript vars), PascalCase (classes/components)
- Use layered architecture: routes → services → repositories → models (backend)
- Use feature-based structure: routes/{feature}/components/ (frontend)
- Implement service layer for business logic, repositories for data access
- All database operations must include tenant_id filtering
- Use Pydantic V2 for all request/response validation
- Implement streaming operations (no file buffering in memory) for uploads, downloads, and ZIP extraction

**From UX Design Document:**

**Design System & Components:**
- Implement shadcn/ui component library with Tailwind CSS
- Use Functional Minimalism design direction (clean, professional, trust-building)
- Implement responsive design with breakpoints: mobile (320px), tablet (768px), desktop (1024px), wide (1440px)
- Follow WCAG 2.1 Level AA accessibility guidelines

**Custom Components to Build:**
- Asset Upload Zone: Drag-and-drop interface with file validation and progress tracking
- Video Stream Player: HTTP Range request support for seeking and buffering
- Asset Card: Visual preview with metadata display and action buttons
- Multi-File Progress Tracker: Real-time upload progress for bulk operations
- Asset Browser Table: Sortable, filterable table with virtual scrolling
- Code Documentation Viewer: Syntax-highlighted API documentation (for developer integration)

**UX Consistency Patterns:**
- Implement toast notifications for success/error feedback (5s auto-dismiss)
- Use button hierarchy: Primary (CTA), Secondary (alternatives), Ghost (tertiary)
- Implement skeleton loading states for all async data fetching
- Use modal dialogs for destructive actions with confirmation
- Implement search with debounced input (300ms) and filter chips
- Show empty states with helpful messaging and call-to-action

**Responsive Strategy:**
- Desktop-first approach (primary users are publishers and teachers on workstations)
- Mobile: Single column, simplified navigation, core functionality only
- Tablet: Adaptive layout with side navigation
- Desktop/Wide: Multi-column layouts with sidebar navigation

### FR Coverage Map

**Epic 1 - Platform Foundation & Infrastructure Setup:**
- Architecture Requirement: FastAPI Full Stack Template Initialization
- FR61: Health check endpoints for monitoring
- FR62: Expose MinIO metrics for operational visibility
- FR63: Maintain PostgreSQL metadata in sync with object storage state
- FR64: Database backup and replication
- FR66: Encryption at rest for stored files (optional configuration)
- FR67: Enforce HTTPS/TLS for all API communications

**Epic 2 - Authentication & Multi-Tenant Access Control:**
- FR12: Authenticate using JWT-based tokens
- FR13: Admins can access all storage areas across all tenants
- FR14: Supervisors can access all storage areas across all tenants
- FR15: Publishers can write only to their own publisher storage area
- FR16: Schools can write only to their own school storage area
- FR17: Teachers can write only to their own teacher storage area
- FR18: Students can write only to their own student storage area
- FR19: Teachers can read publisher content when granted access via LMS
- FR20: Students can read teacher materials when granted access via LMS
- FR22: Enforce role-based authorization at the API level
- FR23: Validate ownership before allowing write operations
- FR24: Apply rate limiting to API endpoints
- FR25: Isolate tenant storage using prefix-based paths
- FR26: Maintain separate storage areas for publishers, schools, teachers, students, and apps
- FR27: Track owner_type and owner_id for every asset in metadata
- FR28: Enforce tenant isolation at the physical storage layer
- FR29: Prevent cross-tenant write access while allowing managed read access

**Epic 3 - Core Asset Upload & Storage:**
- FR1: Upload single files to their designated storage area with progress tracking
- FR2: Upload multiple files via ZIP archive with streaming extraction
- FR3: Automatically filter system files (.DS_Store, __MACOSX/, Thumbs.db) during ZIP extraction
- FR9: Validate file types and sizes before accepting uploads
- FR21: Generate time-limited signed URLs for secure file access
- FR49: Provide direct MinIO access via signed URLs (no API proxying)
- FR51: Deliver files with minimal CPU/RAM usage on API layer

**Epic 4 - Asset Download & Streaming:**
- FR4: Download files from storage areas they have access to
- FR47: Stream video files with HTTP Range support for seeking
- FR48: Stream audio files with HTTP Range support
- FR50: Preview images, videos, and audio files before downloading
- FR52: Support batch downloads for multiple files

**Epic 5 - Asset Lifecycle Management:**
- FR5: Delete files from their designated storage area (soft delete to trash)
- FR6: Restore deleted files from trash within retention period
- FR7: Maintain version history when files are updated
- FR8: View version information for assets (version number, date)
- FR10: Organize files within their storage area using folder/prefix structures
- FR11: View asset metadata (owner, type, size, mime_type, upload date, checksum)
- FR30: Support trash storage area for soft-deleted files

**Epic 6 - Asset Discovery & Search:**
- FR41: Search assets by metadata fields (name, type, owner, date)
- FR42: Filter asset lists by asset type (book, video, image, material)
- FR43: View asset library with visual previews for supported formats
- FR44: Publishers can browse their complete asset collection organized by folders
- FR45: Teachers can browse publisher content assigned to them
- FR46: Students can browse teacher materials assigned to them

**Epic 7 - Integration API & External Application Support:**
- FR31: Developers can integrate applications using RESTful API endpoints
- FR32: Provide clear API error responses for debugging
- FR33: Authenticate API requests using JWT tokens
- FR34: Return asset metadata via API queries
- FR35: Support multipart upload for large files
- FR36: Provide API documentation for integration teams
- FR37: LMS can assign publisher books to teachers via API
- FR38: LMS can assign teacher materials to students via API
- FR39: Applications can download config.json files for FlowBook integration
- FR40: Support API versioning for multiple application versions

**Epic 8 - Audit, Compliance & Security Hardening:**
- FR53: Log all user actions with user_id, asset_id, action, IP address, and timestamp
- FR54: Maintain immutable audit logs that cannot be modified or deleted
- FR55: Admins can generate access reports for compliance reviews
- FR56: Support configurable data retention policies
- FR57: Retain files indefinitely until user deletion (default policy)
- FR58: Permanently delete files after configurable trash retention period
- FR59: Purge or anonymize user data when user is deleted
- FR60: Track file integrity using checksums

**Epic 9 - Admin & User Frontend Interfaces:**
- UX Requirement: shadcn/ui component library with Tailwind CSS
- UX Requirement: Functional Minimalism design direction
- UX Requirement: Responsive design (mobile, tablet, desktop, wide breakpoints)
- UX Requirement: WCAG 2.1 Level AA accessibility guidelines
- UX Requirement: Custom components (Upload Zone, Video Player, Asset Card, Progress Tracker, Browser Table, Doc Viewer)
- UX Requirement: Consistency patterns (toast notifications, button hierarchy, loading states, modals, search/filtering)

**Note:** FR65 (storage quotas per tenant) is marked as future capability and not included in initial epic breakdown.

## Epic List

### Epic 1: Platform Foundation & Infrastructure Setup

**Goal:** Developers have a running, production-ready platform to start integrating with

Developers can access a fully operational Dream Central Storage platform with all infrastructure components properly configured (FastAPI backend, React frontend, PostgreSQL, MinIO, Traefik). The system includes health monitoring, operational metrics, and is ready for integration and deployment.

**FRs covered:** Architecture requirement (FastAPI template initialization), FR61, FR62, FR63, FR64, FR66, FR67

---

### Epic 2: Authentication & Multi-Tenant Access Control

**Goal:** All user types (Admin, Supervisor, Publisher, School, Teacher, Student) can securely authenticate and access only their designated storage areas

Users can log in securely with JWT authentication and trust that their data is completely isolated from other tenants. The system enforces role-based access control where users can only write to their own storage areas, while read access is managed through LMS-driven permission grants.

**FRs covered:** FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR22, FR23, FR24, FR25, FR26, FR27, FR28, FR29

---

### Epic 3: Core Asset Upload & Storage

**Goal:** Users can upload digital assets (single files and ZIP archives) to their storage areas with confidence

Users can upload single files with progress tracking or bulk upload via ZIP archives with streaming extraction. The system automatically filters unwanted system files, validates file types and sizes, and provides direct MinIO access via time-limited signed URLs without proxying through the API layer.

**FRs covered:** FR1, FR2, FR3, FR9, FR21, FR49, FR51

---

### Epic 4: Asset Download & Streaming

**Goal:** Users can download files and stream video/audio content smoothly

Users can download files they have access to and stream video/audio content with full seek capability using HTTP Range requests. Media can be previewed before downloading, and multiple files can be downloaded in batches for efficient workflows.

**FRs covered:** FR4, FR47, FR48, FR50, FR52

---

### Epic 5: Asset Lifecycle Management

**Goal:** Users can manage the complete lifecycle of their assets including versioning, deletion, and recovery

Users can soft delete files to trash and restore them within the retention period. The system maintains version history when files are updated, allows folder-based organization, and provides comprehensive metadata views for all assets.

**FRs covered:** FR5, FR6, FR7, FR8, FR10, FR11, FR30

---

### Epic 6: Asset Discovery & Search

**Goal:** Users can efficiently find and browse assets using search and filtering

Users can search assets by metadata fields, filter by asset type, and browse asset libraries with visual previews. Publishers, teachers, and students have tailored browsing experiences showing only content they're authorized to access.

**FRs covered:** FR41, FR42, FR43, FR44, FR45, FR46

---

### Epic 7: Integration API & External Application Support

**Goal:** Developers can integrate external applications (LMS, FlowBook, Kanban) seamlessly with comprehensive API support

Developers have access to a RESTful API with comprehensive documentation, supporting multipart uploads for large files, LMS assignment workflows, and config.json downloads for FlowBook integration. The API supports versioning to accommodate multiple client application versions simultaneously.

**FRs covered:** FR31, FR32, FR33, FR34, FR35, FR36, FR37, FR38, FR39, FR40

---

### Epic 8: Audit, Compliance & Security Hardening

**Goal:** Admins can ensure regulatory compliance (COPPA/FERPA) and track all system activity through comprehensive audit logs

Admins can review immutable audit logs for all user actions, generate compliance reports, configure data retention policies, and manage user data purging. The system tracks file integrity via checksums and maintains complete accountability for educational content handling.

**FRs covered:** FR53, FR54, FR55, FR56, FR57, FR58, FR59, FR60

---

### Epic 9: Admin & User Frontend Interfaces

**Goal:** All user types have intuitive, role-based web interfaces for managing their digital assets

All users (Publishers, Teachers, Students, Admins) have access to role-specific dashboards with drag-and-drop file uploads, asset browsers with visual previews, and responsive interfaces that work across desktop, tablet, and mobile devices. The interface follows Functional Minimalism design direction and WCAG 2.1 Level AA accessibility guidelines.

**Additional Requirements covered:** All UX Design requirements including shadcn/ui component library, custom components, responsive design, accessibility standards, and UX consistency patterns

---

## Epic 1: Platform Foundation & Infrastructure Setup

**Goal:** Developers have a running, production-ready platform to start integrating with

### Story 1.1: Initialize Project from FastAPI Full Stack Template

As a developer,
I want to initialize the project from the Official FastAPI Full Stack Template,
So that I have a production-ready foundation with all necessary tooling configured.

**Acceptance Criteria:**

**Given** I have Python, Node.js, and Docker installed on my development machine
**When** I run the copier command with the FastAPI full-stack template
**Then** the project structure is generated with backend/ and frontend/ directories
**And** the configuration includes project_name="Dream Central Storage" and stack_name="dream-central-storage"
**And** Docker Compose files are present with service definitions for backend, frontend, and PostgreSQL
**And** the project includes pre-commit hooks configured with ruff and prettier
**And** environment configuration files (.env.example) are present with all required variables
**And** I can run `docker-compose up` and see all services starting without errors

### Story 1.2: Configure Docker Compose with MinIO and Traefik Services

As a developer,
I want MinIO and Traefik services added to the Docker Compose configuration,
So that object storage and reverse proxy infrastructure are available for the platform.

**Acceptance Criteria:**

**Given** the project has been initialized from the FastAPI template
**When** I add MinIO and Traefik service definitions to docker-compose.yml
**Then** the MinIO service is configured with single-bucket setup and environment variables
**And** MinIO is accessible on port 9000 with management console on port 9001
**And** Traefik is configured as reverse proxy routing /api/* to backend and /* to frontend
**And** Traefik is configured for automatic HTTPS with Let's Encrypt (production ready)
**And** All services (backend, frontend, PostgreSQL, MinIO, Traefik) start successfully with `docker-compose up`
**And** I can access MinIO console and create the initial "assets" bucket
**And** MinIO versioning is enabled on the assets bucket for soft delete support (FR7)

### Story 1.3: Set Up Core Database Models and Migrations Framework

As a developer,
I want the core database schema with multi-tenant tables and Alembic migrations configured,
So that I have a foundation for storing asset metadata with proper tenant isolation.

**Acceptance Criteria:**

**Given** PostgreSQL is running via Docker Compose
**When** I create SQLModel models for users, tenants, assets, and audit_logs tables
**Then** the User model includes id, email, hashed_password, role (enum: Admin/Supervisor/Publisher/School/Teacher/Student), tenant_id, created_at, updated_at
**And** the Tenant model includes id, name, tenant_type, created_at
**And** the Asset model includes id, user_id, tenant_id, bucket, object_key, file_name, file_size_bytes, mime_type, checksum, is_deleted, created_at, updated_at
**And** the AuditLog model includes id, user_id, action, asset_id, ip_address, timestamp, metadata_json
**And** All tables have proper indexes on tenant_id, user_id, and created_at columns (NFR-SC9)
**And** Alembic migration files are generated and can be applied with `alembic upgrade head`
**And** Database constraints enforce referential integrity (foreign keys, not null, unique)
**And** Row-level security foundation is prepared for multi-tenant isolation (FR27, FR28)

### Story 1.4: Implement Health Check and System Status Endpoints

As a developer,
I want health check endpoints that verify all system components are operational,
So that monitoring tools can detect issues and ensure platform availability (FR61, NFR-M1).

**Acceptance Criteria:**

**Given** the backend API is running
**When** I send a GET request to `/health`
**Then** I receive a 200 OK response with JSON: `{"status": "healthy", "database": "ok", "minio": "ok", "timestamp": "ISO-8601"}`
**And** the endpoint checks PostgreSQL connectivity by executing a simple query
**And** the endpoint checks MinIO connectivity by listing buckets
**And** if PostgreSQL is unavailable, the response is 503 with `{"status": "unhealthy", "database": "error", "minio": "ok"}`
**And** if MinIO is unavailable, the response is 503 with `{"status": "unhealthy", "database": "ok", "minio": "error"}`
**And** the endpoint responds within 100ms under normal conditions (NFR-P1)
**And** Traefik uses this endpoint for service health checks

### Story 1.5: Configure Monitoring, Logging, and Metrics Exposure

As a developer,
I want structured logging with request tracing and MinIO metrics exposed,
So that I can monitor system health and troubleshoot issues effectively (FR62, NFR-M2, NFR-M3, NFR-M4).

**Acceptance Criteria:**

**Given** the platform is running
**When** API requests are processed
**Then** all logs are written in structured JSON format with fields: timestamp, level, request_id (UUID v4), user_id, message, context
**And** request_id is generated by middleware for every API request and included in all log entries
**And** request_id is included in API error responses for debugging (NFR-M8)
**And** MinIO Prometheus metrics endpoint is accessible at `:9000/minio/v2/metrics/cluster`
**And** MinIO metrics include storage usage, request rates, and error rates
**And** critical errors are logged with sufficient context including stack traces (NFR-M4)
**And** log levels can be configured via environment variables (INFO for production, DEBUG for development)

### Story 1.6: Set Up CI/CD Pipeline with GitHub Actions

As a developer,
I want automated CI/CD pipeline that tests, builds, and deploys the application,
So that code quality is maintained and deployments are reliable (NFR-M5).

**Acceptance Criteria:**

**Given** code is pushed to the GitHub repository
**When** a pull request is created
**Then** GitHub Actions workflow runs backend tests with pytest and frontend tests with Vitest
**And** test coverage reports are generated (pytest-cov for backend, minimum 80% coverage target)
**And** linting checks pass for Python (ruff) and TypeScript (eslint, prettier)
**And** the PR cannot be merged if tests fail or coverage drops below threshold
**When** code is merged to main branch
**Then** Docker images are built for backend and frontend using multi-stage builds
**And** images are tagged with git commit SHA and pushed to GitHub Container Registry
**And** deployment workflow can SSH to VPS, pull new images, and perform blue-green deployment
**And** database migrations are applied before container swap (NFR-M6)
**And** zero-downtime deployment is achieved using Traefik routing updates (NFR-M5)

### Story 1.7: Configure HTTPS, Security Headers, and Encryption

As a developer,
I want HTTPS configured with automatic certificate management and encryption at rest enabled,
So that all communications are secure and compliance requirements are met (FR67, NFR-S5, NFR-S6).

**Acceptance Criteria:**

**Given** Traefik is configured as reverse proxy
**When** the platform is accessed via HTTPS
**Then** Traefik obtains Let's Encrypt certificates automatically for the configured domain
**And** HTTP requests are automatically redirected to HTTPS
**And** TLS 1.3 is used for all encrypted communications (NFR-S5)
**And** security headers are added to responses: X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security
**When** MinIO is configured for encryption
**Then** server-side encryption (SSE-S3 mode with AES-256) is enabled on the assets bucket (NFR-S6, FR66)
**And** all new objects uploaded to MinIO are encrypted at rest
**And** sensitive credentials (DB password, MinIO keys, JWT secret) are never logged or exposed in errors (NFR-S7)
**And** environment variables are used for all secrets, not hardcoded values

---

## Epic 2: Authentication & Multi-Tenant Access Control

**Goal:** All user types can securely authenticate and access only their designated storage areas

### Story 2.1: Implement JWT Authentication with Login and Token Generation

As a user,
I want to log in with my credentials and receive a JWT token,
So that I can securely access the platform (FR12, NFR-S1, NFR-S2).

**Acceptance Criteria:**

**Given** I am a registered user with email and password
**When** I send a POST request to `/api/v1/auth/login` with valid credentials
**Then** I receive a 200 OK response with access_token and refresh_token
**And** the access token is a JWT signed with RS256 algorithm and expires in 30 minutes (NFR-S2)
**And** the refresh token expires in 7 days
**And** the JWT payload includes user_id, email, role, and tenant_id claims
**And** passwords are hashed with bcrypt before storage (never stored as plaintext)
**When** I provide invalid credentials
**Then** I receive 401 Unauthorized with error message "Invalid credentials"
**And** the system rate limits login attempts to prevent brute force (5 attempts per minute per IP)

### Story 2.2: Implement Role-Based Authorization Middleware

As a developer,
I want role-based authorization enforced on all API endpoints,
So that users can only access resources based on their role (FR22, NFR-S3).

**Acceptance Criteria:**

**Given** a user is authenticated with a valid JWT
**When** they access an API endpoint
**Then** the authorization middleware extracts role and tenant_id from the JWT
**And** role-based access control is enforced: Admins/Supervisors can access all tenants (FR13, FR14)
**And** Publishers can only write to `/publishers/{their_id}/` storage (FR15)
**And** Schools can only write to `/schools/{their_id}/` storage (FR16)
**And** Teachers can only write to `/teachers/{their_id}/` storage (FR17)
**And** Students can only write to `/students/{their_id}/` storage (FR18)
**When** a user attempts to access a resource they're not authorized for
**Then** they receive 403 Forbidden with error_code "PERMISSION_DENIED"
**And** the attempt is logged in audit logs with user_id, action, resource, and timestamp

### Story 2.3: Implement Multi-Tenant Database Isolation with Row-Level Security

As a developer,
I want database queries automatically filtered by tenant_id,
So that tenant data is completely isolated (FR25, FR26, FR27, FR28, FR29).

**Acceptance Criteria:**

**Given** a user makes an API request
**When** the request handler queries the database
**Then** middleware injects current_user_id and tenant_id into the database session context
**And** all SQLModel queries automatically include tenant_id filters on tenant-specific tables
**And** the Asset model queries always filter by tenant_id matching the authenticated user's tenant
**And** Admins and Supervisors bypass tenant_id filtering to access all tenants (FR13, FR14)
**And** cross-tenant write access is prevented at both API and database layers (FR29)
**When** a query attempts to access another tenant's data
**Then** the query returns zero results (data is invisible to the requester)
**And** PostgreSQL row-level security policies are created as a backstop defense layer
**And** database indexes on owner_type and owner_id enable fast tenant isolation queries (NFR-SC9)

### Story 2.4: Implement Rate Limiting per User Role

As a developer,
I want API rate limiting applied based on user role,
So that abuse is prevented and resources are fairly allocated (FR24, NFR-S10).

**Acceptance Criteria:**

**Given** a user is making API requests
**When** rate limiting is evaluated
**Then** Publishers are limited to 1000 requests per hour (bulk upload workflows)
**And** Teachers are limited to 500 requests per hour (classroom operations)
**And** Students are limited to 100 requests per hour (individual browsing)
**And** Admins and Supervisors have unlimited API access
**And** rate limits are tracked using token bucket algorithm per user_id + role combination
**And** rate limits are enforced in-memory using slowapi library (future: Redis for distributed)
**When** a user exceeds their rate limit
**Then** they receive 429 Too Many Requests with error_code "RATE_LIMIT_EXCEEDED"
**And** the response includes Retry-After header indicating when they can retry
**And** rate limit violations are logged for abuse detection

### Story 2.5: Implement User Management Endpoints for Admin/Supervisor

As an admin,
I want to create, update, and manage user accounts for all roles,
So that I can onboard publishers, schools, teachers, and students to the platform.

**Acceptance Criteria:**

**Given** I am authenticated as Admin or Supervisor
**When** I send POST `/api/v1/users` with user data (email, password, role, tenant_id)
**Then** a new user account is created with hashed password and assigned role
**And** the tenant_id is validated to ensure it exists in the tenants table
**And** the user receives a 201 Created response with user details (excluding password)
**When** I send GET `/api/v1/users/{user_id}`
**Then** I receive user details including role, tenant_id, created_at
**When** I send PATCH `/api/v1/users/{user_id}` to update role or deactivate account
**Then** the user record is updated and changes are logged in audit_logs
**When** I send GET `/api/v1/users?role=publisher&page=1&page_size=50`
**Then** I receive a paginated list of users filtered by role (NFR-P1: <500ms)
**And** non-admin users attempting these endpoints receive 403 Forbidden

---

## Epic 3: Core Asset Upload & Storage

**Goal:** Users can upload digital assets to their storage areas with confidence

### Story 3.1: Implement Single File Upload with Progress Tracking

As a user,
I want to upload a single file to my storage area with progress feedback,
So that I can store my digital assets (FR1).

**Acceptance Criteria:**

**Given** I am authenticated and have write access to my storage area
**When** I send POST `/api/v1/assets/upload` with file data
**Then** the API validates file type and size before accepting (FR9: max 10GB per NFR-P3)
**And** allowed MIME types are validated against a configurable whitelist
**And** the file is uploaded directly to MinIO bucket with path `/{tenant_type}/{tenant_id}/{file_name}`
**And** asset metadata is created in PostgreSQL: user_id, tenant_id, bucket, object_key, file_name, file_size_bytes, mime_type, checksum, created_at
**And** checksum (MD5) is calculated and stored for integrity verification (FR60, NFR-R5)
**And** I receive 201 Created with asset metadata including asset_id and upload confirmation
**And** the upload does not buffer the entire file in memory (streaming design, NFR-P7)
**When** upload completes
**Then** an audit log entry is created with action="upload", user_id, asset_id, timestamp (FR53)
**And** the file is immediately accessible via download API

### Story 3.2: Generate Time-Limited Signed URLs for Direct MinIO Access

As a developer,
I want the API to generate signed URLs for direct MinIO access,
So that files are not proxied through the API layer (FR21, FR49, NFR-P2, NFR-P7).

**Acceptance Criteria:**

**Given** a user requests access to an asset they're authorized for
**When** I call the signed URL generation service
**Then** the backend generates a presigned URL using MinIO SDK with HMAC-SHA256 signature
**And** signed URLs for uploads have 15-minute TTL (short-lived for security)
**And** signed URLs for downloads have 1-hour TTL (classroom viewing duration)
**And** the signed URL generation completes within 100ms (NFR-P2)
**And** clients use the signed URL to upload/download directly to/from MinIO without API proxying
**And** API CPU and RAM usage remains minimal as files bypass the API layer (FR51, NFR-P5, NFR-P6)
**When** a signed URL expires
**Then** MinIO rejects the request and the client must request a new signed URL

### Story 3.3: Implement ZIP Archive Upload with Streaming Extraction

As a publisher,
I want to upload a ZIP archive and have it automatically extracted,
So that I can bulk upload hundreds of assets efficiently (FR2, FR3, NFR-P9).

**Acceptance Criteria:**

**Given** I am authenticated as a Publisher
**When** I send POST `/api/v1/assets/upload-zip` with a ZIP file
**Then** the API validates the ZIP file size (max 10GB)
**And** the ZIP file is streamed and extracted without loading the entire file into memory (NFR-P9)
**And** system files are automatically filtered: .DS_Store, __MACOSX/, Thumbs.db, .git/, desktop.ini (FR3)
**And** each extracted file is validated for type and size
**And** each valid file is uploaded to MinIO at `/{tenant_type}/{tenant_id}/{folder_structure}/{file_name}`
**And** folder structure from the ZIP is preserved as MinIO prefixes (FR10)
**And** asset metadata records are created for each extracted file
**And** the extraction does not require disk buffering (streaming mode, NFR-P9)
**When** extraction completes
**Then** I receive a response with count of files extracted, count of files skipped, and list of all created assets
**And** all upload operations are logged in audit logs
**And** if any file fails validation, it's skipped and reported but extraction continues

### Story 3.4: Implement File Type and Size Validation

As a system,
I want to validate all uploaded files for type and size,
So that malicious or inappropriate files are rejected (FR9).

**Acceptance Criteria:**

**Given** a file is being uploaded
**When** the upload API receives the file
**Then** the file MIME type is extracted from the Content-Type header and file extension
**And** allowed MIME types include: application/pdf, video/mp4, video/webm, audio/mp3, audio/wav, image/jpeg, image/png, image/gif, application/zip, application/json
**And** if MIME type is not in the allowed list, upload is rejected with 400 Bad Request and error_code "INVALID_FILE_TYPE"
**And** file size is checked: max 10GB for videos, max 500MB for images, max 5GB for ZIPs
**And** if file size exceeds limits, upload is rejected with 400 Bad Request and error_code "FILE_TOO_LARGE"
**And** validation errors include helpful messages: "File type 'application/exe' is not allowed. Supported types: pdf, mp4, mp3, jpg, png, zip"

---

## Epic 4: Asset Download & Streaming

**Goal:** Users can download files and stream video/audio content smoothly

### Story 4.1: Implement Asset Download with Signed URLs

As a user,
I want to download assets I have access to,
So that I can use them offline (FR4).

**Acceptance Criteria:**

**Given** I am authenticated and have read access to an asset
**When** I send GET `/api/v1/assets/{asset_id}/download`
**Then** the API validates I have permission to access the asset (FR22, FR23)
**And** the API generates a presigned download URL from MinIO with 1-hour TTL
**And** I receive a 200 OK response with `{"download_url": "https://minio.../presigned-url", "expires_at": "ISO-8601"}`
**And** the download URL allows direct access to MinIO without API proxying (FR49)
**And** an audit log entry is created with action="download", user_id, asset_id (FR53)
**When** I use the presigned URL
**Then** the file downloads directly from MinIO
**And** the download supports HTTP Range requests for partial downloads (resume capability)

### Story 4.2: Implement Video and Audio Streaming with HTTP Range Support

As a student,
I want to stream video and audio files with seek capability,
So that I can watch course materials without downloading entire files (FR47, FR48, NFR-P4).

**Acceptance Criteria:**

**Given** I am authenticated and have access to a video or audio asset
**When** I send GET `/api/v1/assets/{asset_id}/stream`
**Then** the API validates permissions and generates a presigned MinIO URL
**And** I receive a stream URL that supports HTTP Range requests
**When** my video player sends Range requests (e.g., "Range: bytes=1000-2000")
**Then** MinIO responds with 206 Partial Content and the requested byte range
**And** video seeking works smoothly without buffering the entire file
**And** audio playback supports scrubbing through the timeline
**And** the streaming URL remains valid for 1 hour (re-request if longer viewing)
**And** streaming performance has minimal latency for seeking (NFR-P4)
**And** API server CPU/RAM usage is minimal as streaming is direct to MinIO (FR51)

### Story 4.3: Implement Asset Preview Endpoints

As a user,
I want to preview images, videos, and audio before downloading,
So that I can verify it's the correct file (FR50).

**Acceptance Criteria:**

**Given** I am viewing an asset in the web interface
**When** I request a preview for an image asset
**Then** the API returns a signed URL to the image in MinIO
**And** the image is displayed inline in the browser
**When** I request a preview for a video asset
**Then** the API returns a signed stream URL with HTTP Range support
**And** a video player component loads the stream URL and displays the first frame as thumbnail
**When** I request a preview for an audio asset
**Then** the API returns a signed stream URL
**And** an audio player component allows playing the audio inline
**When** I request a preview for a PDF
**Then** the API returns a signed URL and the PDF renders in an iframe or PDF viewer component
**And** preview URLs have 1-hour TTL and are regenerated as needed

### Story 4.4: Implement Batch Download for Multiple Assets

As a teacher,
I want to download multiple assets at once,
So that I can efficiently retrieve all materials for a lesson (FR52).

**Acceptance Criteria:**

**Given** I am authenticated and have access to multiple assets
**When** I send POST `/api/v1/assets/batch-download` with a list of asset_ids
**Then** the API validates I have permission for all requested assets
**And** the API generates a temporary ZIP archive containing all requested files
**And** the ZIP generation uses streaming (no full buffering in memory)
**And** I receive a download URL for the generated ZIP file
**And** the ZIP file is stored temporarily in MinIO (trash bucket or temp prefix) with 1-hour expiry
**And** the batch download request is logged in audit logs
**When** I access the download URL
**Then** the ZIP file downloads directly from MinIO
**And** after 1 hour, the temporary ZIP is automatically deleted

---

## Epic 5: Asset Lifecycle Management

**Goal:** Users can manage asset lifecycle including versioning, deletion, and recovery

### Story 5.1: Implement Soft Delete to Trash

As a user,
I want to delete assets which moves them to trash,
So that I can recover them if deleted accidentally (FR5, FR30).

**Acceptance Criteria:**

**Given** I own an asset in my storage area
**When** I send DELETE `/api/v1/assets/{asset_id}`
**Then** the asset is NOT permanently deleted
**And** the asset metadata record is updated: is_deleted=true, deleted_at=current_timestamp
**And** the MinIO object is moved from its current location to `/trash/{tenant_id}/{asset_id}/{file_name}`
**And** the asset is no longer visible in regular asset listing endpoints
**And** the asset is visible in the trash endpoint: GET `/api/v1/trash`
**And** an audit log entry is created with action="soft_delete", user_id, asset_id (FR53)
**When** I query my assets via GET `/api/v1/assets`
**Then** soft-deleted assets are excluded from results (is_deleted=false filter)

### Story 5.2: Implement Restore from Trash

As a user,
I want to restore assets from trash,
So that I can recover accidentally deleted files (FR6).

**Acceptance Criteria:**

**Given** I have a soft-deleted asset in trash
**When** I send POST `/api/v1/trash/{asset_id}/restore`
**Then** the asset metadata is updated: is_deleted=false, deleted_at=null, restored_at=current_timestamp
**And** the MinIO object is moved from `/trash/{tenant_id}/{asset_id}/` back to its original location
**And** the asset becomes visible again in regular asset listings
**And** the asset retains all original metadata (file_name, mime_type, checksum, created_at)
**And** an audit log entry is created with action="restore", user_id, asset_id (FR53)
**When** I attempt to restore an asset that's past the retention period
**Then** I receive 410 Gone with error_code "ASSET_PERMANENTLY_DELETED"

### Story 5.3: Implement Asset Versioning on Updates

As a user,
I want file versions tracked when I upload a new version,
So that I can review version history and revert if needed (FR7, FR8).

**Acceptance Criteria:**

**Given** an asset exists in my storage
**When** I upload a new file with the same name to the same location
**Then** MinIO versioning preserves the previous version (versioning enabled in Story 1.2)
**And** a new asset_versions table record is created: asset_id, version_number, object_version_id, file_size_bytes, checksum, created_at
**And** the asset metadata is updated with new file_size_bytes and checksum
**And** the current version number is incremented
**And** previous versions remain accessible via MinIO version IDs
**When** I send GET `/api/v1/assets/{asset_id}/versions`
**Then** I receive a list of all versions with version_number, created_at, file_size_bytes
**And** each version includes a download URL for accessing that specific version
**And** version history is maintained indefinitely (or per configured retention policy)

### Story 5.4: Implement Folder Organization with Prefix Structure

As a publisher,
I want to organize my assets into folders,
So that I can manage large asset collections efficiently (FR10).

**Acceptance Criteria:**

**Given** I am uploading assets
**When** I specify a folder path in the upload request (e.g., "books/grade-8/math")
**Then** the asset is stored in MinIO with prefix: `/publishers/{publisher_id}/books/grade-8/math/{file_name}`
**And** the asset metadata includes a "folder_path" field: "books/grade-8/math"
**When** I send GET `/api/v1/assets?folder=books/grade-8/math`
**Then** I receive only assets within that folder prefix
**When** I send GET `/api/v1/assets/folders`
**Then** I receive a hierarchical list of all folder paths in my storage area
**And** folder listing includes asset count per folder
**And** empty folders are not shown (folders are logical prefixes, not physical entities)

### Story 5.5: Implement Asset Metadata Display

As a user,
I want to view comprehensive metadata for any asset,
So that I can verify file details and integrity (FR11).

**Acceptance Criteria:**

**Given** I have access to an asset
**When** I send GET `/api/v1/assets/{asset_id}`
**Then** I receive complete metadata: asset_id, file_name, file_size_bytes, mime_type, checksum (MD5), owner_id, owner_type, tenant_id, created_at, updated_at, folder_path, version_number
**And** the response includes human-readable file size (e.g., "1.5 MB" formatted on frontend)
**And** the response includes upload date formatted in user's timezone
**And** if the asset has versions, version count is included
**And** if the asset is in trash, deleted_at timestamp is included
**And** metadata query response time is <500ms (NFR-P1)

---

## Epic 6: Asset Discovery & Search

**Goal:** Users can efficiently find and browse assets using search and filtering

### Story 6.1: Implement Asset Search by Metadata Fields

As a user,
I want to search assets by name, type, and date,
So that I can quickly find specific files (FR41).

**Acceptance Criteria:**

**Given** I have assets in my storage area
**When** I send GET `/api/v1/assets/search?q=math&type=pdf&date_from=2025-01-01`
**Then** the API searches asset file_name, mime_type, and created_at fields
**And** search is case-insensitive on file_name
**And** results are filtered by owner permissions (I only see assets I'm authorized for)
**And** results are paginated with page and page_size parameters
**And** response includes total count, page, page_size, and items array
**And** search queries use database indexes for performance (NFR-P1: <500ms)
**When** I provide a search query "q=mathematics textbook"
**Then** PostgreSQL full-text search is used to match words in file_name
**And** results are ranked by relevance

### Story 6.2: Implement Asset Filtering by Type and Owner

As a user,
I want to filter asset lists by type (book, video, image, material),
So that I can browse specific content categories (FR42).

**Acceptance Criteria:**

**Given** I am viewing my asset library
**When** I send GET `/api/v1/assets?asset_type=video&page=1&page_size=50`
**Then** results are filtered by mime_type: video/* types
**And** asset_type can be: all, book (pdf), video (mp4/webm), audio (mp3/wav), image (jpg/png/gif), document (pdf/json)
**And** the response is paginated with total count
**When** I send GET `/api/v1/assets?owner_type=publisher&owner_id=123`
**Then** results are filtered to show assets from that specific publisher (if I have permission)
**And** Admins can filter by any owner_type and owner_id
**And** Non-admins can only filter within their authorized access scope

### Story 6.3: Implement Asset Library with Visual Previews

As a user,
I want to view an asset library with thumbnails and previews,
So that I can visually identify files (FR43).

**Acceptance Criteria:**

**Given** I am viewing the asset library web interface
**When** the library loads asset listings
**Then** each image asset displays a thumbnail (generated by MinIO or direct presigned URL)
**And** each video asset displays a video thumbnail/poster frame
**And** each PDF displays a generic PDF icon
**And** each audio file displays a generic audio icon
**And** thumbnails are lazy-loaded as I scroll (virtual scrolling for lists >100 items per NFR)
**When** I hover over or click an asset
**Then** a preview modal opens showing the asset preview (image, video player, audio player, or PDF viewer)
**And** preview uses the signed URL from Story 4.3

### Story 6.4: Implement Role-Specific Asset Browsing

As a publisher/teacher/student,
I want to browse only the assets I'm authorized to access,
So that I see a personalized view (FR44, FR45, FR46).

**Acceptance Criteria:**

**Given** I am authenticated as a Publisher
**When** I access the asset library
**Then** I see only assets in `/publishers/{my_id}/` storage area (FR44)
**And** the UI shows folder organization for my complete asset collection
**Given** I am authenticated as a Teacher
**When** I access the asset library
**Then** I see assets from `/teachers/{my_id}/` (my own uploads)
**And** I also see publisher content that the LMS has granted me access to (FR45)
**And** assets are visually distinguished: "My Materials" vs "Publisher Resources"
**Given** I am authenticated as a Student
**When** I access the asset library
**Then** I see assets from `/students/{my_id}/` (my submissions)
**And** I see teacher materials that have been assigned to me via LMS (FR46)
**And** I cannot see other students' files or unassigned materials

---

## Epic 7: Integration API & External Application Support

**Goal:** Developers can integrate external applications seamlessly

### Story 7.1: Implement RESTful API with Standardized Error Responses

As a developer,
I want clear, consistent API error responses,
So that I can debug integration issues quickly (FR31, FR32, NFR-M10).

**Acceptance Criteria:**

**Given** an API request fails
**When** the API returns an error response
**Then** the response follows standardized format: `{"error_code": "ASSET_NOT_FOUND", "message": "Asset with ID 12345 does not exist or you lack permission", "details": {"asset_id": 12345}, "request_id": "uuid", "timestamp": "ISO-8601"}`
**And** error_code is a machine-readable enum (ASSET_NOT_FOUND, PERMISSION_DENIED, VALIDATION_ERROR, RATE_LIMIT_EXCEEDED, etc.)
**And** message is human-readable and actionable
**And** details object provides context-specific information
**And** request_id allows tracing the error in logs
**And** HTTP status codes are semantically correct: 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (validation), 429 (rate limit), 500 (server error)
**And** validation errors include field-level details: `{"error_code": "VALIDATION_ERROR", "details": {"email": "Invalid email format", "file_size": "File exceeds 10GB limit"}}`

### Story 7.2: Implement Multipart Upload for Large Files

As a developer,
I want to upload large files using multipart upload,
So that uploads can resume and progress reliably (FR35).

**Acceptance Criteria:**

**Given** I need to upload a file >100MB
**When** I initiate multipart upload via POST `/api/v1/assets/multipart/init`
**Then** I receive an upload_id and a list of presigned URLs for each part (10MB chunks)
**When** I upload each part to its presigned URL
**Then** MinIO stores each part with an ETag
**When** all parts are uploaded, I send POST `/api/v1/assets/multipart/complete` with upload_id and ETags
**Then** the backend validates all ETags via MinIO
**And** MinIO combines all parts into the final object
**And** asset metadata is created in PostgreSQL with complete file details
**And** an audit log entry is created for the upload
**When** upload fails midway
**Then** I can resume by uploading only the missing parts (ETags track completed parts)

### Story 7.3: Implement LMS Assignment Permission API

As an LMS application,
I want to manage asset permissions via API,
So that teachers and students can access assigned materials (FR37, FR38).

**Acceptance Criteria:**

**Given** LMS is authenticated with a service account
**When** LMS sends POST `/api/v1/permissions` with `{"asset_id": "123", "user_id": "456", "permission": "read", "expires_at": "2025-12-31"}`
**Then** an asset_permissions table record is created granting the user read access
**And** the permission can have an expiration date (optional)
**When** the teacher or student queries their assets
**Then** they see the granted asset in their library
**And** they can download or stream the asset using signed URLs
**When** LMS sends DELETE `/api/v1/permissions/{permission_id}`
**Then** the permission is revoked and the user loses access to the asset
**When** LMS sends GET `/api/v1/permissions?user_id=456`
**Then** all permissions for that user are returned (for auditing)

### Story 7.4: Implement Config.json Download for FlowBook Integration

As a FlowBook application,
I want to download config.json files for books,
So that offline book readers can access book configuration (FR39).

**Acceptance Criteria:**

**Given** a book asset exists in DCS with an associated config.json
**When** FlowBook sends GET `/api/v1/assets/{asset_id}/config.json`
**Then** the API validates FlowBook has permission to access the asset
**And** the API returns the config.json file content directly
**And** the config.json includes asset metadata, file URLs, and book structure
**When** the config.json references additional assets (images, videos)
**Then** signed URLs with 24-hour TTL are embedded in the config.json
**And** FlowBook can download all referenced assets for offline use

### Story 7.5: Implement API Versioning

As a developer,
I want API versioning support,
So that multiple client versions can coexist during updates (FR40, NFR-M7).

**Acceptance Criteria:**

**Given** the API has multiple versions
**When** clients make requests
**Then** all endpoints are prefixed with version: `/api/v1/assets`, `/api/v1/users`
**And** breaking changes require a new version: `/api/v2/assets`
**And** v1 remains available during v2 rollout (maintain v1 for 6 months minimum)
**When** a client uses an deprecated API version
**Then** responses include a deprecation warning header: `X-API-Deprecation: v1 will be sunset on 2026-06-01`
**And** API documentation clearly indicates which version endpoints belong to

### Story 7.6: Implement Comprehensive API Documentation

As a developer,
I want comprehensive, up-to-date API documentation,
So that I can integrate applications without guessing (FR36, NFR-M8, NFR-M9).

**Acceptance Criteria:**

**Given** the FastAPI application is running
**When** I access `/docs`
**Then** I see automatic OpenAPI/Swagger documentation for all endpoints
**And** each endpoint includes description, parameters, request body schema, response schema, and example responses
**And** authentication requirements are documented (JWT token in Authorization header)
**And** error codes and their meanings are documented
**When** I access `/redoc`
**Then** I see alternative ReDoc documentation with better readability
**And** code examples are provided for curl, Python, and JavaScript
**And** the documentation is automatically updated when API changes (OpenAPI generation)

---

## Epic 8: Audit, Compliance & Security Hardening

**Goal:** Admins can ensure regulatory compliance and track all system activity

### Story 8.1: Implement Immutable Audit Logging for All Actions

As a system,
I want all user actions logged immutably,
So that compliance and security investigations are possible (FR53, FR54, NFR-S12).

**Acceptance Criteria:**

**Given** a user performs any action (upload, download, delete, restore, permission change)
**When** the action completes
**Then** an audit log entry is created in the audit_logs table with: id, user_id, action (enum), asset_id, ip_address, timestamp, metadata_json
**And** the audit_logs table has no UPDATE or DELETE permissions (append-only, immutable)
**And** metadata_json captures additional context (e.g., file_name, file_size, requester role)
**And** all logs include request_id for correlation with application logs
**And** authentication events are also logged (login, logout, token refresh, failed login attempts)
**When** an admin attempts to modify or delete an audit log
**Then** the database rejects the operation (enforced by PostgreSQL permissions)

### Story 8.2: Implement Compliance Reporting and Audit Log Access

As an admin,
I want to generate access reports for compliance reviews,
So that we meet COPPA/FERPA requirements (FR55, NFR-S11).

**Acceptance Criteria:**

**Given** I am authenticated as Admin or Supervisor
**When** I send GET `/api/v1/audit-logs?user_id=123&date_from=2025-01-01&date_to=2025-12-31`
**Then** I receive all audit log entries for the specified user and date range
**And** the response is paginated for large result sets
**And** I can filter by action type: upload, download, delete, restore, permission_change
**When** I send GET `/api/v1/audit-logs/report?format=csv&date_from=2025-01-01`
**Then** I receive a CSV export of audit logs for the specified period
**And** the CSV includes all columns: timestamp, user_email, action, asset_name, ip_address
**And** the export is suitable for compliance audits (COPPA/FERPA reporting)
**When** a non-admin user attempts to access audit logs
**Then** they receive 403 Forbidden (audit logs are admin-only)

### Story 8.3: Implement Configurable Data Retention Policies

As an admin,
I want to configure data retention policies,
So that deleted files are permanently removed per compliance requirements (FR56, FR57, FR58, NFR-S13).

**Acceptance Criteria:**

**Given** retention policies are configured in settings
**When** an asset is soft-deleted (moved to trash)
**Then** the deleted_at timestamp is recorded
**And** the asset remains in trash for the configured retention period (default: 30 days)
**When** the retention period expires
**Then** a background job runs daily and identifies assets with deleted_at > retention_period
**And** the MinIO object is permanently deleted from the trash bucket
**And** the asset metadata record is either deleted or anonymized (configurable)
**And** an audit log entry is created with action="permanent_delete"
**When** files are retained indefinitely (default for non-deleted assets per FR57)
**Then** non-deleted assets are never automatically purged
**And** retention only applies to trash

### Story 8.4: Implement File Integrity Verification with Checksums

As a system,
I want to verify file integrity using checksums,
So that data corruption is detected (FR60, NFR-R4, NFR-R5).

**Acceptance Criteria:**

**Given** a file is uploaded
**When** the upload completes
**Then** an MD5 checksum is calculated for the file
**And** the checksum is stored in the asset metadata
**When** a file is downloaded
**Then** the client can optionally verify the checksum after download
**And** the API returns the expected checksum in the asset metadata response
**When** an admin runs integrity verification (background job)
**Then** the job fetches the object from MinIO, recalculates checksum, and compares to stored value
**And** if checksums mismatch, an alert is logged and admin is notified
**And** data integrity validation ensures zero data loss tolerance (NFR-R4)

### Story 8.5: Implement User Data Purging on Account Deletion

As an admin,
I want to purge or anonymize user data when accounts are deleted,
So that we comply with data privacy regulations (FR59).

**Acceptance Criteria:**

**Given** an admin deletes a user account
**When** the DELETE `/api/v1/users/{user_id}` request is processed
**Then** the admin is prompted to choose: "Delete all assets" or "Anonymize audit logs"
**When** "Delete all assets" is selected
**Then** all assets owned by the user are soft-deleted (moved to trash)
**And** after trash retention period, assets are permanently deleted
**And** audit logs remain but user_id is replaced with "deleted_user_{uuid}"
**When** "Anonymize audit logs" is selected
**Then** the user's account is marked as deleted
**And** all audit log entries have user_id replaced with "anonymized_user_{uuid}"
**And** user's assets remain but ownership is transferred to a system account or deleted
**And** the operation is logged in audit logs

---

## Epic 9: Admin & User Frontend Interfaces

**Goal:** All user types have intuitive, role-based web interfaces

### Story 9.1: Set Up React Frontend with shadcn/ui and Tailwind CSS

As a developer,
I want a React frontend configured with shadcn/ui component library,
So that I have a design system foundation for building the UI (UX requirement).

**Acceptance Criteria:**

**Given** the frontend/ directory exists from the FastAPI template
**When** I configure the frontend build
**Then** Tailwind CSS is installed and configured with design tokens
**And** shadcn/ui component library is initialized with components: Button, Dialog, Input, Table, Toast, Card
**And** the design system uses the Functional Minimalism direction (clean, professional colors)
**And** color system is configured: neutral grays for backgrounds, blue for primary actions, red for destructive
**And** typography system uses Inter font family with clear hierarchy
**And** spacing system follows 4px base unit (4, 8, 12, 16, 24, 32, 48, 64px)
**And** responsive breakpoints are configured: mobile (320px), tablet (768px), desktop (1024px), wide (1440px)
**And** Vite is configured for fast development with hot module replacement

### Story 9.2: Implement Authentication UI with Login and Role-Based Routing

As a user,
I want to log in via a web interface and see role-specific content,
So that I can access the platform features for my role.

**Acceptance Criteria:**

**Given** I visit the frontend application
**When** I am not authenticated
**Then** I am redirected to the login page at `/login`
**And** the login page displays email and password input fields (shadcn/ui Input components)
**And** clicking "Log In" sends credentials to POST `/api/v1/auth/login`
**When** login succeeds
**Then** the JWT access token is stored in localStorage
**And** I am redirected to my role-specific dashboard: `/publisher`, `/teacher`, `/student`, or `/admin`
**And** React Context provides authentication state (useAuth hook)
**When** I am authenticated
**Then** protected routes use React Router v6 ProtectedRoute wrapper
**And** navigation bar displays role-specific menu items
**And** attempting to access unauthorized routes shows 403 Forbidden page

### Story 9.3: Implement Asset Upload Zone with Drag-and-Drop

As a user,
I want to drag and drop files to upload them,
So that uploading is intuitive and fast (UX requirement: Upload Zone component).

**Acceptance Criteria:**

**Given** I am on the asset upload page
**When** the page loads
**Then** an upload zone is displayed with text "Drag files here or click to browse"
**And** the zone has a dashed border and hover state (visual feedback)
**When** I drag a file over the zone
**Then** the zone highlights with a blue border and background color change
**When** I drop a file
**Then** the file is validated client-side for type and size
**And** if valid, upload begins immediately using the upload API
**And** a progress bar displays upload percentage in real-time
**And** multiple files can be uploaded simultaneously with individual progress bars
**When** upload completes
**Then** a success toast notification appears: "File uploaded successfully"
**And** the asset appears in my asset library immediately
**When** upload fails
**Then** an error toast notification appears with the error message

### Story 9.4: Implement Asset Browser with Table View and Previews

As a user,
I want to browse my assets in a table with sorting and filtering,
So that I can manage large asset collections (UX requirement: Asset Browser Table).

**Acceptance Criteria:**

**Given** I am on the asset library page
**When** the page loads
**Then** assets are displayed in a table (shadcn/ui Table component) with columns: Thumbnail, Name, Type, Size, Uploaded Date, Actions
**And** the table supports virtual scrolling for lists >100 items (react-window)
**And** I can sort by Name, Type, Size, or Date (clicking column headers)
**And** I can filter by asset type using dropdown: All, Books, Videos, Images, Audio
**And** I can search by file name using a search input with 300ms debounce
**When** I hover over an asset row
**Then** action buttons appear: View, Download, Delete
**When** I click "View"
**Then** a modal opens displaying the asset preview (image, video player, PDF viewer)
**When** I click "Download"
**Then** the file downloads using the presigned URL from the API
**When** I click "Delete"
**Then** a confirmation dialog appears: "Are you sure you want to delete {file_name}?"
**And** confirming deletes the asset (soft delete to trash)

### Story 9.5: Implement Video Player with HTTP Range Support

As a student,
I want to watch video lessons with seek capability,
So that I can jump to specific sections (UX requirement: Video Stream Player).

**Acceptance Criteria:**

**Given** I am viewing a video asset
**When** I click play on the video player
**Then** the video streams from MinIO using the presigned URL with HTTP Range support
**And** the video player component uses HTML5 `<video>` element with controls
**And** I can seek to any position in the video by clicking the timeline
**And** seeking sends HTTP Range requests and playback resumes without full reload
**And** playback is smooth with minimal buffering (NFR-P4)
**And** the player displays current time, duration, and volume controls
**And** the player supports fullscreen mode

### Story 9.6: Implement Multi-File Upload Progress Tracker

As a publisher,
I want to see progress for all files when uploading a ZIP or multiple files,
So that I can monitor bulk uploads (UX requirement: Progress Tracker).

**Acceptance Criteria:**

**Given** I am uploading multiple files or a ZIP archive
**When** uploads are in progress
**Then** a progress tracker panel appears (bottom-right corner, non-blocking)
**And** the tracker lists each file with individual progress bars
**And** each file shows: file name, size, upload percentage, status (uploading/complete/failed)
**When** all uploads complete successfully
**Then** the tracker displays "All uploads complete" with success icon
**And** the tracker auto-dismisses after 5 seconds
**When** any upload fails
**Then** the failed file is highlighted in red with error message
**And** I can retry failed uploads by clicking "Retry"

### Story 9.7: Implement Responsive Design for Mobile and Tablet

As a user,
I want the interface to work on mobile and tablet devices,
So that I can access DCS from any device (UX requirement: Responsive design).

**Acceptance Criteria:**

**Given** I access the application on different devices
**When** I view on mobile (320px-767px)
**Then** navigation is a hamburger menu
**And** the asset table switches to card-based layout (one asset per card)
**And** upload zone is full-width with tap-to-browse
**And** core functionality works: upload, browse, download
**When** I view on tablet (768px-1023px)
**Then** navigation shows as a collapsible sidebar
**And** the asset table uses adaptive columns (fewer columns, more rows)
**And** asset cards are displayed in 2-column grid
**When** I view on desktop (1024px+)
**Then** full table view with all columns visible
**And** sidebar navigation is always visible
**And** multi-column layouts for dashboards

### Story 9.8: Implement Accessibility Features (WCAG 2.1 Level AA)

As a user with disabilities,
I want the interface to be accessible via keyboard and screen readers,
So that I can use the platform independently (UX requirement: Accessibility).

**Acceptance Criteria:**

**Given** I am using keyboard navigation
**When** I press Tab
**Then** focus moves through all interactive elements in logical order
**And** focus indicators are clearly visible (blue outline, 2px)
**When** I press Enter or Space on buttons
**Then** the button action triggers (same as mouse click)
**When** I use a screen reader
**Then** all images have alt text describing their content
**And** all form inputs have associated labels
**And** ARIA labels are present for icon-only buttons
**And** screen reader announces modal dialogs when they open
**And** table headers are properly marked with <th> and scope attributes
**When** I view the interface
**Then** color contrast meets WCAG AA standards (4.5:1 for text, 3:1 for large text)
**And** interactive elements have sufficient size (44x44px minimum touch targets)
