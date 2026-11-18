"""
Configuration module for application settings.

This module loads environment variables and provides configuration settings
for the Telegram bot, database, web server, and application parameters.
"""

import os

from dotenv import load_dotenv

load_dotenv()

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_bool(name: str, default: str) -> bool:
    """Parse a boolean environment variable ("1", "true", "yes", "on" are truthy)."""
    return os.getenv(name, default).strip().lower() in _TRUTHY


def _env_or_file(name: str, default: str = "") -> str:
    """
    Read a setting from `{name}_FILE` if it is set, otherwise from `{name}`.

    The file form is how Docker secrets are passed (/run/secrets/...), so the value
    never appears in the container's environment or in `docker inspect`.
    """
    path = os.getenv(f"{name}_FILE")
    if path:
        with open(path, encoding="utf-8") as file:
            return file.read().strip()
    return os.getenv(name, default)


def _normalize_url(url: str) -> str:
    """Add an http:// scheme if missing and strip trailing slashes."""
    url = url.strip().rstrip("/")
    return url if "://" in url else f"http://{url}"


class Config:
    """
    Application configuration class.

    Loads and validates environment variables with fallback defaults.

    Attributes:
        BOT_TOKEN (str): Telegram bot token, from BOT_TOKEN or the file in BOT_TOKEN_FILE.
            Only the bot needs it; see require_bot_token().
        DATABASE_URL (str): Database connection URL with SQLite fallback.
        WEB_HOST (str): Web server host address with localhost fallback.
        WEB_PORT (int): Web server port number.
        EMBEDDING_MODEL (str): sentence-transformers model used to embed interests.
        MINIMAL_MATCH_VALUE (float): Minimum cosine similarity for a match to be shown.
        BACKEND_URL (str): FastAPI base URL used by the bot, always with a scheme.
        DEBUG (bool): Debug mode flag.
        REDIS_URL (str): Redis URL for dialog state storage; empty means in-memory.
        TELEGRAM_PROXY_URL (str): Proxy for the Telegram API, may carry a password,
            so it can also come from TELEGRAM_PROXY_URL_FILE.

    """

    BOT_TOKEN: str = _env_or_file("BOT_TOKEN")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

    WEB_HOST: str = os.getenv("WEB_HOST", "localhost")

    WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

    MINIMAL_MATCH_VALUE: float = float(os.getenv("MINIMAL_MATCH_VALUE", "0.45"))

    SEED_GENERATION_AMOUNT: int = int(os.getenv("SEED_GENERATION_AMOUNT", "50"))

    BACKEND_URL: str = _normalize_url(os.getenv("BACKEND_URL", "http://localhost:8000"))

    DEBUG: bool = _env_bool("DEBUG", "true")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    TELEGRAM_PROXY_URL: str = _env_or_file("TELEGRAM_PROXY_URL")

    REDIS_URL: str = os.getenv("REDIS_URL", "")

    def require_bot_token(self) -> str:
        """
        Return the bot token, failing if it is not configured.

        Checked when the bot starts rather than on import, so the web server,
        migrations and other processes run without access to the token.

        Raises:
            ValueError: If neither BOT_TOKEN nor BOT_TOKEN_FILE provides a token.

        """
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set: put it in .env or point BOT_TOKEN_FILE at a file with it")
        return self.BOT_TOKEN


config = Config()
