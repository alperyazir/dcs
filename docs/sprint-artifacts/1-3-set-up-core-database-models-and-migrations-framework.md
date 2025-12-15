# Story 1.3: Set Up Core Database Models and Migrations Framework

Status: done

## Story

As a developer,
I want the core database schema with multi-tenant tables and Alembic migrations configured,
so that I have a foundation for storing asset metadata with proper tenant isolation.

## Acceptance Criteria

1. **Given** PostgreSQL is running via Docker Compose
   **When** I create SQLModel models for users, tenants, assets, and audit_logs tables
   **Then** the User model includes id, email, hashed_password, role (enum: Admin/Supervisor/Publisher/School/Teacher/Student), tenant_id, created_at, updated_at

2. **And** the Tenant model includes id, name, tenant_type, created_at

3. **And** the Asset model includes id, user_id, tenant_id, bucket, object_key, file_name, file_size_bytes, mime_type, checksum, is_deleted, created_at, updated_at

4. **And** the AuditLog model includes id, user_id, action, asset_id, ip_address, timestamp, metadata_json

5. **And** All tables have proper indexes on tenant_id, user_id, and created_at columns (NFR-SC9)

6. **And** Alembic migration files are generated and can be applied with `alembic upgrade head`

7. **And** Database constraints enforce referential integrity (foreign keys, not null, unique)

8. **And** Row-level security foundation is prepared for multi-tenant isolation (FR27, FR28)

## Tasks / Subtasks

- [x] Task 1: Extend User model with role enum and tenant_id (AC: 1)
  - [x] Create UserRole enum with values: ADMIN, SUPERVISOR, PUBLISHER, SCHOOL, TEACHER, STUDENT
  - [x] Add `role` field to User model using SQLModel Field with enum type
  - [x] Add `tenant_id` field as foreign key to tenants table (nullable for superusers)
  - [x] Add `created_at` and `updated_at` timestamp fields with auto-generation
  - [x] Update UserBase, UserCreate, UserUpdate, UserPublic schemas accordingly
  - [x] Ensure existing tests pass with updated User model

- [x] Task 2: Create Tenant model (AC: 2)
  - [x] Create Tenant SQLModel class in app/models.py
  - [x] Fields: id (UUID PK), name (str, required), tenant_type (enum: PUBLISHER, SCHOOL, TEACHER, STUDENT), created_at
  - [x] Add unique constraint on tenant name
  - [x] Create TenantCreate, TenantPublic Pydantic schemas
  - [x] Add relationship from User to Tenant

- [x] Task 3: Create Asset model (AC: 3)
  - [x] Create Asset SQLModel class in app/models.py
  - [x] Fields: id (UUID PK), user_id (FK), tenant_id (FK), bucket (str), object_key (str), file_name (str, max 255), file_size_bytes (int), mime_type (str), checksum (str, nullable), is_deleted (bool, default False), deleted_at (datetime, nullable), created_at, updated_at
  - [x] Add composite unique constraint on (bucket, object_key)
  - [x] Create relationships: Asset.owner -> User, Asset.tenant -> Tenant
  - [x] Create AssetCreate, AssetUpdate, AssetPublic Pydantic schemas

- [x] Task 4: Create AuditLog model (AC: 4)
  - [x] Create AuditLog SQLModel class in app/models.py
  - [x] Fields: id (UUID PK), user_id (UUID, nullable for system actions), action (enum: UPLOAD, DOWNLOAD, DELETE, RESTORE, UPDATE, LOGIN, LOGOUT), asset_id (UUID, nullable), ip_address (str), timestamp (datetime), metadata_json (JSON/dict)
  - [x] Create AuditAction enum for action field
  - [x] This table should be append-only (no update/delete operations in CRUD)
  - [x] Create AuditLogCreate, AuditLogPublic schemas

- [x] Task 5: Add database indexes for multi-tenant queries (AC: 5)
  - [x] Add index on assets.tenant_id
  - [x] Add index on assets.user_id
  - [x] Add index on assets.created_at
  - [x] Add composite index on assets (tenant_id, is_deleted) for filtered queries
  - [x] Add index on audit_logs.user_id
  - [x] Add index on audit_logs.timestamp
  - [x] Add index on audit_logs.asset_id

- [x] Task 6: Generate and apply Alembic migration (AC: 6)
  - [x] Run `alembic revision --autogenerate -m "Add multi-tenant models (tenants, assets, audit_logs)"`
  - [x] Review generated migration file for correctness
  - [x] Apply migration with `alembic upgrade head`
  - [x] Verify tables created with correct columns and constraints
  - [x] Test downgrade with `alembic downgrade -1` then upgrade again

- [x] Task 7: Add database constraints (AC: 7)
  - [x] Verify foreign key constraints are properly defined with ON DELETE behavior
  - [x] Add CHECK constraint: file_size_bytes >= 0 on assets table
  - [x] Add NOT NULL constraints on required fields
  - [x] Verify unique constraints on: users.email, tenants.name, assets(bucket, object_key)

- [x] Task 8: Prepare row-level security foundation (AC: 8)
  - [x] Add comment in db.py documenting RLS strategy for future implementation
  - [x] Ensure all queries can be filtered by tenant_id
  - [x] Document in code how tenant_id will be injected via middleware
  - [x] Create helper function `get_tenant_filter()` stub for future RLS enforcement

- [x] Task 9: Update existing tests and add new model tests
  - [x] Update conftest.py with fixtures for Tenant, Asset, AuditLog
  - [x] Add test for User model with role and tenant_id
  - [x] Add test for Tenant model creation
  - [x] Add test for Asset model CRUD operations
  - [x] Add test for AuditLog append-only behavior
  - [x] Verify all 55+ existing tests still pass

## Dev Notes

### Architecture References

**Database Multi-Tenancy Strategy:**
[Source: docs/architecture/core-architectural-decisions.md#data-architecture]
- Row-level security with tenant_id columns on all tables
- Middleware injects user context into database queries
- PostgreSQL RLS policies enforce isolation as backstop defense

**Naming Conventions:**
[Source: docs/architecture/implementation-patterns-consistency-rules.md#naming-patterns]
- Table names: Lowercase plural nouns - `users`, `assets`, `tenants`, `audit_logs`
- Column names: Lowercase snake_case - `user_id`, `created_at`, `file_size_bytes`
- Primary keys: Always `id` (UUID type)
- Foreign keys: `{referenced_table}_id` pattern
- Timestamps: `created_at`, `updated_at`, `deleted_at`
- Booleans: `is_{attribute}` prefix - `is_deleted`, `is_active`

**Index Naming:**
- Format: `idx_{table}_{columns}` - e.g., `idx_assets_tenant_id`
- Constraint naming: `uq_{table}_{column}`, `fk_{table}_{ref_table}`, `ck_{table}_{constraint}`

### Technical Requirements

**SQLModel/Pydantic Patterns:**
[Source: docs/architecture/core-architectural-decisions.md#data-architecture]
- Use SQLModel for database models (combines SQLAlchemy 2.0 + Pydantic V2)
- Use Pydantic V2 for all request/response validation
- Model naming: Singular noun for SQLModel - `User`, `Asset`, `Tenant`
- Schema naming: `{Model}{Purpose}` - `AssetCreate`, `AssetPublic`, `UserUpdate`

**Field Types:**
- UUIDs: Use `uuid.UUID` with `default_factory=uuid.uuid4`
- Timestamps: Use `datetime` from `datetime` module
- Enums: Use Python `enum.Enum` with SQLModel compatibility
- JSON fields: Use `dict` type with SQLModel's JSON column support

**Existing Template Structure:**
The FastAPI Full Stack Template uses a single `app/models.py` file pattern. Maintain this pattern for now (don't split into models/ directory yet).

### Project Structure Notes

**Current Backend Structure:**
```
backend/app/
├── models.py          # Add new models here (User, Tenant, Asset, AuditLog)
├── crud.py            # Add CRUD functions for new models
├── core/db.py         # Database engine and init_db function
├── core/config.py     # Pydantic Settings
├── alembic/versions/  # Migration files will be generated here
```

**Existing Models to Extend:**
- `User` model already exists with: id, email, hashed_password, is_active, is_superuser, full_name
- Add: role (UserRole enum), tenant_id (FK), created_at, updated_at
- `Item` model exists but is sample data - can be removed later when Asset replaces it

### Previous Story Learnings

**From Story 1.2:**
- PostgreSQL is running on localhost:5432 (docker service: db)
- MinIO is running with versioning enabled on assets bucket
- Docker compose with healthchecks is working
- All 55 backend tests currently passing
- Use `docker compose exec backend` for running commands in container

**Git Patterns Established:**
- Feature branch naming: `story/{epic}-{story}-{slug}`
- Commit message format: `feat(story-{epic}.{story}): {description}`
- PR workflow with review before merge

### Library Versions

**Current Stack (from pyproject.toml):**
- Python 3.11+
- SQLModel (SQLAlchemy 2.0 + Pydantic V2)
- Alembic for migrations
- pytest for testing

### Testing Requirements

**Test Coverage:**
- Minimum 80% coverage target
- Run tests: `docker compose exec backend pytest`
- Tests must pass before PR merge

**Test Patterns:**
[Source: docs/architecture/implementation-patterns-consistency-rules.md#structure-patterns]
- Test files mirror source: `tests/crud/test_user.py` for `app/crud.py` user functions
- Use conftest.py fixtures for database sessions and test data

### References

- [Architecture: Data Architecture](docs/architecture/core-architectural-decisions.md#data-architecture)
- [Architecture: Multi-Tenant Authorization](docs/architecture/core-architectural-decisions.md#multi-tenant-authorization-pattern)
- [Patterns: Database Naming](docs/architecture/implementation-patterns-consistency-rules.md#database-naming-conventions)
- [Patterns: Code Naming](docs/architecture/implementation-patterns-consistency-rules.md#code-naming-conventions)
- [Structure: Backend Organization](docs/architecture/project-structure-boundaries.md#complete-project-directory-structure)
- [PRD: FR25-FR30 Multi-Tenant Storage](docs/epics.md#functional-requirements)
- [PRD: NFR-SC9 Database Indexing](docs/epics.md#nonfunctional-requirements)

## Dev Agent Record

### Context Reference

Story file: docs/sprint-artifacts/1-3-set-up-core-database-models-and-migrations-framework.md

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Migration file: backend/app/alembic/versions/b198e225ee29_add_multi_tenant_models.py
- Test output: 65 tests passed (55 original + 10 new model tests)

### Completion Notes List

1. **Models Implementation**: Created comprehensive SQLModel classes for Tenant, Asset, and AuditLog with proper enum types (UserRole, TenantType, AuditAction)
2. **User Model Extended**: Added role field with UserRole enum, tenant_id FK, created_at/updated_at timestamps
3. **Database Indexes**: All required indexes added via `__table_args__` including composite indexes for multi-tenant queries
4. **Alembic Migration**: Generated and applied migration b198e225ee29 with proper enum type creation using postgresql.ENUM
5. **Constraints**: CHECK constraint for file_size_bytes >= 0, foreign key constraints, unique constraints all verified
6. **RLS Foundation**: Added comprehensive documentation in db.py and get_tenant_filter() helper function
7. **CRUD Functions**: Implemented create/get/update for Tenant, Asset (with soft delete/restore), AuditLog (append-only)
8. **Tests**: Added 10 new tests covering Tenant, Asset, AuditLog models and CRUD operations

### Change Log

- 2025-12-15: Story implementation complete - all 9 tasks done, 65 tests passing
- 2025-12-15: Code review fixes applied:
  - Added UniqueConstraint on Asset (bucket, object_key) per AC3
  - Fixed User.updated_at and Asset.updated_at to auto-update in CRUD
  - Added tests for get_asset_by_id and get_audit_logs_by_asset
  - 67 tests now passing (55 original + 12 new model tests)

### File List

**New Files:**
- backend/app/alembic/versions/b198e225ee29_add_multi_tenant_models.py
- backend/app/alembic/versions/17b368820ee1_add_unique_constraint_on_asset_bucket_.py
- backend/tests/crud/test_models.py

**Modified Files:**
- backend/app/models.py (added Tenant, Asset, AuditLog models, extended User model, added enums, UniqueConstraint)
- backend/app/crud.py (added CRUD functions for Tenant, Asset, AuditLog, updated_at handling)
- backend/app/core/db.py (added RLS documentation and get_tenant_filter helper)
- backend/tests/conftest.py (updated imports and cleanup for new models)
- docs/sprint-artifacts/sprint-status.yaml (story status updates)
- .env (created from .env.example for local development - not tracked in git)
