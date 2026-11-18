"""Parsing helpers used by src.core.config."""

from pathlib import Path

import pytest

from src.core.config import Config, _env_bool, _env_or_file, _normalize_url


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


def test_env_or_file_prefers_the_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    secret = tmp_path / "token"
    secret.write_text("from-file\n", encoding="utf-8")
    monkeypatch.setenv("SOME_SECRET", "from-env")
    monkeypatch.setenv("SOME_SECRET_FILE", str(secret))

    assert _env_or_file("SOME_SECRET") == "from-file"


def test_env_or_file_falls_back_to_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOME_SECRET_FILE", raising=False)
    monkeypatch.setenv("SOME_SECRET", "from-env")

    assert _env_or_file("SOME_SECRET") == "from-env"


def test_missing_token_fails_only_when_the_bot_needs_it() -> None:
    settings = Config()
    settings.BOT_TOKEN = ""

    with pytest.raises(ValueError, match="BOT_TOKEN"):
        settings.require_bot_token()


def test_require_bot_token_returns_the_token() -> None:
    settings = Config()
    settings.BOT_TOKEN = "123:abc"

    assert settings.require_bot_token() == "123:abc"
