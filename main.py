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

from src.bot import RegisterSM
from src.bot.dialogs import main_dialog, register_dialog
from src.bot.middlewares import DatabaseMiddleware
from src.core.config import config
from src.web.app import app

storage = MemoryStorage()
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=storage)
dp.update.middleware(DatabaseMiddleware())
dp.include_router(register_dialog)
dp.include_router(main_dialog)
setup_dialogs(dp)


@dp.message(Command("start"))
async def start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(RegisterSM.GET_CONTACT, mode=StartMode.RESET_STACK)


def run_fastapi(host: str = config.WEB_HOST, port: int = config.WEB_PORT) -> None:
    uvicorn.run(app, host=host, port=port)


def run_telegram_bot() -> None:
    dp.run_polling(bot, skip_updates=True)


if __name__ == "__main__":
    fastapi_process = multiprocessing.Process(target=run_fastapi)
    bot_process = multiprocessing.Process(target=run_telegram_bot)

    # Запускаем процессы
    fastapi_process.start()
    bot_process.start()

    # Ожидаем завершения
    fastapi_process.join()
    bot_process.join()
