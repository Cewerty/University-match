"""Parsing helpers used by src.core.config."""

import pytest

from src.core.config import _env_bool, _normalize_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1", True),
        ("true", True),
        ("True", True),
        (" yes ", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("False", False),
        ("no", False),
        ("", False),
    ],
)
def test_env_bool(monkeypatch: pytest.MonkeyPatch, raw: str, expected: bool) -> None:
    monkeypatch.setenv("SOME_FLAG", raw)

    assert _env_bool("SOME_FLAG", "true") is expected


def test_env_bool_uses_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOME_FLAG", raising=False)

    assert _env_bool("SOME_FLAG", "true") is True


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("localhost:8000", "http://localhost:8000"),
        ("http://web:8000/", "http://web:8000"),
        ("https://example.dev", "https://example.dev"),
    ],
)
def test_normalize_url(raw: str, expected: str) -> None:
    assert _normalize_url(raw) == expected
