"""Column formatters of the admin panel keep their output after the typing refactor."""

from types import SimpleNamespace

import pytest

from src.web.app import _faculty_name, _group_faculty, _mark_faculty, _user_faculty


@pytest.mark.parametrize(("name", "expected"), [("ФБ", "ФБ❤️"), ("РЭФ", "РЭФ"), ("", "")])
def test_mark_faculty(name: str, expected: str) -> None:
    assert _mark_faculty(name) == expected


def test_formatters_read_the_faculty_from_the_model_instance() -> None:
    faculty = SimpleNamespace(name="ФБ")

    assert _user_faculty(SimpleNamespace(faculty=faculty), None) == "ФБ❤️"
    assert _group_faculty(SimpleNamespace(faculty=SimpleNamespace(name="РЭФ")), None) == "РЭФ"
    assert _faculty_name(faculty, None) == "ФБ❤️"
