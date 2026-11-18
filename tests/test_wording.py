"""
Bot texts must stay neutral: no dating or romantic wording.

Some users may be minors, so the bot is positioned as a way to find study
and project partners. See src/docs/adr/0001-bot-only-introduces-no-media-or-chat.md.
"""

import re
from pathlib import Path

import pytest

BOT_SOURCES = sorted(Path("src/bot").rglob("*.py"))
FORBIDDEN = re.compile(r"знакомств|познаком|нечто большее|свидан|романт|любов|флирт|dating|romanc", re.IGNORECASE)


def test_bot_sources_are_found() -> None:
    assert BOT_SOURCES, "no bot sources found; is the test run from the project root?"


@pytest.mark.parametrize("path", BOT_SOURCES, ids=str)
def test_no_romantic_wording_in_bot_texts(path: Path) -> None:
    matches = [
        f"{path}:{number}: {line.strip()}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if FORBIDDEN.search(line)
    ]

    assert not matches, "romantic wording found:\n" + "\n".join(matches)
