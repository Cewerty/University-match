"""
Configuration module for application settings.

This module loads environment variables and provides configuration settings
for the Telegram bot, database, web server, and application parameters.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Application configuration class.

    Loads and validates environment variables with fallback defaults.

    Attributes:
        BOT_TOKEN (str): Telegram bot token from environment variables.
        DATABASE_URL (str): Database connection URL with SQLite fallback.
        WEB_HOST (str): Web server host address with localhost fallback.
        WEB_PORT (int): Web server port number.
        MINIMAL_MATCH_VALUE (float): Minimum match threshold for user matching.

    Raises:
        ValueError: If required BOT_TOKEN environment variable is not set.

    """

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Переменная BOT_TOKEN не найдена в .env!")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

    WEB_HOST = os.getenv("WEB_HOST", "localhost")

    WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

    MINIMAL_MATCH_VALUE = float(os.getenv("MINIMAL_MATCH_VALUE", "0.2"))

    SEED_GENERATION_AMOUNT = int(os.getenv("SEED_GENERATION_AMOUNT", "50"))


config = Config()
