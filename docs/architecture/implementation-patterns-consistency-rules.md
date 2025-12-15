# Implementation Patterns & Consistency Rules

## Pattern Categories Defined

**Critical Conflict Points Identified:**

43 potential conflict areas where AI agents could make inconsistent choices, organized into 5 major categories: Naming (15), Structure (8), Format (10), Communication (6), and Process (4).

**Pattern Philosophy:**

These patterns ensure that when multiple AI agents implement different features, their code integrates seamlessly without conflicts in naming, structure, or behavior. Patterns follow the principle: **"Convention over configuration, consistency over cleverness."**

## Naming Patterns

**Database Naming Conventions:**

- **Table Names:** Lowercase plural nouns - `users`, `assets`, `audit_logs`
  - Exception: Junction tables use singular - `asset_permission` (not `assets_permissions`)
  - Multi-tenant tables include `tenant_id` column
- **Column Names:** Lowercase snake_case - `user_id`, `created_at`, `file_size_bytes`
  - Primary keys: Always `id` (UUID type preferred for distributed systems)
  - Foreign keys: `{referenced_table}_id` - `user_id`, `publisher_id`
  - Timestamps: `created_at`, `updated_at`, `deleted_at` (for soft deletes)
  - Booleans: `is_{attribute}` or `has_{attribute}` - `is_active`, `has_permission`
- **Index Names:** `idx_{table}_{columns}` - `idx_assets_user_id`, `idx_audit_logs_timestamp`
- **Constraint Names:**
  - Unique: `uq_{table}_{column}` - `uq_users_email`
  - Foreign key: `fk_{table}_{ref_table}` - `fk_assets_users`
  - Check: `ck_{table}_{constraint}` - `ck_assets_file_size_positive`

**Example:**

```sql
-- CORRECT
CREATE TABLE assets (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_assets_users FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT ck_assets_file_size_positive CHECK (file_size_bytes >= 0)
);
CREATE INDEX idx_assets_tenant_id ON assets(tenant_id);

-- INCORRECT
CREATE TABLE Asset ( -- Wrong: Should be lowercase plural
    ID serial, -- Wrong: Should be UUID
    UserID int, -- Wrong: Should be snake_case
    fileName text, -- Wrong: Should be snake_case
    deleted boolean -- Wrong: Should be is_deleted
);
```

**API Naming Conventions:**

- **Endpoint Paths:** Lowercase plural nouns, kebab-case for multi-word - `/api/v1/assets`, `/api/v1/audit-logs`
  - Collection: `/api/v1/assets` (GET for list, POST for create)
  - Individual: `/api/v1/assets/{asset_id}` (GET, PUT, DELETE)
  - Sub-resources: `/api/v1/assets/{asset_id}/versions`
  - Actions: Use verbs as final segment - `/api/v1/assets/{asset_id}/restore`
- **Path Parameters:** Curly braces with descriptive name - `{asset_id}`, `{user_id}`, `{version_number}`
  - Always use specific names, never just `{id}`
- **Query Parameters:** snake_case - `?page_size=20&sort_by=created_at&order=desc`
  - Pagination: `page`, `page_size` (default 50, max 100)
  - Sorting: `sort_by`, `order` (asc/desc)
  - Filtering: `{field}_filter` - `status_filter=active`
- **HTTP Methods:**
  - GET: Retrieve resources (list or single)
  - POST: Create new resources
  - PUT: Full resource update
  - PATCH: Partial resource update
  - DELETE: Soft delete (mark `is_deleted=true`)
- **Headers:** PascalCase with hyphens - `X-Request-ID`, `X-User-ID`, `Authorization`

**Example:**

```python
# CORRECT
@router.get("/api/v1/assets", response_model=PaginatedAssetList)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at"),
    tenant_id_filter: Optional[UUID] = None,
    current_user: User = Depends(get_current_user)
):
    ...

@router.post("/api/v1/assets/{asset_id}/restore")
async def restore_asset(asset_id: UUID, current_user: User = Depends(get_current_user)):
    ...

# INCORRECT
@router.get("/api/v1/Asset") # Wrong: Should be lowercase plural
async def getAssets(pageSize: int = 20): # Wrong: Should be snake_case
    ...

@router.post("/api/v1/assets/{id}/Restore") # Wrong: Non-specific {id}, PascalCase action
```

**Code Naming Conventions:**

**Python (Backend):**

- **Modules/Files:** Lowercase snake_case - `asset_service.py`, `user_repository.py`
- **Classes:** PascalCase - `AssetService`, `UserRepository`, `AssetCreateSchema`
  - SQLModel models: Singular noun - `Asset`, `User`, `AuditLog`
  - Pydantic schemas: `{Model}{Purpose}` - `AssetCreate`, `AssetResponse`, `UserUpdate`
  - Services: `{Domain}Service` - `AssetService`, `AuthService`
  - Repositories/CRUD: `{Model}Repository` - `AssetRepository`, `UserRepository`
- **Functions:** Lowercase snake_case, verb-first - `get_user_by_id`, `create_asset`, `validate_permissions`
- **Variables:** Lowercase snake_case - `user_id`, `asset_metadata`, `signed_url`
- **Constants:** Uppercase snake_case - `MAX_FILE_SIZE_MB`, `DEFAULT_PAGE_SIZE`, `ALLOWED_MIME_TYPES`
- **Private members:** Leading underscore - `_validate_tenant_access`, `_internal_user_id`

**TypeScript (Frontend):**

- **Files/Modules:** PascalCase for components, camelCase for utilities
  - Components: `AssetCard.tsx`, `UploadModal.tsx`
  - Hooks: `useAssets.ts`, `useAuth.ts`
  - Utilities: `formatDate.ts`, `apiClient.ts`
- **Components:** PascalCase - `AssetLibrary`, `UploadProgressBar`, `UserMenu`
- **Functions:** camelCase, verb-first - `getUserData`, `handleUpload`, `validateForm`
- **Variables:** camelCase - `userId`, `assetList`, `isLoading`
- **Constants:** UPPER_SNAKE_CASE - `MAX_UPLOAD_SIZE`, `API_BASE_URL`
- **Types/Interfaces:**
  - Interfaces: PascalCase with `I` prefix for props - `IAssetCardProps`, `IUserProfile`
  - Types: PascalCase - `AssetStatus`, `UploadState`
  - Enums: PascalCase, values UPPER_SNAKE_CASE

**Example:**

```python
# CORRECT - Python
class Asset(SQLModel, table=True):
    id: UUID
    user_id: UUID
    file_name: str
    is_deleted: bool = False

class AssetService:
    def __init__(self, repository: AssetRepository):
        self._repository = repository

    async def create_asset(self, data: AssetCreate, user_id: UUID) -> Asset:
        return await self._repository.create(data, user_id)

# INCORRECT - Python
class asset: # Wrong: Should be PascalCase
    userId: UUID # Wrong: Should be snake_case
    FileName: str # Wrong: Should be snake_case

def CreateAsset(data): # Wrong: Should be snake_case
    pass
```

```typescript
// CORRECT - TypeScript
interface IAssetCardProps {
  assetId: string;
  onDelete: (id: string) => void;
}

const AssetCard: React.FC<IAssetCardProps> = ({ assetId, onDelete }) => {
  const { data: asset, isLoading } = useAsset(assetId);

  const handleDeleteClick = () => {
    onDelete(assetId);
  };

  return <div>...</div>;
};

// INCORRECT - TypeScript
interface AssetCardProps { // Wrong: Missing I prefix
  asset_id: string; // Wrong: Should be camelCase
}

const assetCard = (props) => { // Wrong: Should be PascalCase
  const DeleteAsset = () => {}; // Wrong: Should be camelCase
};
```

## Structure Patterns

**Project Organization:**

**Backend Structure (Python/FastAPI):**

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependency injection (DB session, auth)
│   │   ├── main.py              # API router aggregation
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── assets.py        # Asset CRUD endpoints
│   │       ├── users.py         # User management endpoints
│   │       ├── auth.py          # Authentication endpoints
│   │       └── health.py        # Health check endpoints
│   ├── core/
│   │   ├── config.py            # Pydantic settings
│   │   ├── db.py                # Database engine and session
│   │   ├── security.py          # JWT, password hashing
│   │   └── constants.py         # Application constants
│   ├── models/                  # SQLModel ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── asset.py
│   │   └── audit_log.py
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── asset.py             # AssetCreate, AssetResponse, AssetUpdate
│   │   ├── user.py
│   │   └── common.py            # Shared schemas (PaginatedResponse, ErrorResponse)
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── asset_service.py
│   │   ├── auth_service.py
│   │   └── minio_service.py
│   ├── repositories/            # Data access layer (CRUD operations)
│   │   ├── __init__.py
│   │   ├── asset_repository.py
│   │   └── user_repository.py
│   ├── middleware/              # Custom middleware
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   ├── logging_middleware.py
│   │   └── rate_limit_middleware.py
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   └── helpers.py
│   └── main.py                  # FastAPI app initialization
├── alembic/                     # Database migrations
│   ├── versions/
│   └── env.py
├── tests/                       # Test suites
│   ├── api/                     # API endpoint tests
│   ├── services/                # Service layer tests
│   ├── repositories/            # Repository tests
│   └── conftest.py              # Pytest fixtures
├── Dockerfile
├── pyproject.toml               # Python dependencies (uv)
└── .env.example
```

**Frontend Structure (React/TypeScript):**

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                  # shadcn/ui base components
│   │   │   ├── Button.tsx
│   │   │   ├── Dialog.tsx
│   │   │   └── Input.tsx
│   │   └── Common/              # Shared application components
│   │       ├── Navbar.tsx
│   │       ├── Footer.tsx
│   │       └── ErrorBoundary.tsx
│   ├── routes/                  # Feature-based page organization
│   │   ├── _layout/
│   │   │   ├── MainLayout.tsx
│   │   │   └── AuthLayout.tsx
│   │   ├── assets/              # Asset management feature
│   │   │   ├── AssetLibrary.tsx
│   │   │   ├── AssetDetail.tsx
│   │   │   └── components/
│   │   │       ├── AssetCard.tsx
│   │   │       └── AssetFilter.tsx
│   │   ├── upload/              # Upload feature
│   │   │   ├── UploadPage.tsx
│   │   │   └── components/
│   │   │       ├── UploadModal.tsx
│   │   │       └── UploadProgress.tsx
│   │   └── admin/               # Admin feature
│   │       ├── Dashboard.tsx
│   │       └── components/
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAssets.ts
│   │   ├── useUpload.ts
│   │   ├── useAuth.ts
│   │   └── usePagination.ts
│   ├── client/                  # Auto-generated API client
│   │   ├── api.ts               # Generated from OpenAPI
│   │   └── models.ts
│   ├── lib/                     # Utilities and helpers
│   │   ├── api.ts               # API client configuration
│   │   ├── formatters.ts        # Date/size formatting
│   │   └── validators.ts
│   ├── types/                   # Shared TypeScript types
│   │   ├── asset.ts
│   │   └── user.ts
│   ├── constants/               # Application constants
│   │   └── config.ts
│   └── main.tsx                 # React entry point
├── public/                      # Static assets
├── tests/                       # Frontend tests
│   └── components/
├── Dockerfile
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**File Organization Rules:**

1. **Co-location:** Related files stay together
   - Feature components live in `routes/{feature}/components/`
   - Feature-specific hooks live in feature directory or shared `hooks/`
   - Shared UI components in `components/ui/` or `components/Common/`

2. **Test Location:** Tests mirror source structure
   - Backend: `tests/api/test_assets.py` mirrors `app/api/routes/assets.py`
   - Frontend: `tests/components/AssetCard.test.tsx` mirrors `src/routes/assets/components/AssetCard.tsx`

3. **Index Files:** Use `__init__.py` (Python) for clean imports
   - Export public API from modules
   - Do NOT use barrel exports excessively in TypeScript (impacts tree-shaking)

4. **Configuration Files:** Root level only
   - Environment: `.env`, `.env.example`, `.env.production`
   - Docker: `Dockerfile`, `docker-compose.yml` in service root
   - Config: `pyproject.toml`, `tsconfig.json`, `vite.config.ts` in service root

**Anti-Pattern:**

```
# WRONG - Don't mix concerns
backend/app/
├── asset_routes.py              # Wrong: Routes, services, models mixed
├── asset_service.py
├── user_routes.py
└── utils_and_helpers_mixed.py   # Wrong: Non-descriptive naming

# WRONG - Don't scatter tests
backend/app/api/routes/
├── assets.py
└── test_assets.py               # Wrong: Tests should be in tests/ directory
```

## Format Patterns

**API Response Formats:**

**Success Response (Single Resource):**

```json
{
  "id": "uuid-here",
  "user_id": "uuid-here",
  "file_name": "example.pdf",
  "file_size_bytes": 1048576,
  "created_at": "2025-12-15T10:30:00Z",
  "updated_at": "2025-12-15T10:30:00Z"
}
```

**Success Response (Collection with Pagination):**

```json
{
  "items": [
    {"id": "uuid-1", ...},
    {"id": "uuid-2", ...}
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

**Error Response:**

```json
{
  "error_code": "ASSET_NOT_FOUND",
  "message": "Asset with ID 12345 does not exist or you lack permission to access it",
  "details": {
    "asset_id": "12345",
    "user_id": "67890"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-15T10:30:00Z"
}
```

**Error Code Conventions:**

- Format: `{RESOURCE}_{FAILURE_TYPE}` in UPPER_SNAKE_CASE
- Examples: `ASSET_NOT_FOUND`, `USER_UNAUTHORIZED`, `QUOTA_EXCEEDED`, `VALIDATION_ERROR`
- HTTP status codes:
  - 200: Success
  - 201: Created
  - 204: No Content (for DELETE)
  - 400: Bad Request (validation errors)
  - 401: Unauthorized (not authenticated)
  - 403: Forbidden (authenticated but not authorized)
  - 404: Not Found
  - 409: Conflict (e.g., duplicate resource)
  - 422: Unprocessable Entity (semantic validation errors)
  - 429: Too Many Requests (rate limit)
  - 500: Internal Server Error

**Data Format Standards:**

- **Dates/Times:** ISO 8601 strings in UTC - `"2025-12-15T10:30:00Z"`
  - Backend stores as `datetime` with timezone
  - API serializes to ISO string
  - Frontend parses to `Date` objects
- **UUIDs:** String format - `"550e8400-e29b-41d4-a716-446655440000"`
  - Use UUID v4 for new IDs
  - Database stores as UUID type
- **File Sizes:** Integer bytes - `1048576` (not "1 MB")
  - Frontend formats for display: `formatBytes(1048576) => "1.0 MB"`
- **Booleans:** JSON `true`/`false` (never 1/0 or "true"/"false" strings)
- **Null Handling:**
  - Optional fields: `null` when absent
  - Required fields: Never null, validation error if missing
  - Empty arrays: `[]` (never null)
- **Field Naming in JSON:**
  - Backend (Python) internally: `snake_case`
  - API JSON responses: `snake_case` (Pydantic `alias_generator` disabled)
  - Frontend (TypeScript) internally: `camelCase` (client generator transforms)

**Example Schema Definitions:**

```python
# Backend - Pydantic Schema
class AssetResponse(BaseModel):
    id: UUID
    user_id: UUID
    file_name: str
    file_size_bytes: int
    mime_type: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        # Return snake_case in JSON (don't transform to camelCase)
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440001",
                "file_name": "document.pdf",
                "file_size_bytes": 1048576,
                "mime_type": "application/pdf",
                "is_deleted": False,
                "created_at": "2025-12-15T10:30:00Z",
                "updated_at": "2025-12-15T10:30:00Z"
            }
        }
```

```typescript
// Frontend - TypeScript Interface (from generated client)
interface Asset {
  id: string;
  user_id: string;        // Received as snake_case from API
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  is_deleted: boolean;
  created_at: string;     // ISO date string
  updated_at: string;
}

// Frontend - Usage with transformation
const assetDisplay = {
  id: asset.id,
  fileName: asset.file_name,          // Transform for internal use
  fileSize: formatBytes(asset.file_size_bytes),
  uploadedAt: new Date(asset.created_at)
};
```

## Communication Patterns

**API Request/Response Flow:**

1. **Request ID Injection:** Middleware generates UUID v4 for every request
2. **Authentication:** JWT validation via dependency injection
3. **Authorization:** Row-level security checks in service layer
4. **Validation:** Pydantic schema validation on request body
5. **Business Logic:** Service layer orchestrates
6. **Data Access:** Repository layer queries database
7. **Response:** Pydantic schema serialization
8. **Logging:** Structured JSON logs with request_id

**State Management Patterns (Frontend):**

**TanStack Query Patterns:**

- **Query Keys:** Array format with hierarchical structure
  ```typescript
  // CORRECT
  ['assets', { userId: '123', page: 1 }]
  ['assets', assetId]
  ['users', 'me']

  // INCORRECT
  'getAssets123' // Wrong: Not hierarchical, not invalidatable
  ```

- **Query Options:**
  ```typescript
  // Standard configuration
  const { data, isLoading, error } = useQuery({
    queryKey: ['assets', { userId, page }],
    queryFn: () => fetchAssets(userId, page),
    staleTime: 5 * 60 * 1000,        // 5 minutes
    cacheTime: 10 * 60 * 1000,       // 10 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  });
  ```

- **Mutations and Invalidation:**
  ```typescript
  const mutation = useMutation({
    mutationFn: (data: AssetCreate) => createAsset(data),
    onSuccess: () => {
      // Invalidate affected queries
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
    onError: (error) => {
      toast.error(`Upload failed: ${error.message}`);
    }
  });
  ```

**React Context Patterns:**

- **Auth Context Only:** Use Context for authentication state, not application data
  ```typescript
  // CORRECT - Auth context
  interface AuthContextType {
    user: User | null;
    login: (credentials: Credentials) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
  }

  // INCORRECT - Don't use Context for server data
  interface AssetContextType {
    assets: Asset[]; // Wrong: Use TanStack Query instead
  }
  ```

**Event Naming (Future Async Events):**

When implementing event-driven features (e.g., Redis pub/sub for background jobs):

- **Format:** `{resource}.{action}` in lowercase
  - Examples: `asset.uploaded`, `asset.deleted`, `user.created`
- **Payload Structure:**
  ```typescript
  {
    event: "asset.uploaded",
    timestamp: "2025-12-15T10:30:00Z",
    data: {
      asset_id: "uuid",
      user_id: "uuid",
      file_name: "example.pdf"
    },
    metadata: {
      request_id: "uuid",
      triggered_by: "user_id"
    }
  }
  ```

## Process Patterns

**Error Handling Patterns:**

**Backend Error Handling:**

```python
# Service Layer - Raise domain exceptions
class AssetService:
    async def get_asset(self, asset_id: UUID, user_id: UUID) -> Asset:
        asset = await self._repository.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundException(asset_id)
        if not self._has_permission(asset, user_id):
            raise PermissionDeniedException(asset_id, user_id)
        return asset

# Custom Exceptions
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

# Global Exception Handler (main.py)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.detail.get("error_code", "UNKNOWN_ERROR"),
            "message": exc.detail.get("message", str(exc.detail)),
            "details": exc.detail.get("details", {}),
            "request_id": request.state.request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )
```

**Frontend Error Handling:**

```typescript
// Component - Display user-friendly errors
const AssetDetail: React.FC = ({ assetId }) => {
  const { data: asset, error, isLoading } = useQuery({
    queryKey: ['assets', assetId],
    queryFn: () => fetchAsset(assetId),
  });

  if (isLoading) return <LoadingSpinner />;

  if (error) {
    // Display user-friendly error from API
    const apiError = error as ApiError;
    return (
      <ErrorMessage
        title="Failed to load asset"
        message={apiError.message}
        code={apiError.error_code}
        onRetry={() => queryClient.invalidateQueries({ queryKey: ['assets', assetId] })}
      />
    );
  }

  return <AssetView asset={asset} />;
};
```

**Loading State Patterns:**

**Naming Conventions:**

- Query loading: `isLoading` (first fetch), `isFetching` (refetch)
- Mutation loading: `isPending` (TanStack Query v5)
- Component loading: `isSubmitting`, `isUploading`, `isProcessing`

**Loading UI Patterns:**

```typescript
// Skeleton loading for initial data fetch
if (isLoading) {
  return <AssetCardSkeleton />;
}

// Spinner overlay for mutations (don't block UI)
{isPending && <SpinnerOverlay />}

// Progress bar for uploads
<UploadProgressBar
  progress={uploadProgress}
  fileName={file.name}
  onCancel={cancelUpload}
/>

// Optimistic updates for immediate feedback
const mutation = useMutation({
  mutationFn: deleteAsset,
  onMutate: async (assetId) => {
    // Cancel outbound refetches
    await queryClient.cancelQueries({ queryKey: ['assets'] });

    // Snapshot previous value
    const previousAssets = queryClient.getQueryData(['assets']);

    // Optimistically update
    queryClient.setQueryData(['assets'], (old) =>
      old.filter(asset => asset.id !== assetId)
    );

    return { previousAssets };
  },
  onError: (err, assetId, context) => {
    // Rollback on error
    queryClient.setQueryData(['assets'], context.previousAssets);
  }
});
```

**Validation Patterns:**

**Backend Validation:**

- **Schema-level:** Pydantic validates types, required fields, formats
- **Business-level:** Service layer validates business rules

```python
class AssetCreate(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., gt=0, le=5_000_000_000)  # Max 5GB
    mime_type: str

    @field_validator('mime_type')
    def validate_mime_type(cls, v):
        allowed = ['application/pdf', 'video/mp4', 'application/zip']
        if v not in allowed:
            raise ValueError(f'MIME type {v} not allowed')
        return v

# Service layer business validation
class AssetService:
    async def create_asset(self, data: AssetCreate, user_id: UUID) -> Asset:
        # Check quota
        user_usage = await self._get_user_storage_usage(user_id)
        if user_usage + data.file_size_bytes > MAX_USER_QUOTA:
            raise QuotaExceededException(user_id, user_usage, MAX_USER_QUOTA)

        # Validate tenant access
        if not await self._validate_tenant_access(user_id, data.tenant_id):
            raise PermissionDeniedException(user_id, data.tenant_id)

        return await self._repository.create(data, user_id)
```

**Frontend Validation:**

- **Form-level:** React Hook Form with Zod schema validation
- **Real-time feedback:** Validate on blur, display errors inline

```typescript
const assetUploadSchema = z.object({
  file: z.instanceof(File)
    .refine((file) => file.size <= 5_000_000_000, "File must be under 5GB")
    .refine(
      (file) => ['application/pdf', 'video/mp4'].includes(file.type),
      "Only PDF and MP4 files allowed"
    ),
  description: z.string().min(1).max(500),
});

const UploadForm: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(assetUploadSchema)
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input {...register("description")} />
      {errors.description && <ErrorText>{errors.description.message}</ErrorText>}
    </form>
  );
};
```

## Enforcement Guidelines

**All AI Agents MUST:**

1. **Follow naming conventions exactly** - No exceptions for "readability" or "preference"
   - Database: snake_case, lowercase, plural tables
   - API: snake_case JSON, kebab-case URLs, plural resources
   - Python: snake_case functions/variables, PascalCase classes
   - TypeScript: camelCase variables/functions, PascalCase components/types

2. **Use established project structure** - Don't create new organizational patterns
   - Backend: routes → services → repositories → models
   - Frontend: Feature-based in routes/{feature}/
   - Tests mirror source structure in tests/ directory

3. **Return consistent API formats** - Use defined response schemas
   - Single resource: Direct object `{id, ...}`
   - Collections: Paginated `{items: [], total, page, page_size, total_pages}`
   - Errors: `{error_code, message, details, request_id, timestamp}`

4. **Handle errors uniformly** - Raise custom exceptions, use global handlers
   - Backend: Raise domain exceptions (AssetNotFoundException), handle globally
   - Frontend: Display API error messages, provide retry mechanisms

5. **Log with request IDs** - Every log entry must include request_id for tracing
   - Backend: Middleware injects request_id into request.state
   - Logs: JSON format `{"timestamp": ..., "level": ..., "request_id": ..., "message": ...}`

6. **Validate at boundaries** - Schema validation on API input, business validation in services
   - API layer: Pydantic validates types and formats
   - Service layer: Validates business rules (quotas, permissions)

7. **Use TanStack Query for server state** - No custom fetch wrappers or Context for server data
   - Queries: `useQuery` with hierarchical keys `['resource', filters]`
   - Mutations: `useMutation` with query invalidation on success

8. **Implement row-level security** - All tenant-specific queries must filter by tenant_id
   - Middleware injects user context
   - Repositories enforce tenant_id filtering
   - PostgreSQL RLS policies as backstop

9. **Generate signed URLs for storage access** - Never proxy files through API
   - Backend generates MinIO presigned URLs
   - Frontend uploads/downloads directly to/from MinIO
   - TTL: 15 min (upload), 1 hour (download)

10. **Write tests that mirror structure** - Test file location matches source file location
    - Backend: `tests/api/test_assets.py` for `app/api/routes/assets.py`
    - Frontend: `tests/components/AssetCard.test.tsx` for `src/routes/assets/components/AssetCard.tsx`

**Pattern Verification Process:**

1. **Pre-commit Hooks:**
   - Python: `ruff` linting enforces naming conventions
   - TypeScript: `prettier` + `eslint` enforce code style
   - Commit fails if violations detected

2. **Code Review Checklist:**
   - [ ] Naming conventions followed (database, API, code)
   - [ ] Project structure maintained (no new organizational patterns)
   - [ ] API responses match defined formats
   - [ ] Error handling uses standard patterns
   - [ ] Tests mirror source structure
   - [ ] Logging includes request_id
   - [ ] TanStack Query used for server state (no custom Context)

3. **CI/CD Validation:**
   - Backend tests run with coverage requirement (80% minimum)
   - Frontend tests run for all components
   - OpenAPI schema validated for consistency
   - Build fails if linting errors present

**Pattern Update Process:**

1. **Propose Change:** Create issue describing pattern conflict or improvement
2. **Discuss Trade-offs:** Team reviews impact on existing code
3. **Update Document:** Modify this architecture document if approved
4. **Migration Plan:** Define how to update existing code to new pattern
5. **Communicate:** Notify all developers and update project README

## Pattern Examples

**Good Examples:**

**Backend Route with Full Pattern Compliance:**

```python
# app/api/routes/assets.py
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from app.schemas.asset import AssetResponse, AssetCreate, PaginatedAssetList
from app.services.asset_service import AssetService
from app.api.deps import get_current_user, get_asset_service
from app.models.user import User

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])

@router.get("", response_model=PaginatedAssetList)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    service: AssetService = Depends(get_asset_service)
) -> PaginatedAssetList:
    """
    List assets for current user with pagination.

    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (max 100)
    - **sort_by**: Field to sort by
    - **order**: Sort order (asc/desc)
    """
    return await service.list_user_assets(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order
    )

@router.post("", response_model=AssetResponse, status_code=201)
async def create_asset(
    data: AssetCreate,
    current_user: User = Depends(get_current_user),
    service: AssetService = Depends(get_asset_service)
) -> AssetResponse:
    """Create a new asset."""
    return await service.create_asset(data, user_id=current_user.id)

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AssetService = Depends(get_asset_service)
) -> AssetResponse:
    """Get asset by ID."""
    return await service.get_asset(asset_id, user_id=current_user.id)
```

**Frontend Component with Full Pattern Compliance:**

```typescript
// src/routes/assets/components/AssetCard.tsx
import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { formatBytes, formatDate } from '@/lib/formatters';
import { deleteAsset } from '@/client/api';
import type { Asset } from '@/client/models';

interface IAssetCardProps {
  asset: Asset;
  onView: (assetId: string) => void;
}

export const AssetCard: React.FC<IAssetCardProps> = ({ asset, onView }) => {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => deleteAsset(asset.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      toast.success('Asset deleted successfully');
    },
    onError: (error) => {
      toast.error(`Failed to delete: ${error.message}`);
    }
  });

  const handleDeleteClick = () => {
    if (confirm(`Delete "${asset.file_name}"?`)) {
      deleteMutation.mutate();
    }
  };

  return (
    <Card>
      <CardContent>
        <h3 className="text-lg font-semibold">{asset.file_name}</h3>
        <p className="text-sm text-gray-600">
          {formatBytes(asset.file_size_bytes)} • {formatDate(asset.created_at)}
        </p>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button onClick={() => onView(asset.id)} variant="primary">
          View
        </Button>
        <Button
          onClick={handleDeleteClick}
          variant="destructive"
          disabled={deleteMutation.isPending}
        >
          {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        </Button>
      </CardFooter>
    </Card>
  );
};
```

**Anti-Patterns (What to Avoid):**

**❌ Inconsistent Naming:**

```python
# WRONG - Mixed naming conventions
class AssetRoutes: # Wrong: Should be in routes/ file, not class-based
    def GetAsset(self, AssetID): # Wrong: PascalCase function, parameter
        asset = db.query(Assets).filter(Assets.ID == AssetID) # Wrong: PascalCase table
        return {"AssetData": asset} # Wrong: PascalCase JSON key
```

**❌ Bypassing Service Layer:**

```python
# WRONG - Direct database access from route
@router.get("/assets/{asset_id}")
async def get_asset(asset_id: UUID, db: Session = Depends(get_db)):
    # Wrong: Routes should call services, not access DB directly
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    return asset

# CORRECT - Use service layer
@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AssetService = Depends(get_asset_service)
):
    return await service.get_asset(asset_id, user_id=current_user.id)
```

**❌ Custom Fetch Wrappers Instead of TanStack Query:**

```typescript
// WRONG - Custom data fetching
const [assets, setAssets] = useState<Asset[]>([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
  setLoading(true);
  fetchAssets().then(setAssets).finally(() => setLoading(false));
}, []);

// CORRECT - Use TanStack Query
const { data: assets, isLoading } = useQuery({
  queryKey: ['assets'],
  queryFn: fetchAssets
});
```

**❌ Inconsistent Error Responses:**

```python
# WRONG - Non-standard error format
raise HTTPException(
    status_code=404,
    detail="Not found" # Wrong: Should use structured error format
)

# CORRECT - Standard error format
raise AssetNotFoundException(asset_id) # Custom exception with standard format
```

**❌ Missing Tenant Filtering:**

```python
# WRONG - No tenant isolation
async def list_assets(self, user_id: UUID):
    return await self.db.query(Asset).filter(Asset.user_id == user_id).all()

# CORRECT - Enforce tenant filtering
async def list_assets(self, user_id: UUID, tenant_id: UUID):
    return await self.db.query(Asset).filter(
        Asset.user_id == user_id,
        Asset.tenant_id == tenant_id # Must filter by tenant
    ).all()
```

---

**These patterns ensure that when multiple AI agents implement features in parallel, their code integrates seamlessly without naming conflicts, structural inconsistencies, or behavioral incompatibilities.**
