# Project Context Analysis

## Requirements Overview

**Functional Requirements:**

Dream Central Storage has 67 functional requirements organized into 8 core capability areas that define the architectural scope:

1. **Asset Management (FR1-FR11):** Upload, download, versioning, soft delete/restore, metadata tracking, and folder organization
2. **Access Control & Authentication (FR12-FR24):** JWT authentication, 6-role RBAC model, signed URL generation, ownership validation, rate limiting
3. **Multi-Tenant Storage Organization (FR25-FR30):** Prefix-based tenant isolation, separate storage areas per tenant type, trash management
4. **Integration & API Layer (FR31-FR40):** RESTful API, multipart uploads, API documentation, LMS assignment integration, config.json delivery for FlowBook
5. **Search & Asset Discovery (FR41-FR46):** Metadata search, filtering, asset library with previews, role-specific browsing
6. **Streaming & Media Delivery (FR47-FR52):** HTTP Range support for video/audio, direct MinIO access via signed URLs, preview capabilities, batch downloads
7. **Audit & Compliance (FR53-FR60):** Immutable audit logs, compliance reporting, configurable retention, data integrity via checksums
8. **System Operations & Monitoring (FR61-FR67):** Health checks, metrics exposure, backup/replication, encryption support

**Non-Functional Requirements:**

Critical quality attributes that will drive architectural decisions:

- **Performance (NFR-P1 to P9):** P95 API response <500ms, signed URLs <100ms, no file buffering in memory, streaming ZIP extraction
- **Reliability & Availability (NFR-R1 to R12):** 99% uptime at 3mo → 99.9%+ at 12mo, zero data loss, RTO <30min, metadata sync integrity
- **Security (NFR-S1 to S13):** JWT auth, HTTPS/TLS, encryption at rest support, COPPA/FERPA compliance, immutable audit logs
- **Scalability (NFR-SC1 to SC12):** 1TB → 2TB storage growth, 3 → 5 app integrations, 10x user growth tolerance, horizontal scaling
- **Maintainability & Operability (NFR-M1 to M10):** Zero-downtime updates, API versioning, comprehensive docs, request ID tracing

**Scale & Complexity:**

- **Primary domain:** Full-stack platform (API backend + admin/user frontend)
- **Complexity level:** Medium
- **Target scale:** Conservative growth - 3-5 applications, up to 2TB storage, modest concurrent users
- **Estimated architectural components:** 4 major layers (Storage, API, Database, Frontend) with cross-cutting concerns

## Technical Constraints & Dependencies

**Hard Constraints:**

- **MinIO (S3-compatible storage):** Core storage layer - architecture must leverage MinIO's strengths (versioning, distributed mode, metrics)
- **FastAPI (Python):** API framework - architecture must align with async Python patterns
- **PostgreSQL:** Metadata store - must handle multi-tenant queries efficiently
- **React/Next.js:** Frontend framework - admin and user interfaces

**Dependencies on External Systems:**

- **LMS (in development):** Primary consumer - will manage publisher-to-teacher and teacher-to-student assignments
- **FlowBook (existing):** Offline desktop app - needs config.json + assets from DCS
- **Kanban (future):** Production workflow tool - will track book creation pipeline

**Architectural Mandates from PRD:**

- **Zero-proxy design:** Files must NOT flow through API layer - use signed URLs for direct client-to-MinIO access
- **Streaming-first:** ZIP extraction and file operations must stream without full RAM/disk buffering
- **Metadata-driven:** All business logic lives in metadata (PostgreSQL), MinIO is pure binary storage
- **Stability over performance:** Every design trade-off favors reliability and consistency

## Cross-Cutting Concerns Identified

These concerns will affect multiple architectural components and require coordinated decisions:

1. **Multi-Tenant Isolation**
   - Impacts: Storage paths, database queries, API authorization, frontend UI
   - Critical for: Data privacy, compliance, security

2. **Role-Based Authorization**
   - Impacts: API middleware, database row-level security, frontend route protection
   - Pattern: Write to own area only, read with grants managed by LMS

3. **Audit Trail & Compliance**
   - Impacts: All CRUD operations, API middleware, database design
   - Requirements: Immutable logs, COPPA/FERPA adherence, retention policies

4. **File Integrity & Versioning**
   - Impacts: Upload workflows, MinIO configuration, metadata tracking
   - Requirements: Checksums, version history, soft delete recovery

5. **Performance Optimization**
   - Impacts: API design (no proxying), database indexing, caching strategy
   - Requirements: Low CPU/RAM, fast metadata queries, streaming operations

6. **Integration Reliability**
   - Impacts: API contract stability, versioning, error handling, documentation
   - Requirements: Multiple app versions supported, clear error messages, backward compatibility

7. **Monitoring & Operability**
   - Impacts: Logging strategy, metrics collection, health checks, deployment process
   - Requirements: Request tracing, MinIO metrics, zero-downtime updates
