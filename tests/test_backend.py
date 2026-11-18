"""request_reindex is best-effort: it reports success or failure and never raises."""

import socket
from collections.abc import AsyncIterator

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from src.bot.backend import request_reindex
from src.core.config import config


async def _serve(monkeypatch: pytest.MonkeyPatch, status: int) -> TestServer:
    """Start a local backend that answers POST /reindex with the given status."""

    async def reindex(_: web.Request) -> web.Response:
        return web.json_response({"status": "Index update started in background"}, status=status)

    app = web.Application()
    app.router.add_post("/reindex", reindex)
    server = TestServer(app)
    await server.start_server()
    monkeypatch.setattr(config, "BACKEND_URL", str(server.make_url("")).rstrip("/"))
    return server


@pytest.fixture
def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
async def accepting_backend(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[TestServer]:
    server = await _serve(monkeypatch, 200)
    yield server
    await server.close()


@pytest.fixture
async def rejecting_backend(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[TestServer]:
    server = await _serve(monkeypatch, 503)
    yield server
    await server.close()


@pytest.mark.usefixtures("accepting_backend")
async def test_returns_true_when_the_backend_accepts() -> None:
    assert await request_reindex() is True


@pytest.mark.usefixtures("rejecting_backend")
async def test_returns_false_when_the_backend_rejects() -> None:
    assert await request_reindex() is False


async def test_returns_false_when_the_backend_is_unreachable(monkeypatch: pytest.MonkeyPatch, free_port: int) -> None:
    monkeypatch.setattr(config, "BACKEND_URL", f"http://127.0.0.1:{free_port}")

    assert await request_reindex() is False
