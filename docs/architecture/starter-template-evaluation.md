# Starter Template Evaluation

## Technical Preferences Established

**Technology Stack:**
- **Backend:** Python 3.11+ with FastAPI
- **Frontend:** React with TypeScript
- **Database:** PostgreSQL with SQLModel ORM
- **Object Storage:** MinIO (S3-compatible)
- **Project Structure:** Monorepo (backend + frontend)
- **Containerization:** Docker + Docker Compose
- **Deployment Target:** VPS (flexible cloud provider)

## Primary Technology Domain

**Full-stack platform** (API backend + admin/user frontend) based on project requirements analysis.

The system architecture consists of:
- **Storage Layer:** MinIO for binary object storage
- **API Layer:** FastAPI for RESTful services
- **Database Layer:** PostgreSQL for metadata and business logic
- **Frontend Layer:** React for admin and user interfaces

## Starter Options Considered

**1. Official FastAPI Full Stack Template** ⭐ Selected
- Repository: https://github.com/fastapi/full-stack-fastapi-template
- Maintained by: FastAPI creator (Sebastián Ramírez)
- Last updated: Actively maintained (2025)
- Stack: FastAPI + React + SQLModel + PostgreSQL + Docker + shadcn/ui

**2. FastAPI React Cookiecutter (Buuntu)**
- SQLAlchemy out-of-the-box but less actively maintained
- Older React patterns

**3. Monorepo Template (jacobwillemsma)**
- Simpler structure, less comprehensive than official template

## Selected Starter: Official FastAPI Full Stack Template

**Rationale for Selection:**

1. **Official Support:** Maintained by FastAPI creator, ensuring alignment with framework best practices
2. **Production-Ready:** Includes comprehensive production features (HTTPS, CI/CD, monitoring)
3. **Modern Tooling:** Uses latest Python tooling (uv package manager, Pydantic V2)
4. **Component Library:** Pre-integrated with shadcn/ui (matches PRD requirements)
5. **Docker-First:** Complete Docker Compose setup for development and production
6. **Monorepo Structure:** Clear separation between backend and frontend with shared configuration
7. **Active Maintenance:** Regular updates and community support
8. **SQLModel Integration:** Combines SQLAlchemy power with Pydantic validation seamlessly

**Initialization Command:**

```bash
# Install copier (template generator)
pip install copier

# Generate project from template
copier copy https://github.com/fastapi/full-stack-fastapi-template dream-central-storage

# Follow interactive prompts to configure:
# - project_name: Dream Central Storage
# - stack_name: dream-central-storage
# - secret_key: (generate secure key)
# - first_superuser: admin@dreamcentral.com
# - postgres_password: (secure password)
```

## Architectural Decisions Provided by Starter

**Language & Runtime:**
- **Python 3.11+** with type hints and async/await patterns
- **TypeScript** for frontend with strict mode enabled
- **Node.js 20+** for frontend build tooling
- **Pydantic V2** for data validation and settings management

**Backend Framework & Structure:**
- **FastAPI** with automatic OpenAPI documentation
- **SQLModel** for database operations (combines SQLAlchemy + Pydantic)
- **Alembic** for database migrations
- **Dependency injection** pattern for database sessions and authentication
- **Layered architecture:** routes → services → CRUD → models

**Frontend Framework & Styling:**
- **React 18+** with TypeScript and hooks
- **Vite** for fast development and optimized production builds
- **React Router** for client-side routing
- **TanStack Query** for server state management and caching
- **Tailwind CSS** for utility-first styling
- **shadcn/ui** component library for consistent UI
- **OpenAPI TypeScript generator** for type-safe API client

**Build Tooling:**
- **uv** for Python package management (faster than pip)
- **Vite** for frontend bundling and hot module replacement
- **ESBuild** for TypeScript compilation
- **PostCSS** with Tailwind CSS processing
- **Multi-stage Docker builds** for optimized images

**Testing Framework:**
- **pytest** for backend testing with async support
- **pytest-cov** for code coverage reporting
- **httpx** for async HTTP client testing
- **Vitest** for frontend unit testing
- **Testing Library** for React component testing

**Code Organization:**

**Backend Structure:**
```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py           # Dependency injection (auth, db session)
│   │   ├── main.py           # API router aggregation
│   │   └── routes/           # Endpoint modules
│   ├── core/
│   │   ├── config.py         # Pydantic settings from environment
│   │   ├── db.py             # Database engine and session
│   │   └── security.py       # JWT, password hashing
│   ├── models/               # SQLModel ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── crud/                 # Database CRUD operations
│   └── main.py               # FastAPI app initialization
├── alembic/                  # Database migration scripts
├── tests/                    # Pytest test suites
└── Dockerfile                # Multi-stage Docker build
```

**Frontend Structure:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   └── Common/           # Shared app components
│   ├── hooks/                # Custom React hooks
│   ├── routes/               # Page components
│   │   ├── _layout/          # Layout components
│   │   └── [feature]/        # Feature-specific routes
│   ├── client/               # Auto-generated API client
│   ├── lib/                  # Utilities
│   └── main.tsx              # React entry point
├── Dockerfile                # Multi-stage Docker build
└── vite.config.ts            # Vite configuration
```

**Project Root:**
```
docker-compose.yml            # Development environment
docker-compose.override.yml   # Local overrides
.env                          # Environment variables
```

**Development Experience:**
- **Hot reloading** for both backend (FastAPI auto-reload) and frontend (Vite HMR)
- **TypeScript strict mode** for type safety across frontend and API client
- **Pre-commit hooks** with ruff (Python linting) and prettier (JS/TS formatting)
- **Docker Compose** for one-command local development setup
- **VSCode settings** included for consistent editor experience

**Security & Authentication:**
- **JWT tokens** with RS256 signing algorithm
- **Password hashing** with bcrypt
- **CORS middleware** with configurable origins
- **API key authentication** option for service-to-service
- **Role-based access control** structure ready for extension

**Database & ORM:**
- **SQLModel** for models (combines SQLAlchemy 2.0 + Pydantic)
- **Async database operations** with asyncio support
- **Alembic migrations** with auto-generation support
- **Connection pooling** configured for production
- **PostgreSQL-specific features** supported (JSON columns, full-text search)

**API Documentation:**
- **Automatic OpenAPI/Swagger** documentation at `/docs`
- **ReDoc** alternative documentation at `/redoc`
- **TypeScript client generation** from OpenAPI spec for type-safe frontend calls

**Deployment & DevOps:**
- **Multi-stage Docker builds** to minimize image size
- **Docker Compose** for orchestration
- **Health check endpoints** for monitoring
- **GitHub Actions workflows** for CI/CD (testing, building, deploying)
- **Traefik** configuration for automatic HTTPS with Let's Encrypt

**Environment Configuration:**
- **Pydantic Settings** for type-safe configuration
- **Environment variables** for secrets and deployment-specific config
- **Separate configs** for development, testing, production
- **`.env` file support** for local development

**Note:** Project initialization using this template should be the first implementation story in the epic breakdown.
