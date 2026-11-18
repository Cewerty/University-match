"""request_reindex is best-effort: it reports success or failure and never raises."""

import aiohttp
from aioresponses import aioresponses

from src.bot.backend import request_reindex
from src.core.config import config

REINDEX_URL = f"{config.BACKEND_URL}/reindex"


async def test_returns_true_when_the_backend_accepts() -> None:
    with aioresponses() as mocked:
        mocked.post(REINDEX_URL, status=200, payload={"status": "Index update started in background"})

        assert await request_reindex() is True


async def test_returns_false_when_the_backend_rejects() -> None:
    with aioresponses() as mocked:
        mocked.post(REINDEX_URL, status=503)

        assert await request_reindex() is False


async def test_returns_false_when_the_backend_is_unreachable() -> None:
    with aioresponses() as mocked:
        mocked.post(REINDEX_URL, exception=aiohttp.ClientConnectionError("down"))

        assert await request_reindex() is False
