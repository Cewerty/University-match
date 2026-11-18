# syntax=docker/dockerfile:1

# Base image pinned by digest for reproducible builds; Dependabot keeps it up to date
ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

# ---- builder: install dependencies into /app/.venv --------------------------------------
FROM ${PYTHON_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /usr/local/bin/uv

# Use the image's Python (the runtime stage has the same one), copy files out of the
# cache mount instead of hardlinking, and keep the build from stalling on slow downloads
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=600

WORKDIR /app

# Dependencies first, so code changes do not invalidate this layer
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --no-compile

# ---- runtime: only the virtual environment and the code ---------------------------------
FROM ${PYTHON_IMAGE}

# Create the user first, so files can be copied with the right owner
# instead of a recursive chown that duplicates the whole layer
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# The virtual environment stays owned by root: the app only reads it
COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

# Only the app directory itself (for the default SQLite file) and data/ need to be writable
RUN mkdir -p /app/data && chown appuser:appuser /app /app/data

USER appuser

CMD ["/app/.venv/bin/python", "main.py"]
