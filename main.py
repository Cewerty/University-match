"""
Entry point: runs the Telegram bot, the FastAPI server, or both.

    python main.py          # both, in two processes (local development)
    python main.py bot      # only the bot (the `bot` service in compose.yaml)
    python main.py web      # only FastAPI with the admin panel and the matcher (`web` service)

The bot talks to FastAPI over HTTP (BACKEND_URL), so the two can run in separate
containers. Heavy imports (the web app pulls in torch and FAISS) happen only in the
process that needs them.
"""

import argparse
import multiprocessing
from collections.abc import Callable, Sequence

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.bot.states import RegisterSM
from src.core import logger
from src.core.config import config

start_router = Router(name="start")


@start_router.message(Command("start"))
async def start(message: Message, dialog_manager: DialogManager) -> None:
    """
    Handle the /start command and initiate registration dialog.

    Args:
        message: The incoming message object from user.
        dialog_manager: Dialog manager for controlling dialog flow.

    """
    await dialog_manager.start(RegisterSM.GET_CONTACT, mode=StartMode.RESET_STACK)


def create_storage() -> BaseStorage:
    """
    Create FSM storage for dialog state.

    Uses Redis when REDIS_URL is set, so dialog state survives restarts;
    otherwise falls back to in-memory storage for local development.
    aiogram-dialog requires a key builder with destiny enabled.
    """
    if config.REDIS_URL:
        from aiogram.fsm.storage.base import DefaultKeyBuilder  # noqa: PLC0415
        from aiogram.fsm.storage.redis import RedisStorage  # noqa: PLC0415

        logger.info("🗄️ Dialog state storage: Redis")
        return RedisStorage.from_url(config.REDIS_URL, key_builder=DefaultKeyBuilder(with_destiny=True))

    from aiogram.fsm.storage.memory import MemoryStorage  # noqa: PLC0415

    logger.info("🗄️ Dialog state storage: in-memory (REDIS_URL is not set)")
    return MemoryStorage()


def run_fastapi(host: str = config.WEB_HOST, port: int = config.WEB_PORT) -> None:
    """
    Run FastAPI application using Uvicorn server.

    Args:
        host: Host address to bind the server. Defaults to config.WEB_HOST.
        port: Port number to listen on. Defaults to config.WEB_PORT.

    """
    import uvicorn  # noqa: PLC0415

    from src.web.app import app  # noqa: PLC0415

    try:
        logger.info("🚀 Launching the FastAPI server...")
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.critical(f"❌ Critical Error FastAPI: {e!r}", exc_info=True)
        raise


def run_telegram_bot() -> None:
    """Build the bot and dispatcher, then poll Telegram for updates."""
    from aiogram import Bot, Dispatcher  # noqa: PLC0415
    from aiogram.client.session.aiohttp import AiohttpSession  # noqa: PLC0415
    from aiogram_dialog import setup_dialogs  # noqa: PLC0415

    from src.bot.dialogs import main_dialog, register_dialog  # noqa: PLC0415
    from src.bot.middlewares import DatabaseMiddleware  # noqa: PLC0415

    bot = Bot(
        token=config.require_bot_token(),
        # An empty proxy string is rejected by aiohttp-socks, so pass None when no proxy is configured
        session=AiohttpSession(proxy=config.TELEGRAM_PROXY_URL or None),
    )
    dp = Dispatcher(storage=create_storage())
    dp.update.middleware(DatabaseMiddleware())
    dp.include_router(start_router)
    dp.include_router(register_dialog)
    dp.include_router(main_dialog)
    setup_dialogs(dp)

    try:
        logger.info("🤖 Launching tg-bot...")
        dp.run_polling(bot, skip_updates=True)
    except Exception as e:
        logger.critical(f"❌ Critical error tg-bot: {e!r}", exc_info=True)
        raise


def run_all() -> None:
    """Run the bot and FastAPI in two processes and wait for both."""
    processes = [
        multiprocessing.Process(target=run_fastapi, name="web"),
        multiprocessing.Process(target=run_telegram_bot, name="bot"),
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()


MODES: dict[str, Callable[[], None]] = {
    "all": run_all,
    "bot": run_telegram_bot,
    "web": run_fastapi,
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line: which part of the application to run."""
    parser = argparse.ArgumentParser(description="Run the University Match bot and/or its FastAPI backend.")
    parser.add_argument("mode", nargs="?", choices=MODES, default="all", help="what to run (default: all)")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    logger.info(f"🔧 Initialization app, mode: {args.mode}")
    logger.info(f"🌐 Configuration: WEB_HOST={config.WEB_HOST}, WEB_PORT={config.WEB_PORT}")
    MODES[args.mode]()
