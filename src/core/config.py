import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Переменная BOT_TOKEN не найдена в .env!")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

    WEB_HOST = os.getenv("WEB_HOST", "localhost")

    WEB_PORT = int(os.getenv("WEB_PORT", None))


config = Config()
