"""
Main application module for running Telegram bot and FastAPI server concurrently.

This module initializes and configures the Telegram bot with dialogs and middleware,
sets up the FastAPI application, and starts both services using multiprocessing.
"""

import multiprocessing

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram_dialog import (
    DialogManager,
    StartMode,
    setup_dialogs,
)
from aiogram.client.session.aiohttp import AiohttpSession

from src.bot.dialogs import main_dialog, register_dialog
from src.bot.middlewares import DatabaseMiddleware
from src.bot.states import RegisterSM
from src.core import logger
from src.core.config import config
from src.web.app import app

storage = MemoryStorage()
bot = Bot(token=config.BOT_TOKEN, session=AiohttpSession(proxy=config.TELEGRAM_PROXY_URL),)
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
    uvicorn.run(app, host=host, port=port)
    try:
        logger.info("🚀 Launching the FastAPI server...")
        uvicorn.run("src.web.app:app", host=config.WEB_HOST, port=config.WEB_PORT, reload=False)
    except Exception as e:
        logger.critical(f"❌ Critical Error FastAPI: {e!r}", exc_info=True)
        raise


def run_telegram_bot() -> None:
    """Start polling for Telegram bot updates."""
    try:
        logger.info("🤖 Launcing tg-bot...")
        dp.run_polling(bot, skip_updates=True)
    except Exception as e:
        logger.critical(f"❌ Critical error tg-bot: {e!r}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("🔧 Initialization app...")
    logger.info(f"🌐 Configuration: WEB_HOST={config.WEB_HOST}, WEB_PORT={config.WEB_PORT}")
    logger.info(f"🤖 Tg-bot launcing with token: {config.BOT_TOKEN[:5]}...")

    fastapi_process = multiprocessing.Process(target=run_fastapi)
    bot_process = multiprocessing.Process(target=run_telegram_bot)

    # Запускаем процессы
    fastapi_process.start()
    bot_process.start()

    # Ожидаем завершения
    fastapi_process.join()
    bot_process.join()
