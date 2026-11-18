"""
User matching service using FAISS and sentence transformers.

Each user's interests are joined into one string and encoded with a
multilingual sentence-transformers model. Embeddings are L2-normalized and
stored in a FAISS inner-product index, so the search score is the cosine
similarity between two users' interest profiles, in the range [-1, 1].
"""

import asyncio
from typing import Any

import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core import logger
from ..core.config import config
from ..core.models import User


class UserMatcher:
    """
    Service for matching users based on interest similarity.

    Attributes:
        model: Sentence transformer model for text embeddings (loaded lazily).
        index: FAISS inner-product index over normalized embeddings.
        user_data: Mapping of user IDs to display data (name, interests).
        user_vectors: Normalized embedding vectors, row-aligned with index_to_user_id.
        index_to_user_id: Mapping from FAISS row to user ID.
        is_ready: Flag indicating if the service is ready for queries.

    """

    def __init__(self, model_name: str = config.EMBEDDING_MODEL) -> None:
        """
        Initialize UserMatcher with the given model name.

        Args:
            model_name: Name of the sentence-transformers model to use.

        """
        self.model: SentenceTransformer | None = None
        self.index: Any = None
        self.user_data: dict[int, dict[str, Any]] = {}
        self.user_vectors: np.ndarray | None = None
        self.index_to_user_id: list[int] = []
        self.is_ready = False
        self.model_name = model_name

    def load_model(self) -> SentenceTransformer:
        """Load the sentence transformer model once and return it."""
        if self.model is None:
            logger.info(f"🚀 Start loading NLP model {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ NLP model loaded.")
        return self.model

    def _embed(self, texts: list[str]) -> np.ndarray:
        """
        Encode texts into L2-normalized float32 vectors.

        Normalization makes the inner product equal to cosine similarity.
        """
        model = self.load_model()
        embeddings = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return np.asarray(embeddings, dtype="float32")

    async def update_index(self, session: AsyncSession) -> None:
        """
        Rebuild the FAISS index from the current users in the database.

        Args:
            session: Database session for querying users.

        Note:
            Model loading, encoding and index building run in worker threads
            to avoid blocking the event loop.

        """
        result = await session.execute(select(User).options(selectinload(User.interests)))
        users = result.scalars().all()

        texts_to_encode: list[str] = []
        ids: list[int] = []
        user_data: dict[int, dict[str, Any]] = {}

        for user in users:
            if not user.interests:
                continue
            interest_names = [i.name for i in user.interests]
            user_data[user.id] = {"name": f"{user.first_name} {user.second_name}", "interests": interest_names}
            texts_to_encode.append(", ".join(interest_names))
            ids.append(user.id)

        if not texts_to_encode:
            logger.warning("⚠️ Нет пользователей с интересами, индекс не построен.")
            return

        logger.info(f"🧠 Векторизация {len(texts_to_encode)} пользователей...")
        embeddings = await asyncio.to_thread(self._embed, texts_to_encode)
        await asyncio.to_thread(self._build_faiss_index, embeddings, ids, user_data)

        self.is_ready = True
        logger.info(f"✅ Индекс обновлен. В базе {self.index.ntotal} векторов.")

    def _build_faiss_index(self, embeddings: np.ndarray, ids: list[int], data_map: dict[int, dict[str, Any]]) -> None:
        """
        Build an inner-product FAISS index (runs in a worker thread).

        Args:
            embeddings: Normalized user embeddings, one row per user.
            ids: User IDs, row-aligned with embeddings.
            data_map: Mapping from user IDs to display data.

        """
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)

        self.index = index
        self.user_vectors = embeddings
        self.index_to_user_id = ids
        self.user_data = data_map

    async def search(self, user_id: int, session: AsyncSession, num_results: int = 10) -> list[dict[str, Any]]:
        """
        Find users with the most similar interests.

        Args:
            user_id: ID of the user to find matches for.
            session: Database session, used to build the index if it is not ready.
            num_results: Maximum number of results to return.

        Returns:
            Matches sorted by descending score, each a dict with keys:
            - id: User ID
            - name: User's full name
            - interests: List of user's interests
            - score: Cosine similarity of interest embeddings, in [-1, 1]

        Note:
            Returns an empty list if the index cannot be built or the user is
            not in it yet (e.g. registered after the last rebuild).

        """
        try:
            logger.info(f"🔍 Поиск match-ей для пользователя {user_id}")

            if not self.is_ready or self.index is None or self.user_vectors is None:
                logger.warning(f"⚠️ Индекс не готов для пользователя {user_id}, запускаем обновление")
                await self.update_index(session)
                if not self.is_ready or self.user_vectors is None:
                    logger.error(f"❌ Индекс не удалось обновить для пользователя {user_id}")
                    return []

            if user_id not in self.index_to_user_id:
                logger.warning(f"⚠️ Пользователя {user_id} ещё нет в индексе, он появится после переиндексации")
                return []

            row = self.index_to_user_id.index(user_id)
            query_vector = self.user_vectors[row : row + 1]

            similarities, indices = await asyncio.to_thread(self.index.search, query_vector, num_results + 1)

            results = []
            for i, similarity in zip(indices[0], similarities[0], strict=True):
                if i == -1:
                    continue
                found_user_id = self.index_to_user_id[i]
                if found_user_id == user_id:
                    continue
                user_info = self.user_data[found_user_id]
                results.append(
                    {
                        "id": found_user_id,
                        "name": user_info["name"],
                        "interests": user_info["interests"],
                        "score": float(similarity),
                    }
                )

            logger.info(f"✅ Найдено {len(results)} match-ей для пользователя {user_id}")
            logger.debug(f"📊 Результаты поиска: {results}")
            return results[:num_results]

        except Exception as e:
            logger.error(f"❌ Ошибка при поиске match-ей для пользователя {user_id}: {e!r}")
            logger.exception("🔍 Трейс ошибки поиска match-ей")
            return []


matcher_service = UserMatcher()
