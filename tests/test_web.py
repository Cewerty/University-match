"""FastAPI endpoints. The app is used without its lifespan, so no index is built and no model is loaded."""

import pytest
from fastapi.testclient import TestClient

from src.services.matcher import matcher_service
from src.web.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_search_returns_503_while_index_is_not_ready(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matcher_service, "is_ready", False)

    response = client.get("/search/1")

    assert response.status_code == 503


def test_reindex_rebuilds_index_once(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    async def fake_update_index(session: object) -> None:
        calls.append(session)

    monkeypatch.setattr(matcher_service, "update_index", fake_update_index)

    response = client.post("/reindex")

    assert response.status_code == 200
    assert len(calls) == 1
