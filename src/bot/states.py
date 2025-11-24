"""
State machines for the registration dialog and the main menu.

This module defines aiogram state groups used to manage the user flow during
registration and subsequent navigation across the main menu.
"""

from aiogram.filters.state import State, StatesGroup


class RegisterSM(StatesGroup):
    """
    Define the state machine for the registration flow.

    Attributes:
        GET_CONTACT: Await contact sharing from the user.
        second_name: Await the user's family name (last name).
        first_name: Await the user's first name.
        surname: Await the user's patronymic/middle name (optional).
        faculty: Await the faculty selection.
        groups: Await the group selection (depends on the selected faculty).
        interests: Await interests selection (can be multiple).
        render: Render/confirm the collected data before finalizing.

    """

    GET_CONTACT = State()
    second_name = State()
    first_name = State()
    surname = State()
    faculty = State()
    groups = State()
    interests = State()
    render = State()


class MainMenuSM(StatesGroup):
    """
    Define the state machine for the main menu navigation.

    Attributes:
        main: Main menu screen.
        profile: User profile screen.
        events: Events listing screen.
        matches_select: Screen for selecting match filters/options.
        matches_selected: Screen showing results of the selection.

    """

    main = State()
    profile = State()
    events = State()
    matches_select = State()
    matches_selected = State()
