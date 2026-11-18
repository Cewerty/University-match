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

# System user with a uid outside the range of ordinary host users, no home and no shell
RUN groupadd --system --gid 10001 app \
    && useradd --system --no-log-init --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# The container runs with a read-only root filesystem (see compose.yaml), so:
# no .pyc files next to the code, HOME points at the /tmp tmpfs for libraries that
# write to ~, and the embedding model cache is a named volume at /cache/huggingface
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    HF_HOME=/cache/huggingface \
    DATABASE_URL=sqlite+aiosqlite:////app/data/bot.db

# The only writable places: the database and the model cache
# (named volumes copy this ownership on first use)
RUN mkdir -p /app/data "$HF_HOME" \
    && chown app:app /app/data "$HF_HOME"

# ---- dev: for `docker compose watch` and running checks in a container ------------------
FROM base AS dev

COPY --from=builder-dev /app/.venv /app/.venv
# Owned by the app user: `docker compose watch` syncs changed files into /app
COPY --chown=10001:10001 . .

USER 10001:10001

CMD ["python", "main.py"]

# ---- runtime: only the virtual environment and the code (default target) ----------------
FROM base AS runtime

# Code and the virtual environment stay owned by root: the app only reads them
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Numeric id, so the host can resolve it without the image's /etc/passwd
USER 10001:10001

CMD ["/app/.venv/bin/python", "main.py"]
