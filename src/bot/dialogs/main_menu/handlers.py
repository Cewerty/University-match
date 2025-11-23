from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from ...states import MainMenuSM

# async def send_events_list(callback: CallbackQuery, button: Button, manager: DialogManager):
#     await callback.message.answer(
#         """

# 28.11-Лига КВН среди 1 курсов
# 01.12-Начало зимы
# 05.12-Просто хороший день
# 08.12-Прекрасный зимний день
#         """
#     )


async def send_profile(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(MainMenuSM.profile)


async def send_events(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(MainMenuSM.events)


async def back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(MainMenuSM.main)
