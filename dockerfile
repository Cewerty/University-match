# Dockerfile
FROM python:3.12-slim-bookworm

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    g++ \
    git \
    libgl1 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Установка uv для быстрой установки зависимостей
RUN pip install uv --no-cache-dir

# Установка рабочей директории
WORKDIR /app

# Копирование зависимостей для кэширования
COPY pyproject.toml uv.lock ./

# Установка зависимостей
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-cache-dir --requirement pyproject.toml \
    --compile \
    --no-binary=:all: faiss-cpu  # Компилируем из исходников для оптимизации

# Копирование приложения
COPY . .

# Создание пользователя для безопасности
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Переключение на пользователя
USER appuser

# Команда запуска
CMD ["python", "-m", "main.py"]