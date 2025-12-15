# Story 1.1: Initialize Project from FastAPI Full Stack Template

Status: Done

## Story

As a developer,
I want to initialize the project from the Official FastAPI Full Stack Template,
so that I have a production-ready foundation with all necessary tooling configured.

## Acceptance Criteria

**Given** I have Python, Node.js, and Docker installed on my development machine
**When** I run the copier command with the FastAPI full-stack template
**Then** the project structure is generated with backend/ and frontend/ directories
**And** the configuration includes project_name="Dream Central Storage" and stack_name="dream-central-storage"
**And** Docker Compose files are present with service definitions for backend, frontend, and PostgreSQL
**And** the project includes pre-commit hooks configured with ruff and prettier
**And** environment configuration files (.env.example) are present with all required variables
**And** I can run `docker-compose up` and see all services starting without errors

## Tasks / Subtasks

- [x] Install copier and initialize project from template (AC: 1)
  - [x] Install copier: `pip install copier`
  - [x] Run template generation: `copier copy https://github.com/fastapi/full-stack-fastapi-template .` (generated into existing directory)
  - [x] Configure template prompts with project-specific values

- [x] Verify project structure generation (AC: 2, 3)
  - [x] Confirm backend/ directory with FastAPI structure
  - [x] Confirm frontend/ directory with React + TypeScript structure
  - [x] Verify docker-compose.yml with backend, frontend, db services

- [x] Configure environment variables (AC: 6)
  - [x] Review .env.example file
  - [x] Create .env file with development values
  - [x] Ensure secure secret_key generation (64-char hex via openssl rand -hex 32)
  - [x] Set postgres_password (secure random via openssl rand -hex 16)
  - [x] Configure first_superuser email (admin@example.com)

- [x] Verify development environment startup (AC: 7)
  - [x] Run `docker-compose up`
  - [x] Confirm PostgreSQL starts successfully (port 5433 externally to avoid LMS conflict)
  - [x] Confirm backend API starts on expected port (8000)
  - [x] Confirm frontend dev server starts (5173)
  - [x] Access API docs at /docs to verify OpenAPI generation (HTTP 200)

- [x] Verify pre-commit hooks (AC: 5)
  - [x] Confirm .pre-commit-config.yaml exists
  - [x] Install hooks: `pre-commit install`
  - [x] Test ruff (Python linting) - All checks passed
  - [x] Test biome (TypeScript/JavaScript formatting - replaced prettier in template)

## Dev Notes

### ⚠️ GIT WORKFLOW - READ BEFORE STARTING

**MANDATORY: Create Feature Branch Before Implementation**

```bash
# 1. Check for uncommitted changes in current directory
git status

# 2. If changes exist, commit them first
git add . && git commit -m "Prepare for Story 1.1"

# 3. Ensure you're on main branch
git checkout main

# 4. Create feature branch for this story
git checkout -b story/1-1-initialize-template

# 5. Verify branch
git branch --show-current  # Should show: story/1-1-initialize-template

# 6. NOW you can start implementation
```

**Branch Naming:** `story/1-1-initialize-template`
**Full Workflow Guide:** See `/docs/GIT-WORKFLOW.md`

**After Story Completion:**
- Push branch: `git push -u origin story/1-1-initialize-template`
- Create PR or merge to main
- Delete feature branch after merge

---

### 🎯 Critical Success Factors

**This is Story 1.1 - the foundation for the entire project. Everything else depends on getting this right!**

**Zero Deviation from Template:**
- Do NOT modify the template structure during initialization
- Accept the starter template's architecture decisions
- Customizations come in later stories, not this one
- Template provides production-ready patterns - trust them

**Configuration Values (EXACTLY as specified):**
```
project_name: Dream Central Storage
stack_name: dream-central-storage
first_superuser: admin@example.com (change in production)
```

### 📋 Architecture Compliance

**From Architecture Document:** [Source: docs/architecture/starter-template-evaluation.md]

**Selected Template:**
- **Repository:** https://github.com/fastapi/full-stack-fastapi-template
- **Maintained by:** Sebastián Ramírez (FastAPI creator)
- **Why Selected:**
  - Official support ensuring framework best practices
  - Production-ready (HTTPS, CI/CD, monitoring included)
  - Modern tooling (uv package manager, Pydantic V2)
  - Pre-integrated shadcn/ui (matches UX requirements)
  - Active maintenance with regular updates

**Template Provides These Architectural Decisions:**
[Source: docs/architecture/starter-template-evaluation.md#architectural-decisions-provided-by-starter]

1. **Language & Runtime:**
   - Python 3.11+ with type hints and async/await
   - TypeScript with strict mode
   - Node.js 20+ for frontend builds
   - Pydantic V2 for validation

2. **Backend Stack:**
   - FastAPI with automatic OpenAPI docs
   - SQLModel (SQLAlchemy 2.0 + Pydantic)
   - Alembic for migrations
   - Dependency injection for auth/db
   - Layered architecture: routes → services → CRUD → models

3. **Frontend Stack:**
   - React 18+ with TypeScript
   - Vite for fast builds
   - React Router for routing
   - TanStack Query for server state
   - Tailwind CSS + shadcn/ui
   - OpenAPI TypeScript client generation

4. **Development Experience:**
   - Hot reloading (FastAPI auto-reload + Vite HMR)
   - Pre-commit hooks (ruff + prettier)
   - Docker Compose one-command setup
   - VSCode settings included

5. **Security (Pre-configured):**
   - JWT tokens with RS256
   - bcrypt password hashing
   - CORS middleware
   - RBAC structure ready

6. **Project Structure Generated:**
```
project-root/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes and dependencies
│   │   ├── core/             # Config, DB, security
│   │   ├── models/           # SQLModel ORM models
│   │   ├── schemas/          # Pydantic request/response
│   │   ├── crud/             # Database operations
│   │   └── main.py           # FastAPI initialization
│   ├── alembic/              # DB migrations
│   ├── tests/                # Pytest suites
│   └── Dockerfile            # Multi-stage build
├── frontend/
│   ├── src/
│   │   ├── components/ui/    # shadcn/ui components
│   │   ├── hooks/            # Custom hooks
│   │   ├── routes/           # Page components
│   │   ├── client/           # Auto-generated API client
│   │   └── main.tsx          # Entry point
│   ├── Dockerfile            # Multi-stage build
│   └── vite.config.ts        # Vite config
├── docker-compose.yml        # Service orchestration
└── .env                      # Environment variables
```

### 🚀 Technical Requirements

**Prerequisites (Verify Before Starting):**
```bash
# Python 3.11 or higher
python --version  # Should be 3.11+

# Node.js 20 or higher
node --version    # Should be 20+

# Docker and Docker Compose
docker --version
docker-compose --version

# Git (for version control)
git --version
```

**Installation Steps (Follow Exactly):**

```bash
# 1. Install copier
pip install copier

# 2. IMPORTANT: Navigate to the project directory
cd /Users/alperyazir/Dev/dream-central-storage

# 3. Generate project from template INTO CURRENT DIRECTORY
#    NOTE: Use "." to generate into existing directory
#    The template will add backend/, frontend/, docker-compose.yml etc.
#    Existing files (docs/, .gitignore) will be preserved
copier copy https://github.com/fastapi/full-stack-fastapi-template .

# 4. Template will prompt for configuration - use these values:
#    project_name: Dream Central Storage
#    stack_name: dream-central-storage
#    secret_key: [Generate using: openssl rand -hex 32]
#    first_superuser: admin@example.com
#    first_superuser_password: [Secure password for local dev]
#    postgres_password: [Secure password]
#
# 5. After generation, cd into project
cd dream-central-storage

# 6. Review generated .env file and adjust if needed
cat .env

# 7. Start development environment
docker-compose up

# 8. Wait for all services to start, then verify:
#    - Backend API: http://localhost:8000/docs
#    - Frontend: http://localhost:5173
#    - PostgreSQL: Running in container

# 9. Stop services (Ctrl+C) and install pre-commit hooks
pre-commit install
```

**Verification Checklist:**

After completion, verify these conditions:

```bash
# Directory structure exists
ls -la backend/app/api backend/app/models frontend/src

# Docker Compose services defined
grep -E "(backend|frontend|db):" docker-compose.yml

# Environment file exists
test -f .env && echo "✓ .env exists"

# Pre-commit config exists
test -f .pre-commit-config.yaml && echo "✓ Pre-commit configured"

# Services start successfully
docker-compose up -d
docker-compose ps  # All should show "Up" status
docker-compose logs backend | grep "Application startup complete"
docker-compose logs frontend | grep "ready in"
docker-compose down
```

### 🛡️ Common Pitfalls to Avoid

**DO NOT:**
- ❌ Modify the generated structure during this story
- ❌ Skip the Docker Compose verification step
- ❌ Use weak passwords for local development (establish good habits)
- ❌ Commit .env file to git (already in .gitignore, verify)
- ❌ Proceed to next story if `docker-compose up` fails

**DO:**
- ✅ Use the exact project_name and stack_name specified
- ✅ Generate a proper secret_key (use openssl rand -hex 32)
- ✅ Test pre-commit hooks after installation
- ✅ Verify API docs are accessible at /docs
- ✅ Keep all default configurations from template (customize later)

### 📊 Expected Outcomes

**Files Created by Template:**
- ~50+ files across backend and frontend
- Complete Docker Compose configuration
- CI/CD GitHub Actions workflows
- Pre-commit hook configuration
- Alembic migration setup
- pytest and Vitest test configurations

**Services Available After `docker-compose up`:**
- **Backend API:** http://localhost:8000
  - OpenAPI docs: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc
- **Frontend:** http://localhost:5173
- **PostgreSQL:** localhost:5432 (internal to Docker network)

**What's NOT in This Story:**
- MinIO configuration (Story 1.2)
- Custom database models (Story 1.3)
- Custom API endpoints (Later stories)
- Frontend customization (Epic 9)

### 🔗 References

**Template Documentation:**
- Official Repo: https://github.com/fastapi/full-stack-fastapi-template
- FastAPI Docs: https://fastapi.tiangolo.com/
- Template includes README with detailed setup instructions

**Architecture References:**
- [Source: docs/architecture/starter-template-evaluation.md] - Complete rationale for template selection
- [Source: docs/architecture/core-architectural-decisions.md] - How template decisions align with project needs

**Related Epic Context:**
- **Epic 1 Goal:** Developers have a running, production-ready platform to start integrating with
- **This Story:** Provides the foundation - everything else builds on this
- **Next Story (1.2):** Add MinIO and Traefik to the Docker Compose setup

### 🧪 Testing Requirements

**Manual Testing (This Story):**
```bash
# Test 1: Template generation succeeds
copier copy https://github.com/fastapi/full-stack-fastapi-template dream-central-storage
# Expected: Interactive prompts appear, project generates without errors

# Test 2: All services start
docker-compose up
# Expected: backend, frontend, db all show healthy status

# Test 3: API documentation accessible
curl http://localhost:8000/docs
# Expected: HTTP 200, Swagger UI loads

# Test 4: Frontend loads
curl http://localhost:5173
# Expected: HTTP 200, React app loads

# Test 5: Pre-commit hooks work
echo "test file" > test.py
pre-commit run --all-files
# Expected: ruff runs on Python files, prettier on TypeScript files
```

**Automated Testing:**
- Template includes pytest configuration
- Template includes Vitest configuration
- Run tests: `docker-compose run backend pytest`
- Run tests: `docker-compose run frontend npm test`
- Both should pass with default template tests

### 💡 Developer Context - Read This First!

**Why This Story Exists:**

The FastAPI Full Stack Template provides a battle-tested, production-ready foundation that would take weeks to assemble manually. It includes:
- Security best practices (JWT, password hashing, CORS)
- Development productivity (hot reload, type safety, auto-generated API client)
- Production features (Docker, CI/CD, health checks, migrations)
- Modern tooling (uv, Vite, TanStack Query, shadcn/ui)

**Your Job in This Story:**
1. Run the copier command with correct configuration values
2. Verify everything starts successfully
3. DO NOT modify anything yet - that comes in later stories
4. Confirm the foundation is solid before building on it

**Success Criteria:**
- All Docker services start without errors
- API docs are accessible at /docs
- Frontend loads in browser
- Pre-commit hooks are functional
- You understand the project structure

**Time Estimate:** 30-60 minutes (including Docker image downloads)

**Blockers/Dependencies:**
- None - this is the first story
- Requires working internet connection for template download
- Requires working Docker installation

## Dev Agent Record

### Context Reference

<!-- Story context created by SM create-story workflow -->
<!-- All architectural requirements and constraints documented above -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

**Issues Encountered & Resolved:**

1. **Port Conflict (5432):** PostgreSQL port 5432 was already in use by LMS application.
   - **Resolution:** Modified `docker-compose.override.yml` to map external port to 5433 (`5433:5432`)

2. **Python Version Mismatch:** Backend Dockerfile used Python 3.10, but code uses `datetime.UTC` (Python 3.11+)
   - **Resolution:** Updated `backend/Dockerfile` from `python:3.10` to `python:3.11`

3. **Copier Template .git Conflict:** Initial copier run modified .git directory, causing detached HEAD
   - **Resolution:** Used `--exclude .git` flag on subsequent copier run

### Completion Notes List

_Implementation completed successfully:_
- [x] Template initialized successfully (FastAPI Full Stack Template v0.9.0)
- [x] All services verified running (db, backend, frontend, proxy, adminer, mailcatcher)
- [x] API documentation accessible at http://localhost:8000/docs (HTTP 200)
- [x] Pre-commit hooks installed and tested (ruff for Python, biome for TypeScript)
- [x] .env file configured with secure secrets (openssl rand generated keys)
- [x] Project structure matches expected layout
- [x] All 55 backend tests pass (pytest)
- [x] Feature branch created: `story/1-1-initialize-template`

### File List

**Key files created/modified by template and implementation:**

**Configuration:**
- .env (environment variables with secure secrets)
- .pre-commit-config.yaml (ruff + biome hooks)
- docker-compose.yml (service orchestration)
- docker-compose.override.yml (local dev config, PostgreSQL port 5433)
- .gitignore (updated by template)
- .copier/.copier-answers.yml (copier configuration)

**Backend:**
- backend/Dockerfile (Python 3.11)
- backend/app/main.py (FastAPI entry point)
- backend/app/api/main.py (API router)
- backend/app/api/routes/ (login, users, items, utils, private)
- backend/app/core/ (config, db, security)
- backend/app/models.py (SQLModel ORM)
- backend/app/crud.py (database operations)
- backend/app/alembic/ (migrations)
- backend/tests/ (55 tests)
- backend/pyproject.toml (uv package config)

**Frontend:**
- frontend/src/main.tsx (React entry point)
- frontend/src/components/ (UI, Admin, Items, UserSettings, etc.)
- frontend/src/routes/ (TanStack Router pages)
- frontend/src/client/ (Auto-generated OpenAPI client)
- frontend/src/hooks/ (useAuth, useCustomToast, etc.)
- frontend/package.json (npm dependencies)
- frontend/Dockerfile (multi-stage build)
- frontend/biome.json (linting config)

**CI/CD:**
- .github/workflows/ (test-backend, lint-backend, playwright, deploy, etc.)

**Documentation:**
- README.md (template documentation)
- development.md (local development guide)
- deployment.md (production deployment guide)

_(Template created 150+ files total)_

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story 1.1 implementation complete | Claude Opus 4.5 |
