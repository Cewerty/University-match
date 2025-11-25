FROM python:3.12-slim-bookworm

# Только необходимые системные пакеты
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Установка uv (самый быстрый вариант)
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

WORKDIR /app

# Копируем зависимости для кэширования
COPY pyproject.toml uv.lock ./

# Установка с оптимизацией для VDS
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_INDEX_URL=https://pypi.org/simple \
    UV_HTTP_TIMEOUT=600 \
    uv sync \
    --no-dev \
    --frozen \
    --no-editable \
    --no-compile

# Копируем код приложения
COPY . .

# Безопасность
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

CMD ["/app/.venv/bin/python", "main.py"]