"""UserMatcher behaviour with a fake embedding model (no model download)."""

from typing import Any

import numpy as np
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import User
from src.services.matcher import UserMatcher

# Joined interests of a user -> raw (unnormalized) embedding
VECTORS = {
    "a": np.array([3.0, 0.0, 0.0]),
    "a, b": np.array([2.0, 2.0, 0.0]),
    "c": np.array([0.0, 0.0, 5.0]),
    "b": np.array([-1.0, 1.0, 0.0]),
}


class FakeModel:
    """Stands in for SentenceTransformer: fixed vectors per text."""

    def encode(self, texts: list[str], *, normalize_embeddings: bool = False, **_: Any) -> np.ndarray:
        vectors = np.stack([VECTORS[t] for t in texts])
        if normalize_embeddings:
            vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


@pytest.fixture
async def matcher(session: AsyncSession, catalog: dict[str, Any]) -> UserMatcher:
    interests = catalog["interests"]
    for user_id, names in enumerate([["a"], ["a", "b"], ["c"], ["b"]], start=1):
        session.add(
            User(
                id=user_id,
                telegram_id=1000 + user_id,
                first_name=f"User{user_id}",
                second_name="Test",
                phone_number="+70000000000",
                faculty=catalog["faculty"],
                group=catalog["group"],
                interests=[interests[n] for n in names],
            )
        )
    await session.commit()

    service = UserMatcher(model_name="fake")
    service.model = FakeModel()  # type: ignore[assignment]
    await service.update_index(session)
    return service


async def test_scores_are_cosine_similarity_sorted_and_exclude_self(
    matcher: UserMatcher, session: AsyncSession
) -> None:
    hits = await matcher.search(1, session)

    # self (1) excluded; cosines are ~0.71 (user 2), 0 (user 3), ~-0.71 (user 4)
    assert [h["id"] for h in hits] == [2, 3, 4]
    expected = {2: cosine(VECTORS["a"], VECTORS["a, b"]), 3: 0.0, 4: cosine(VECTORS["a"], VECTORS["b"])}
    for hit in hits:
        assert hit["score"] == pytest.approx(expected[hit["id"]], abs=1e-5)
    assert all(-1.0 <= h["score"] <= 1.0 for h in hits)


async def test_num_results_is_respected(matcher: UserMatcher, session: AsyncSession) -> None:
    hits = await matcher.search(1, session, num_results=1)

    assert [h["id"] for h in hits] == [2]


async def test_unknown_user_returns_empty_list(matcher: UserMatcher, session: AsyncSession) -> None:
    assert await matcher.search(999, session) == []
