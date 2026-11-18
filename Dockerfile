FROM python:3.12-slim-bookworm

# Compiler toolchain for packages without prebuilt wheels
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv from the official image (lands directly on PATH)
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first to cache this layer
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_HTTP_TIMEOUT=600 \
    uv sync --frozen --no-dev --no-install-project --no-compile

# Application code (see .dockerignore)
COPY . .

RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser

CMD ["/app/.venv/bin/python", "main.py"]
