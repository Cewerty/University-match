"""
Main application module for running Telegram bot and FastAPI server concurrently.

This module initializes and configures the Telegram bot with dialogs and middleware,
sets up the FastAPI application, and starts both services using multiprocessing.
"""

import multiprocessing

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.fsm.storage.base import BaseStorage, DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message
from aiogram_dialog import (
    DialogManager,
    StartMode,
    setup_dialogs,
)

from src.bot.dialogs import main_dialog, register_dialog
from src.bot.middlewares import DatabaseMiddleware
from src.bot.states import RegisterSM
from src.core import logger
from src.core.config import config
from src.web.app import app


def create_storage() -> BaseStorage:
    """
    Create FSM storage for dialog state.

    Uses Redis when REDIS_URL is set, so dialog state survives restarts;
    otherwise falls back to in-memory storage for local development.
    aiogram-dialog requires a key builder with destiny enabled.
    """
    if config.REDIS_URL:
        logger.info("🗄️ Dialog state storage: Redis")
        return RedisStorage.from_url(config.REDIS_URL, key_builder=DefaultKeyBuilder(with_destiny=True))
    logger.info("🗄️ Dialog state storage: in-memory (REDIS_URL is not set)")
    return MemoryStorage()


storage = create_storage()
bot = Bot(
    token=config.BOT_TOKEN,
    # An empty proxy string is rejected by aiohttp-socks, so pass None when no proxy is configured
    session=AiohttpSession(proxy=config.TELEGRAM_PROXY_URL or None),
)
dp = Dispatcher(storage=storage)
dp.update.middleware(DatabaseMiddleware())
dp.include_router(register_dialog)
dp.include_router(main_dialog)
setup_dialogs(dp)


@dp.message(Command("start"))
async def start(message: Message, dialog_manager: DialogManager) -> None:
    """
    Handle the /start command and initiate registration dialog.

    Args:
        message: The incoming message object from user.
        dialog_manager: Dialog manager for controlling dialog flow.

    """
    await dialog_manager.start(RegisterSM.GET_CONTACT, mode=StartMode.RESET_STACK)


def run_fastapi(host: str = config.WEB_HOST, port: int = config.WEB_PORT) -> None:
    """
    Run FastAPI application using Uvicorn server.

    Args:
        host: Host address to bind the server. Defaults to config.WEB_HOST.
        port: Port number to listen on. Defaults to config.WEB_PORT.

    """
    try:
        logger.info("🚀 Launching the FastAPI server...")
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.critical(f"❌ Critical Error FastAPI: {e!r}", exc_info=True)
        raise


def run_telegram_bot() -> None:
    """Start polling for Telegram bot updates."""
    try:
        logger.info("🤖 Launching tg-bot...")
        dp.run_polling(bot, skip_updates=True)
    except Exception as e:
        logger.critical(f"❌ Critical error tg-bot: {e!r}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("🔧 Initialization app...")
    logger.info(f"🌐 Configuration: WEB_HOST={config.WEB_HOST}, WEB_PORT={config.WEB_PORT}")
    logger.info(f"🤖 Tg-bot launching with token: {config.BOT_TOKEN[:5]}...")

    fastapi_process = multiprocessing.Process(target=run_fastapi)
    bot_process = multiprocessing.Process(target=run_telegram_bot)

    # Запускаем процессы
    fastapi_process.start()
    bot_process.start()

    # Ожидаем завершения
    fastapi_process.join()
    bot_process.join()
