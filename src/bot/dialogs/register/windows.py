"""
Модуль окон для диалога регистрации.

Содержит функции создания и настройки интерфейса регистрации.
"""

import operator

from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Multiselect, Row, Select
from aiogram_dialog.widgets.text import Const, Format

from ...states import RegisterSM
from .getters import get_faculties, get_faculty_groups, get_interests, on_register_dialog_start
from .handlers import (
    on_contact_received,
    on_faculty_selected,
    on_first_name_received,
    on_group_selected,
    on_interest_selected,
    on_other_messages,
    on_second_name_received,
    on_surname_received,
    send_contact_request,
    send_interest,
)

contact_window = Window(
    Const("""
Привет! 👋
Рад тебя видеть в нашем чат боте для знакомств НГТУ!

Этот бот создан, чтобы помочь студентам твоего вуза находить новых друзей, единомышленников и, возможно, нечто большее.
Здесь все свои — от сессии до сессии живут весело!

Чтобы всё было безопасно и без фейков, для регистрации нам потребуется доступ к номеру твоего телефона.
Это гарантирует, что вокруг тебя будут только реальные студенты.
"""),
    Const("Пожалуйста, оставьте свой номер телефона, нажав на кнопку ниже."),
    Button(Const("Поделиться контактом"), id="start_contact_button", on_click=send_contact_request),
    MessageInput(
        func=on_contact_received,
        content_types=ContentType.CONTACT,
        id="send_contact_info",
    ),
    MessageInput(on_other_messages),
    state=RegisterSM.GET_CONTACT,
)

second_name_window = Window(
    Const("Input your second name."),
    MessageInput(
        func=on_second_name_received,
        content_types=ContentType.TEXT,
        id="second_name",
    ),
    MessageInput(on_other_messages),
    state=RegisterSM.second_name,
)

first_name_window = Window(
    Const("Input your first name."),
    MessageInput(
        func=on_first_name_received,
        content_types=ContentType.TEXT,
        id="first_name",
    ),
    MessageInput(on_other_messages),
    state=RegisterSM.first_name,
)

surname_window = Window(
    Const("Input your surname."),
    MessageInput(
        func=on_surname_received,
        content_types=ContentType.TEXT,
        id="first_name",
    ),
    MessageInput(on_other_messages),
    state=RegisterSM.surname,
)

faculty_select = Window(
    Const("Выбери свой факультет:"),
    Column(
        Select(
            Format("{item[1]}"),
            id="s_faculties",
            items="faculties",
            item_id_getter=operator.itemgetter(0),
            on_click=on_faculty_selected,
        )
    ),
    getter=get_faculties,
    state=RegisterSM.faculty,
)

group_select = Window(
    Const("Выбери свою группу:"),
    Column(
        Select(
            Format("{item[1]}"),
            id="s_groups",
            items="groups",
            item_id_getter=operator.itemgetter(0),
            on_click=on_group_selected,
        )
    ),
    getter=get_faculty_groups,
    state=RegisterSM.groups,
)

interets_select = Window(
    Const("Выбери свои увлечения:"),
    Column(
        Multiselect(
            Format("✅ {item[1]}"),
            Format("{item[1]}"),
            id="s_interets",
            items="interets",
            item_id_getter=operator.itemgetter(0),
            min_selected=1,
            on_state_changed=on_interest_selected,
        ),
    ),
    Row(
        Button(
            Const("Подтвердить"),
            id="interest_submit",
            on_click=send_interest,
        )
    ),
    getter=get_interests,
    state=RegisterSM.interests,
)

register_dialog = Dialog(
    contact_window,
    second_name_window,
    first_name_window,
    surname_window,
    faculty_select,
    group_select,
    interets_select,
    on_start=on_register_dialog_start,
)
