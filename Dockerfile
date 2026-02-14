# ──────────────────────────────────────────────────────────────
# Fleet Management System — Production Dockerfile
# Multi-stage build for minimal image size
# ──────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

# Copy project files
COPY pyproject.toml MANIFEST.in README.md LICENSE NOTICE requirements.txt ./
COPY config/ config/
COPY models/ models/
COPY api/ api/
COPY telematics/ telematics/
COPY services/ services/
COPY templates/ templates/
COPY main.py cli.py __init__.py ./

# Build the wheel package
RUN python -m build --wheel --outdir /build/dist


# ── Stage 2: Production Runtime ──────────────────────────────
FROM python:3.12-slim AS production

LABEL maintainer="Santosh Kumar <santoshiimind@users.noreply.github.com>"
LABEL description="Fleet Management System — Automotive Telematics"
LABEL version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/santoshiimind/fleet-management-system"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Create non-root user for security
RUN groupadd -r fleetmgr && useradd -r -g fleetmgr -m -d /app fleetmgr

WORKDIR /app

# Install production dependencies + the built package
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl gunicorn && \
    rm -rf /tmp/*.whl

# Copy application code (needed at runtime for the app)
COPY --chown=fleetmgr:fleetmgr config/ config/
COPY --chown=fleetmgr:fleetmgr models/ models/
COPY --chown=fleetmgr:fleetmgr api/ api/
COPY --chown=fleetmgr:fleetmgr telematics/ telematics/
COPY --chown=fleetmgr:fleetmgr services/ services/
COPY --chown=fleetmgr:fleetmgr templates/ templates/
COPY --chown=fleetmgr:fleetmgr main.py cli.py __init__.py ./
COPY --chown=fleetmgr:fleetmgr gunicorn_config.py ./

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R fleetmgr:fleetmgr /app/data

# Environment variables — production defaults
ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_DEBUG=false \
    API_SECRET_KEY=change-this-in-production \
    DB_DB_URL=sqlite:///data/fleet.db \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import requests; r=requests.get('http://localhost:8000/health'); exit(0 if r.json()['status']=='healthy' else 1)"

# Expose port
EXPOSE 8000

# Switch to non-root user
USER fleetmgr

# Production entrypoint using gunicorn + uvicorn workers
CMD ["gunicorn", "main:app", \
     "-c", "gunicorn_config.py"]
