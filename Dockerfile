# syntax=docker/dockerfile:1

# Stage 1: Build dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies, frozen lockfile)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY app/ ./app/

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Stage 2: Runtime image
FROM python:3.12-slim-bookworm AS runtime

# Create non-root user
RUN groupadd --gid 1000 tgdigest && \
    useradd --uid 1000 --gid 1000 --create-home tgdigest

# Create data directory for volume mount
RUN mkdir -p /data && chown tgdigest:tgdigest /data

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=tgdigest:tgdigest /app/.venv /app/.venv

# Copy application code
COPY --chown=tgdigest:tgdigest app/ ./app/
COPY --chown=tgdigest:tgdigest pyproject.toml ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/data/app.db \
    TELETHON_SESSION=/data/telethon.session

# Switch to non-root user
USER tgdigest

# Default command
ENTRYPOINT ["tg-digest"]
CMD ["run-all"]
