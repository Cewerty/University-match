import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, Column, Select
from aiogram_dialog.widgets.text import Const, Format, Jinja

from ...states import MainMenuSM
from .getters import get_match_profile_data, get_profile_data, get_user_match, on_main_menu_dialog_start
from .handlers import back_to_menu, on_match_selected, on_search_clicked, send_events, send_profile

main_menu_window = Window(
    Format("С возвращением, {dialog_data[data].second_name} {dialog_data[data].first_name}!"),  # noqa: RUF001
    Column(
        Button(Const("Профиль"), id="again_someshit", on_click=send_profile),
        Button(Const("Мероприятия"), id="events", on_click=send_events),
        Button(Const("Поиск по интересам"), id="and_again_someshit", on_click=on_search_clicked),
    ),
    state=MainMenuSM.main,
)

profile_html = Jinja("""
<b>{{second_name}} {{first_name}} {{surname}}</b>

Факультет: {{faculty}}

Группа: {{group}}

Ваши интересы:
{% for interest in interests %}
— {{interest}}
{% endfor %}
""")

profile_window = Window(
    profile_html,
    Button(Const("В главное меню"), id="from_profile_to_main_menu", on_click=back_to_menu),
    parse_mode="HTML",
    state=MainMenuSM.profile,
    getter=get_profile_data,
)

events_window = Window(
    Const("""

28.11-Лига КВН среди 1 курсов
01.12-Начало зимы
05.12-Просто хороший день
08.12-Прекрасный зимний день
        """),
    Button(Const("В главное меню"), id="from_profile_to_main_menu", on_click=back_to_menu),
    state=MainMenuSM.events,
)

match_select_window = Window(
    Const("Результаты поиска:"),
    Column(
        Select(
            Format("{item[1]}"),
            id="s_matches",
            items="matches",
            item_id_getter=operator.itemgetter(0),
            on_click=on_match_selected,
        ),
        Button(Const("В главное меню"), id="from_profile_to_main_menu", on_click=back_to_menu),
    ),
    getter=get_user_match,
    state=MainMenuSM.matches_select,
)

match_html = Jinja("""
<b>{{phone_number}}</b>: <b>{{second_name}} {{first_name}}</b>

Факультет: {{faculty}}

Группа: {{group}}

Интересы:
{% for interest in interests %}
— {{interest}}
{% endfor %}
""")

match_selected_window = Window(
    match_html,
    Back(Const("Назад"), id="from_profile_to_main_menu"),
    parse_mode="HTML",
    state=MainMenuSM.matches_selected,
    getter=get_match_profile_data,
)

main_dialog = Dialog(
    main_menu_window,
    profile_window,
    events_window,
    match_select_window,
    match_selected_window,
    on_start=on_main_menu_dialog_start,
)
