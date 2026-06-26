# =============================================================================
# Velora Backend — Multi-Stage Production Dockerfile
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: dependency builder
# Installs all Python packages into a clean /install prefix.
# The final image copies only /install — no build tools included.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install Poetry
ENV POETRY_VERSION=1.8.4
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV_IN_PROJECT=false
ENV POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Copy dependency manifests first (layer cache)
COPY pyproject.toml poetry.lock* ./

# Export to requirements.txt then install to /install
RUN /opt/poetry/bin/poetry export --without-hashes --without dev -f requirements.txt \
    | pip install --no-cache-dir --prefix=/install -r /dev/stdin

# ---------------------------------------------------------------------------
# Stage 2: runtime image
# Minimal final image — no build tools, no Poetry, no source.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Security: run as non-root
RUN groupadd --gid 1001 velora && \
    useradd --uid 1001 --gid velora --no-create-home velora

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=velora:velora app/ ./app/
COPY --chown=velora:velora alembic/ ./alembic/
COPY --chown=velora:velora alembic.ini ./

USER velora

# Expose the application port
EXPOSE 8000

# Health check — uses the liveness endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health/live').raise_for_status()"

# Production entrypoint — 2 workers, no --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
