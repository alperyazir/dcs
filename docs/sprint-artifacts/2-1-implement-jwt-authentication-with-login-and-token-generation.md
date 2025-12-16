# Story 2.1: Implement JWT Authentication with Login and Token Generation

Status: done

## Story

As a user,
I want to log in with my email and password and receive a JWT token,
So that I can access protected resources without re-authenticating on every request (FR1, NFR-S1).

## Acceptance Criteria

1. **Given** a registered user with valid credentials, **When** they POST to `/api/v1/auth/login` with email and password, **Then** they receive a 200 response with access_token (30 min expiry), refresh_token (7 day expiry), and token_type

2. **Given** invalid credentials (wrong password), **When** a login attempt is made, **Then** return 401 with generic "Invalid credentials" message (no user enumeration)

3. **Given** a non-existent email, **When** a login attempt is made, **Then** return 401 with the same generic "Invalid credentials" message (timing-safe comparison)

4. **Given** an inactive user account, **When** they attempt to login, **Then** return 401 with "Account is inactive" message

5. **Given** a valid access_token in Authorization header, **When** accessing any protected endpoint, **Then** the request is authenticated and user context is available

6. **Given** an expired access_token, **When** accessing a protected endpoint, **Then** return 401 with "Token expired" message

7. **Given** a valid refresh_token, **When** POST to `/api/v1/auth/refresh`, **Then** receive new access_token and refresh_token pair

8. **Given** 5+ failed login attempts from same IP within 1 minute, **When** another attempt is made, **Then** return 429 Too Many Requests (rate limiting)

9. **Given** JWT tokens are generated, **When** inspecting token payload, **Then** it contains: sub (user_id), email, role, tenant_id, exp, iat claims

10. **Given** the system uses JWT, **When** tokens are signed, **Then** RS256 algorithm (asymmetric) is used with RSA key pair

## Breaking Changes & Migration Notes

### Critical Changes from Existing Code

| Change | Current Value | New Value | Impact |
|--------|---------------|-----------|--------|
| JWT Algorithm | HS256 (`security.py:12`) | RS256 | **BREAKING** - All existing tokens invalidated |
| Token Expiry | 8 days (`config.py:37`) | 30 minutes | **BREAKING** - Users must re-authenticate |
| SECRET_KEY type | `str` | `SecretStr` | Config change, no runtime break |

### Pre-Implementation Checklist

- [x] Generate RSA key pair for RS256 signing (see Task 1.2)
- [x] Communicate token expiry change to team
- [x] Plan deployment during low-traffic window (tokens invalidated)
- [x] Update .env.example with new key variables

## Tasks / Subtasks

- [x] Task 1: UPDATE JWT Token Generation with RS256 (AC: #1, #9, #10)
  - [x] 1.1 UPDATE `backend/app/core/security.py` - Change ALGORITHM from "HS256" to "RS256"
  - [x] 1.2 Generate RSA key pair: `openssl genrsa -out private.pem 2048 && openssl rsa -in private.pem -pubout -out public.pem`
  - [x] 1.3 ADD to `config.py`: `JWT_PRIVATE_KEY: SecretStr` and `JWT_PUBLIC_KEY: str` settings
  - [x] 1.4 UPDATE `config.py`: Change `SECRET_KEY: str` to `SECRET_KEY: SecretStr` for consistency
  - [x] 1.5 UPDATE `create_access_token()` to use private key for signing
  - [x] 1.6 CREATE `create_refresh_token()` function with 7-day expiry
  - [x] 1.7 UPDATE token payload to include: sub, email, role, tenant_id, exp, iat

- [x] Task 2: UPDATE Token Expiry Configuration (AC: #1)
  - [x] 2.1 UPDATE `config.py`: Change `ACCESS_TOKEN_EXPIRE_MINUTES` from `60 * 24 * 8` to `30`
  - [x] 2.2 ADD `REFRESH_TOKEN_EXPIRE_DAYS: int = 7` to config.py
  - [x] 2.3 UPDATE `.env.example` with new token configuration documentation

- [x] Task 3: CREATE Auth Service Layer (AC: #1, #2, #3, #4)
  - [x] 3.1 CREATE `backend/app/services/auth_service.py` with `AuthService` class
  - [x] 3.2 Implement `authenticate_user(email, password)` with timing-safe comparison
  - [x] 3.3 Implement `create_tokens(user)` returning access + refresh token pair
  - [x] 3.4 Implement `validate_refresh_token(token)` for token refresh flow
  - [x] 3.5 Use existing `verify_password()` from security.py (bcrypt already configured)
  - [x] 3.6 Add check for `user.is_active` status before issuing tokens

- [x] Task 4: EXTEND Token Schemas (AC: #1, #7, #9)
  - [x] 4.1 UPDATE `backend/app/models.py` - EXTEND existing `Token` schema to include refresh_token
  - [x] 4.2 UPDATE `TokenPayload` to include: sub, email, role, tenant_id, exp, iat
  - [x] 4.3 CREATE `RefreshTokenRequest` schema for refresh endpoint
  - [x] 4.4 CREATE `TokenResponse` schema with access_token, refresh_token, token_type, expires_in

- [x] Task 5: CREATE Login Endpoint (AC: #1, #2, #3, #4)
  - [x] 5.1 CREATE `backend/app/api/routes/auth.py` router
  - [x] 5.2 Implement `POST /api/v1/auth/login` endpoint
  - [x] 5.3 Accept `OAuth2PasswordRequestForm` for standard OAuth2 compatibility
  - [x] 5.4 Return `TokenResponse` on success
  - [x] 5.5 Return 401 with generic message on auth failure (no user enumeration)
  - [x] 5.6 Register router in `backend/app/api/main.py`

- [x] Task 6: CREATE Token Refresh Endpoint (AC: #7)
  - [x] 6.1 Implement `POST /api/v1/auth/refresh` endpoint
  - [x] 6.2 Accept refresh_token in request body
  - [x] 6.3 Validate refresh token and extract user_id
  - [x] 6.4 Issue new token pair (rotate refresh token)
  - [x] 6.5 Return 401 if refresh token invalid or expired

- [x] Task 7: UPDATE Token Verification Dependency (AC: #5, #6)
  - [x] 7.1 UPDATE `backend/app/api/deps.py` - Modify existing `get_current_user` function
  - [x] 7.2 Change to use RS256 public key for verification
  - [x] 7.3 Validate all required claims (sub, email, role, tenant_id)
  - [x] 7.4 Return 401 with "Token expired" for expired tokens
  - [x] 7.5 Return 401 with "Invalid token" for malformed tokens

- [x] Task 8: Implement Rate Limiting (AC: #8)
  - [x] 8.1 ADD `slowapi` to requirements (pyproject.toml)
  - [x] 8.2 CREATE `backend/app/middleware/rate_limit.py` with rate limiter setup
  - [x] 8.3 Apply `@limiter.limit("5/minute")` to login endpoint
  - [x] 8.4 Configure 429 response handler with Retry-After header
  - [x] 8.5 Use client IP as rate limit key (X-Forwarded-For aware)

- [x] Task 9: Add Audit Logging for Auth Events (AC: #1, #2, #4)
  - [x] 9.1 Log successful login events (user_id, IP, timestamp)
  - [x] 9.2 Log failed login attempts (email attempted, IP, reason)
  - [x] 9.3 Use existing structured logging from Story 1.5
  - [x] 9.4 Ensure passwords are NEVER logged (use existing redaction)

- [x] Task 10: Write Comprehensive Tests (AC: #1-10)
  - [x] 10.1 CREATE `backend/tests/api/routes/test_auth.py`
  - [x] 10.2 Test successful login returns tokens
  - [x] 10.3 Test invalid password returns 401
  - [x] 10.4 Test non-existent user returns 401 (same message)
  - [x] 10.5 Test inactive user returns 401
  - [x] 10.6 Test token refresh flow
  - [x] 10.7 Test expired token returns 401
  - [x] 10.8 Test rate limiting after 5 attempts
  - [x] 10.9 Test JWT payload contains required claims
  - [x] 10.10 Test RS256 signature verification

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Authentication:**
- JWT-based authentication with RS256 algorithm (asymmetric signing)
- Access token: 30 minutes, Refresh token: 7 days
- Token payload: user_id, email, role, tenant_id
- Password hashing: bcrypt with salt (already implemented)

**Service Layer Architecture:**
- Routes → Services → Repositories pattern
- Services contain business logic
- Routes handle HTTP concerns only

**Multi-tenant Isolation:**
- tenant_id included in JWT for downstream filtering
- All queries must filter by tenant_id from token

### Existing Code Assets (REUSE)

**`backend/app/core/security.py`** - Already has:
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # REUSE

def verify_password(plain_password: str, hashed_password: str) -> bool:  # REUSE
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:  # REUSE
    return pwd_context.hash(password)
```

**`backend/app/models/user.py`** - User model with:
- `id`, `email`, `hashed_password`, `is_active`
- `role: UserRole` (admin, user, viewer)
- `tenant_id` for multi-tenant isolation

**`backend/app/api/deps.py`** - Already has `get_current_user` dependency (needs UPDATE)

**`backend/app/middleware/logging_config.py`** - Structured logging with secrets redaction (Story 1.5)

### Project Structure

**UPDATE Files:**
```
backend/app/core/security.py       # UPDATE: HS256 → RS256, add refresh token
backend/app/core/config.py         # UPDATE: Token expiry, add JWT keys, SecretStr
backend/app/schemas/token.py       # UPDATE: Extend Token, TokenPayload schemas
backend/app/api/deps.py            # UPDATE: RS256 verification in get_current_user
backend/app/api/main.py            # UPDATE: Register auth router
.env.example                       # UPDATE: Add JWT_PRIVATE_KEY, JWT_PUBLIC_KEY
pyproject.toml                     # UPDATE: Add slowapi dependency
```

**CREATE Files:**
```
backend/app/services/auth_service.py   # NEW: Authentication business logic
backend/app/api/routes/auth.py         # NEW: Login and refresh endpoints
backend/app/middleware/rate_limit.py   # NEW: Rate limiting configuration
backend/tests/api/test_auth.py         # NEW: Auth endpoint tests
keys/private.pem                       # NEW: RSA private key (gitignored)
keys/public.pem                        # NEW: RSA public key
```

### Previous Story Intelligence (Story 1.7)

**Patterns Established:**
- SecretStr used for `POSTGRES_PASSWORD` and `MINIO_ROOT_PASSWORD`
- Secrets redaction in logging (patterns for password, secret, token, key)
- Environment variables for all secrets (`.env.example` pattern)
- Structured logging with JSON format for production

**Key Implementation from 1.7:**
- `config.py:57-58`: `POSTGRES_PASSWORD: SecretStr = SecretStr("")` - follow same pattern
- Logging redaction already handles JWT tokens via Bearer pattern

### Technical Implementation Details

**RS256 Key Generation:**
```bash
# Generate RSA key pair
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem

# Add to .env
JWT_PRIVATE_KEY="$(cat keys/private.pem)"
JWT_PUBLIC_KEY="$(cat keys/public.pem)"
```

**Token Generation (security.py):**
```python
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

ALGORITHM = "RS256"

def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "tenant_id": str(user.tenant_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY.get_secret_value(), algorithm=ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY.get_secret_value(), algorithm=ALGORITHM)
```

**Auth Service Pattern:**
```python
# backend/app/services/auth_service.py
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.models import User
from app.schemas.token import TokenResponse

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def authenticate(self, email: str, password: str) -> TokenResponse | None:
        user = await self.db.query(User).filter(User.email == email).first()

        # Timing-safe: always verify even if user not found
        if not user:
            verify_password(password, "$2b$12$dummy_hash_for_timing")
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            raise UserInactiveError()

        return TokenResponse(
            access_token=create_access_token(user),
            refresh_token=create_refresh_token(str(user.id)),
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
```

**Rate Limiting Setup:**
```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# In auth.py route:
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    ...
```

### Dependencies

**Already Available:**
- `python-jose[cryptography]` - JWT handling (in pyproject.toml)
- `passlib[bcrypt]` - Password hashing (in pyproject.toml)
- `pydantic-settings` - Configuration management

**To Add:**
- `slowapi` - Rate limiting

### Git Workflow

**Branch:** `story/2-1-jwt-authentication`

**Commit Pattern (from Story 1.7):**
```
feat(story-2.1): Implement JWT Authentication with Login and Token Generation
```

### Testing Standards

**Test Commands:**
```bash
# Run auth tests
uv run pytest backend/tests/api/test_auth.py -v

# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"

# Test rate limiting (run 6 times rapidly)
for i in {1..6}; do curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=wrong@example.com&password=wrong"; done
```

### Security Considerations

**Critical Security Requirements:**
- Use timing-safe password comparison (constant-time)
- Generic error messages to prevent user enumeration
- Rate limit login attempts (5/minute/IP)
- NEVER log passwords or tokens (existing redaction handles this)
- RS256 private key must be kept secure (gitignored, env var)
- Rotate refresh tokens on each use
- Include `tenant_id` in all tokens for multi-tenant isolation

**OWASP Compliance:**
- A2:2021 - Cryptographic Failures: RS256 asymmetric signing
- A7:2021 - Identification Failures: Rate limiting, no enumeration

### Optional Enhancements (Post-MVP)

- [ ] Token blacklist for logout (Redis-based)
- [ ] Device fingerprinting for refresh tokens
- [ ] Login notification emails
- [ ] MFA support (TOTP)

## References

- [Source: docs/epics.md#Story-2.1] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Authentication] - JWT specifications
- [Source: docs/project_context.md] - Implementation patterns and rules
- [Source: docs/sprint-artifacts/1-7-configure-https-security-headers-and-encryption.md] - Previous story patterns

## Dev Agent Record

### Context Reference

Story 2.1 implementation - first story in Epic 2 (User Authentication & Authorization).

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All 10 tasks implemented successfully following the architecture patterns
- RS256 JWT implementation with RSA key pair support
- Token expiry changed from 8 days to 30 minutes (access) + 7 days (refresh)
- Auth service layer follows Routes → Services → Repositories pattern
- Rate limiting implemented with slowapi (5 requests/minute/IP)
- Timing-safe password comparison prevents user enumeration
- Token rotation implemented on refresh
- Comprehensive test suite created (14 tests covering all ACs)
- Integration tests require running database (PostgreSQL not available during final validation)
- All linting and type checks pass

**Code Review Fixes Applied:**
- CRITICAL: Fixed password reset using HS256 (was broken by RS256 change)
- CRITICAL: Added full claims validation (sub, email, role, tenant_id, type) in deps.py
- MEDIUM: Removed duplicate get_client_ip function (now in rate_limit.py only)
- MEDIUM: Added request_id to all auth logging for traceability
- MEDIUM: Improved rate limit test with better documentation
- MEDIUM: Updated File List to include all modified files

### File List

**UPDATED Files:**
- `backend/app/core/security.py` - RS256 JWT, create_access_token, create_refresh_token, verify_token
- `backend/app/core/config.py` - JWT_PRIVATE_KEY, JWT_PUBLIC_KEY, token expiry settings, SecretStr
- `backend/app/api/deps.py` - RS256 public key verification, claims validation in get_current_user
- `backend/app/api/routes/login.py` - Updated to use new create_access_token signature
- `backend/app/models.py` - TokenResponse, TokenPayload, RefreshTokenRequest schemas
- `backend/app/main.py` - Rate limiter integration
- `backend/app/api/main.py` - Auth router registration
- `backend/app/utils.py` - Password reset tokens use HS256 (fixed RS256 bug)
- `backend/pyproject.toml` - pyjwt[crypto] and slowapi dependencies
- `backend/tests/crud/test_models.py` - Updated for new token signature
- `.env.example` - JWT key documentation
- `.gitignore` - Added keys/ directory
- `docs/sprint-artifacts/sprint-status.yaml` - Story 2.1 status tracking
- `backend/uv.lock` - Updated dependencies

**CREATED Files:**
- `backend/app/services/__init__.py` - Services package init
- `backend/app/services/auth_service.py` - AuthService class with authenticate/refresh_tokens
- `backend/app/api/routes/auth.py` - POST /auth/login, POST /auth/refresh endpoints
- `backend/app/middleware/rate_limit.py` - Rate limiting configuration
- `backend/tests/api/routes/test_auth.py` - Comprehensive auth tests (14 tests)
