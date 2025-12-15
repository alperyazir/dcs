# Project Context: Dream Central Storage

**Last Updated:** 2025-12-15
**Architecture Version:** Complete (8 steps)
**Status:** Ready for Implementation

---

## Technology Stack & Versions

### Backend
- **Python:** 3.11+ (required for async features)
- **FastAPI:** 0.104+ (API framework)
- **SQLModel:** Latest (ORM - combines SQLAlchemy 2.0 + Pydantic V2)
- **PostgreSQL:** 14+ (required for row-level security)
- **MinIO:** 7.2.x (S3-compatible object storage)
- **Alembic:** Latest (database migrations)
- **uv:** Latest (package manager, faster than pip)
- **pytest:** Latest with async support

### Frontend
- **React:** 18+ (required for concurrent features)
- **TypeScript:** Latest with strict mode enabled
- **Node.js:** 20+ LTS
- **Vite:** Latest (NOT Create React App)
- **TanStack Query:** v5 (state management - NO Redux)
- **shadcn/ui:** Latest (component library)
- **Tailwind CSS:** Latest
- **React Router:** v6
- **Vitest:** Latest (testing framework)

### Infrastructure
- **Docker Compose:** Latest (orchestration)
- **Traefik:** Latest (reverse proxy + automatic HTTPS)

---

## Critical Implementation Rules

### 🚨 MANDATORY ARCHITECTURAL PATTERNS

#### 1. Zero-Proxy Architecture (NEVER VIOLATE)
```python
# ❌ WRONG - Never proxy files through API
@router.get("/download/{asset_id}")
async def download_asset(asset_id: UUID):
    file_data = await minio.get_object(...)  # NO!
    return StreamingResponse(file_data)      # NO!

# ✅ CORRECT - Always use presigned URLs
@router.get("/download/{asset_id}")
async def download_asset(asset_id: UUID):
    presigned_url = await minio_service.generate_presigned_url(asset_id, ttl=3600)
    return {"download_url": presigned_url}  # Client downloads directly from MinIO
```

#### 2. Layered Architecture (NO BOUNDARY VIOLATIONS)
```python
# ❌ WRONG - Routes must NEVER access database directly
@router.get("/assets")
async def list_assets(db: Session = Depends(get_db)):
    return db.query(Asset).all()  # NO!

# ✅ CORRECT - Routes → Services → Repositories → Database
@router.get("/assets")
async def list_assets(
    asset_service: AssetService = Depends(get_asset_service)
):
    return await asset_service.list_assets()
```

#### 3. Multi-Tenant Isolation (ALWAYS ENFORCE)
```python
# ❌ WRONG - Missing tenant_id filtering
class AssetRepository:
    async def get_all(self, user_id: UUID):
        return await self.db.query(Asset).filter(Asset.user_id == user_id).all()

# ✅ CORRECT - MUST filter by tenant_id on ALL queries
class AssetRepository(BaseRepository):  # BaseRepository enforces tenant_id
    async def get_all(self, user_id: UUID, tenant_id: UUID):
        return await self.db.query(Asset).filter(
            Asset.user_id == user_id,
            Asset.tenant_id == tenant_id  # REQUIRED
        ).all()
```

---

### Python/FastAPI Rules

#### Naming Conventions
```python
# Database models and columns
class Asset(SQLModel, table=True):
    __tablename__ = "assets"  # Lowercase plural
    id: UUID
    user_id: UUID  # snake_case for all columns
    file_name: str
    is_deleted: bool = False  # Booleans: is_* or has_*

# Functions and variables
async def get_user_by_id(user_id: UUID) -> User:  # snake_case
    user_data = await repository.find(user_id)    # snake_case
    return user_data

# Classes
class AssetService:        # PascalCase
    pass

class UserRepository:      # PascalCase
    pass

# Constants
MAX_FILE_SIZE_MB = 5000   # UPPER_SNAKE_CASE
DEFAULT_PAGE_SIZE = 50
```

#### Dependency Injection Pattern
```python
# ✅ ALWAYS use FastAPI dependency injection
async def get_asset_service(
    repository: AssetRepository = Depends(get_asset_repository),
    minio: MinIOService = Depends(get_minio_service)
) -> AssetService:
    return AssetService(repository, minio)

@router.post("/assets")
async def create_asset(
    data: AssetCreate,
    current_user: User = Depends(get_current_user),  # Auth dependency
    service: AssetService = Depends(get_asset_service)
):
    return await service.create_asset(data, current_user.id)
```

#### Error Handling Pattern
```python
# ✅ Custom exceptions with structured error responses
class AssetNotFoundException(HTTPException):
    def __init__(self, asset_id: UUID):
        super().__init__(
            status_code=404,
            detail={
                "error_code": "ASSET_NOT_FOUND",
                "message": f"Asset {asset_id} not found",
                "details": {"asset_id": str(asset_id)}
            }
        )

# Service layer raises custom exceptions
class AssetService:
    async def get_asset(self, asset_id: UUID, user_id: UUID):
        asset = await self.repository.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundException(asset_id)
        if not self._has_permission(asset, user_id):
            raise PermissionDeniedException(asset_id, user_id)
        return asset
```

#### Request ID Tracing (MANDATORY)
```python
# ✅ EVERY log entry MUST include request_id
import logging
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id')

# Middleware sets request_id
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    request.state.request_id = request_id
    response = await call_next(request)
    return response

# All logging includes request_id
logger.info(
    "Asset created",
    extra={
        "request_id": request_id_var.get(),
        "asset_id": asset.id,
        "user_id": user_id
    }
)
```

---

### TypeScript/React Rules

#### Naming Conventions
```typescript
// Files
AssetCard.tsx        // Components: PascalCase
useAssets.ts         // Hooks: camelCase starting with 'use'
formatDate.ts        // Utilities: camelCase
apiClient.ts         // Services: camelCase

// Components
const AssetLibrary: React.FC = () => { ... }  // PascalCase

// Functions and variables
const handleUpload = () => { ... }  // camelCase
const assetList = [...];            // camelCase

// Constants
const MAX_UPLOAD_SIZE = 5000;       // UPPER_SNAKE_CASE
const API_BASE_URL = "...";

// Interfaces (props only)
interface IAssetCardProps {  // 'I' prefix for props
  assetId: string;
  onDelete: (id: string) => void;
}

// Types
type AssetStatus = 'active' | 'deleted';  // PascalCase, no prefix
```

#### TanStack Query Pattern (MANDATORY)
```typescript
// ✅ CORRECT - Use TanStack Query for ALL server state
const { data: assets, isLoading } = useQuery({
  queryKey: ['assets', { userId, page }],  // Hierarchical array keys
  queryFn: () => fetchAssets(userId, page),
  staleTime: 5 * 60 * 1000,  // 5 minutes
});

// ✅ Mutations with invalidation
const mutation = useMutation({
  mutationFn: (data: AssetCreate) => createAsset(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['assets'] });
  },
});

// ❌ WRONG - NEVER use custom fetch wrappers
const [assets, setAssets] = useState([]);  // NO!
useEffect(() => {
  fetchAssets().then(setAssets);  // NO!
}, []);

// ❌ WRONG - NEVER use Redux for server state
const assets = useSelector(state => state.assets);  // NO Redux!
```

#### State Management Boundaries
```typescript
// ✅ TanStack Query - ALL server state (assets, users, permissions)
const { data: asset } = useQuery({ queryKey: ['assets', assetId], ... });

// ✅ React Context - ONLY auth state
const { user, isAuthenticated, login, logout } = useAuth();

// ✅ Local State - ONLY UI state
const [isModalOpen, setModalOpen] = useState(false);
const [formErrors, setFormErrors] = useState<Record<string, string>>({});

// ❌ WRONG - NEVER use Context for server data
const AssetsContext = createContext();  // NO! Use TanStack Query instead
```

#### Component Structure Pattern
```typescript
// ✅ Page components own data fetching
const AssetLibrary: React.FC = () => {
  const { data: assets, isLoading } = useAssets();  // Page owns query

  return (
    <>
      {assets?.map(asset => (
        <AssetCard asset={asset} onDelete={handleDelete} />  // Pass data as props
      ))}
    </>
  );
};

// ✅ Feature components are presentational
interface IAssetCardProps {
  asset: Asset;                       // Receive data via props
  onDelete: (id: string) => void;     // Emit events via callbacks
}

const AssetCard: React.FC<IAssetCardProps> = ({ asset, onDelete }) => {
  // Local UI state only
  const [showMenu, setShowMenu] = useState(false);

  return <Card>...</Card>;
};
```

---

### Testing Rules

#### Test File Organization
```
backend/tests/
  conftest.py              # Pytest fixtures
  api/
    test_assets.py         # Tests for app/api/routes/assets.py
  services/
    test_asset_service.py  # Tests for app/services/asset_service.py

frontend/tests/
  setup.ts                 # Vitest setup
  components/
    AssetCard.test.tsx     # Tests for src/routes/assets/components/AssetCard.tsx
```

**Rule:** Tests MUST mirror source structure exactly.

#### Testing Patterns
```python
# ✅ Backend tests use pytest with async support
@pytest.mark.asyncio
async def test_create_asset_success(
    client: TestClient,
    test_user: User,
    test_db: Session
):
    response = await client.post(
        "/api/v1/assets",
        json={"file_name": "test.pdf", ...},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 201
    assert response.json()["file_name"] == "test.pdf"
```

```typescript
// ✅ Frontend tests use Vitest + Testing Library
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

test('AssetCard displays asset name', () => {
  const queryClient = new QueryClient();
  const asset = { id: '123', file_name: 'test.pdf', ... };

  render(
    <QueryClientProvider client={queryClient}>
      <AssetCard asset={asset} onDelete={jest.fn()} />
    </QueryClientProvider>
  );

  expect(screen.getByText('test.pdf')).toBeInTheDocument();
});
```

#### Coverage Requirements
- **Backend:** 80% minimum coverage (enforced by CI/CD)
- **Frontend:** Component tests for all routes/*/components/
- **Integration tests:** Required for all API endpoints

---

### Code Quality & Style Rules

#### API Response Format (NEVER DEVIATE)
```typescript
// ✅ Single resource
{
  "id": "uuid",
  "file_name": "example.pdf",
  "created_at": "2025-12-15T10:30:00Z"  // ISO 8601 UTC
}

// ✅ Collection with pagination
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}

// ✅ Error response
{
  "error_code": "ASSET_NOT_FOUND",
  "message": "Asset with ID 12345 does not exist",
  "details": {"asset_id": "12345"},
  "request_id": "uuid",
  "timestamp": "2025-12-15T10:30:00Z"
}
```

#### Data Format Standards
```python
# ✅ Dates: ISO 8601 strings in UTC
"created_at": "2025-12-15T10:30:00Z"  # NOT Unix timestamp, NOT local time

# ✅ UUIDs: String format
"id": "550e8400-e29b-41d4-a716-446655440000"  # NOT integer

# ✅ File sizes: Integer bytes
"file_size_bytes": 1048576  # NOT "1 MB" string, frontend formats for display

# ✅ Booleans: JSON true/false
"is_deleted": false  # NOT 1/0, NOT "false" string
```

#### Import Organization
```python
# ✅ Python imports order
from typing import List, Optional  # Standard library
from uuid import UUID

from fastapi import APIRouter, Depends  # Third-party
from sqlmodel import Session

from app.core.db import get_db  # Local imports
from app.models.asset import Asset
from app.services.asset_service import AssetService
```

```typescript
// ✅ TypeScript imports order
import React from 'react';  // React
import { useQuery } from '@tanstack/react-query';  // Third-party

import { Button } from '@/components/ui/Button';  // UI components
import { useAssets } from '@/hooks/useAssets';  // Hooks
import { formatBytes } from '@/lib/formatters';  // Utilities
import type { Asset } from '@/types/asset';  // Types
```

---

### Development Workflow Rules

#### Git Commit Messages
```bash
# ✅ REQUIRED format for all commits
Add multipart upload support for large files

Implement chunked upload workflow using MinIO presigned URLs.
Frontend uploads chunks in parallel, backend validates ETags.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Rules:**
1. Imperative mood ("Add", "Fix", "Update", NOT "Added", "Fixes")
2. Clear description of WHAT and WHY
3. Always include Claude Code attribution footer
4. NEVER use `--amend` unless pre-commit hook made changes

#### Branch Naming
```bash
# Feature branches
feature/multipart-upload
feature/asset-versioning

# Bug fixes
fix/asset-deletion-bug
fix/permission-check-error

# NEVER force push to main/master
```

---

### Critical Don't-Miss Rules (Anti-Patterns)

#### ❌ NEVER Do These

```python
# ❌ 1. NEVER proxy files through API (architectural mandate)
@router.get("/download/{asset_id}")
async def download_asset(asset_id: UUID):
    file_content = minio.get_object(...)  # WRONG!
    return StreamingResponse(file_content)  # Violates zero-proxy architecture

# ❌ 2. NEVER bypass service layer
@router.post("/assets")
async def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    asset = Asset(**data.dict())  # WRONG!
    db.add(asset)  # Routes must call services, not DB directly

# ❌ 3. NEVER skip tenant_id filtering
async def get_assets(user_id: UUID):
    return db.query(Asset).filter(Asset.user_id == user_id).all()  # WRONG! Missing tenant_id

# ❌ 4. NEVER log without request_id
logger.info("Asset created")  # WRONG! Must include request_id for tracing
```

```typescript
// ❌ 5. NEVER use Redux or custom fetch wrappers
const assets = useSelector(state => state.assets);  // WRONG! Use TanStack Query

// ❌ 6. NEVER use Context for server data
const { assets } = useAssetsContext();  // WRONG! Use TanStack Query

// ❌ 7. NEVER use generic 'id' in path parameters
<Route path="/assets/:id" />  // WRONG! Use descriptive name
<Route path="/assets/:asset_id" />  // CORRECT

// ❌ 8. NEVER hardcode API URLs
const response = await fetch('http://localhost:8000/api/v1/assets');  // WRONG!
const response = await apiClient.get('/api/v1/assets');  // CORRECT (uses generated client)
```

#### Security Anti-Patterns
```python
# ❌ NEVER construct SQL with string concatenation
query = f"SELECT * FROM assets WHERE user_id = '{user_id}'"  # SQL INJECTION!

# ❌ NEVER skip authentication checks
@router.get("/assets/{asset_id}")
async def get_asset(asset_id: UUID):  # WRONG! Missing Depends(get_current_user)
    return await service.get_asset(asset_id)

# ❌ NEVER log sensitive data
logger.info(f"User logged in with password: {password}")  # WRONG!
logger.info(f"JWT token: {token}")  # WRONG!
```

#### Performance Anti-Patterns
```python
# ❌ NEVER load all records without pagination
@router.get("/assets")
async def list_assets():
    return await db.query(Asset).all()  # WRONG! Could be millions of rows

# ❌ NEVER buffer entire files in memory
file_content = await file.read()  # WRONG! Files can be GBs
return Response(content=file_content)  # Out of memory!

# ✅ CORRECT - Always stream
return StreamingResponse(file.stream())  # Uses presigned URL, not this pattern
```

---

## Edge Cases & Gotchas

### 1. MinIO Presigned URL TTL
```python
# Upload URLs: 15 minutes (security)
upload_url = minio.generate_presigned_url(expires=900)

# Download URLs: 1 hour (classroom usage)
download_url = minio.generate_presigned_url(expires=3600)

# NEVER use TTL > 24 hours (security risk)
```

### 2. PostgreSQL Row-Level Security
```sql
-- RLS policies MUST be enabled on ALL tenant tables
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON assets
FOR ALL TO authenticated
USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### 3. Soft Delete Pattern
```python
# ✅ Soft delete sets is_deleted flag
asset.is_deleted = True
asset.deleted_at = datetime.utcnow()
db.commit()

# ❌ NEVER hard delete (data loss!)
db.delete(asset)  # WRONG!
```

### 4. TanStack Query Cache Invalidation
```typescript
// ✅ Invalidate related queries after mutation
const mutation = useMutation({
  mutationFn: deleteAsset,
  onSuccess: () => {
    // Invalidate ALL asset queries
    queryClient.invalidateQueries({ queryKey: ['assets'] });
    // Also invalidate specific asset
    queryClient.invalidateQueries({ queryKey: ['assets', assetId] });
  },
});
```

---

## Project-Specific Conventions

### MinIO Bucket Structure
```
assets/  (single bucket)
  publishers/{publisher_id}/{asset_id}/{version_id}/file.pdf
  teachers/{teacher_id}/{asset_id}/{version_id}/video.mp4
  students/{student_id}/... (read-only, no uploads)
  schools/{school_id}/...
```

### Role Hierarchy
```python
# Admin/Supervisor: Full access (bypass RLS)
# Publisher: Write to /publishers/{id}/, read own + granted
# Teacher: Write to /teachers/{id}/, read granted from publishers
# Student: Read-only, granted by teachers via LMS
# School: Organizational, manages teachers
```

### API Versioning Strategy
- Current: `/api/v1/`
- Breaking changes: Create `/api/v2/`
- Maintain v1 for **6 months** after v2 release
- NEVER break v1 compatibility without migration period

---

## Quick Reference

### When implementing ANY feature:
1. ✅ Read architecture.md first
2. ✅ Follow naming conventions (snake_case backend, camelCase frontend)
3. ✅ Use layered architecture (routes → services → repositories)
4. ✅ Add request_id to all logs
5. ✅ Use TanStack Query for server state (NO Redux)
6. ✅ Generate presigned URLs (NEVER proxy files)
7. ✅ Filter by tenant_id on ALL queries
8. ✅ Write tests that mirror source structure
9. ✅ Handle errors with custom exceptions + global handlers
10. ✅ Update this file if new patterns emerge

### When in doubt:
- **Architecture questions:** Read `/docs/architecture.md`
- **Implementation patterns:** This file
- **API contracts:** OpenAPI docs at `/docs` endpoint
- **Testing patterns:** Check existing tests in `tests/` directory

---

**This file is the single source of truth for implementation rules. All AI agents MUST follow these patterns exactly.**
