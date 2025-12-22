# Stage 1: Dependencies
FROM python:3.14-slim AS deps

ENV PYTHONUNBUFFERED=1
WORKDIR /app/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1

# Use copy mode for uv
ENV UV_LINK_MODE=copy

# Install dependencies only (no project)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Stage 2: Production
FROM python:3.14-slim AS production

# Install curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
WORKDIR /app/

# Copy virtual environment from deps stage
COPY --from=deps /app/.venv /app/.venv

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy only necessary application files
COPY ./pyproject.toml ./uv.lock ./alembic.ini /app/
COPY ./scripts /app/scripts
COPY ./app /app/app

# Install uv for running scripts (minimal)
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /bin/

# Sync project (installs the app package)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
