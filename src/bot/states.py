from aiogram.filters.state import State, StatesGroup


class RegisterSM(StatesGroup):
    GET_CONTACT = State()
    second_name = State()
    first_name = State()
    surname = State()
    faculty = State()
    groups = State()
    interests = State()
    render = State()


class MainMenuSM(StatesGroup):
    main = State()
    profile = State()
    events = State()
    matches_select = State()
    matches_selected = State()
