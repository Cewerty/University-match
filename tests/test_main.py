"""Command line of main.py: which part of the application to run."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from main import MODES, parse_args, run_all, run_fastapi, run_telegram_bot

ROOT = Path(__file__).resolve().parent.parent


def test_default_mode_runs_everything() -> None:
    assert parse_args([]).mode == "all"


@pytest.mark.parametrize(("mode", "target"), [("all", run_all), ("bot", run_telegram_bot), ("web", run_fastapi)])
def test_modes_map_to_runners(mode: str, target: object) -> None:
    assert MODES[parse_args([mode]).mode] is target


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(SystemExit):
        parse_args(["worker"])


def test_importing_main_does_not_load_the_web_app() -> None:
    """The bot container must not pay for torch and FAISS: main must not import src.web.app eagerly."""
    code = "import sys, main; assert 'src.web.app' not in sys.modules; assert 'torch' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=os.environ.copy(), check=True)  # noqa: S603
