# syntax=docker/dockerfile:1

# Base image pinned by digest for reproducible builds. It is written out in every FROM line
# (not via ARG) so that Dependabot can find and update it.
#
# Targets:
#   runtime (default, last stage)  production image, no dev tools
#   dev                            runtime + pytest/ruff/mypy, used by compose.override.yaml

# ---- builder: install dependencies into /app/.venv --------------------------------------
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df AS builder

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

# ---- builder-dev: the same environment plus the dev dependency group ---------------------
FROM builder AS builder-dev

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-compile

# ---- base: what runtime and dev share ---------------------------------------------------
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df AS base

# Create the user first, so files can be copied with the right owner
# instead of a recursive chown that duplicates the whole layer
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# The embedding model cache lives in a named volume (see compose.yaml)
ENV PATH=/app/.venv/bin:$PATH \
    HF_HOME=/home/appuser/.cache/huggingface

# ---- dev: for `docker compose watch` and running checks in a container ------------------
FROM base AS dev

COPY --from=builder-dev /app/.venv /app/.venv
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/data "$HF_HOME" \
    && chown appuser:appuser /app /app/data "$HF_HOME"

USER 1000:1000

CMD ["python", "main.py"]

# ---- runtime: only the virtual environment and the code (default target) ----------------
FROM base AS runtime

# The virtual environment stays owned by root: the app only reads it
COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

# Only the app directory itself (for the default SQLite file), data/ and the model
# cache (a named volume copies this ownership on first use) need to be writable
RUN mkdir -p /app/data "$HF_HOME" \
    && chown appuser:appuser /app /app/data "$HF_HOME"

# Numeric id, so the host can resolve it without the image's /etc/passwd
USER 1000:1000

CMD ["/app/.venv/bin/python", "main.py"]
