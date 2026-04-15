"""
User matching service using FAISS and sentence transformers.

This module provides functionality for matching users based on their interests
using semantic similarity with FAISS index and sentence transformer embeddings.
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
from ..core.models import User


class UserMatcher:
    """
    Service for matching users based on interest similarity.

    Uses FAISS for efficient similarity search and sentence transformers
    for text embeddings.

    Attributes:
        model: Sentence transformer model for text embeddings.
        index: FAISS index for similarity search.
        user_data: Mapping of user IDs to user data.
        user_vectors: Embedding vectors for all users.
        index_to_user_id: Mapping from FAISS index to user IDs.
        is_ready: Flag indicating if the service is ready for queries.

    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialize UserMatcher with specified model.

        Args:
            model_name: Name of the sentence transformer model to use.

        """
        self.model = None
        self.index = None
        self.user_data = {}
        self.user_vectors = None
        self.index_to_user_id = None
        self.is_ready = False
        self.model_name = model_name

    def load_model(self) -> None:
        """Load the sentence transformer model."""
        if self.model is None:
            logger.info("🚀 Start loading NLP model...")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ NLP model loaded.")

    async def update_index(self, session: AsyncSession) -> None:
        """
        Update the FAISS index with current user data from database.

        Args:
            session: Database session for querying users.

        Note:
            This method performs CPU-intensive operations in separate threads
            to avoid blocking the main event loop.

        """
        if self.model is None:
            await asyncio.to_thread(self.load_model)

        query = select(User).options(selectinload(User.interests))
        result = await session.execute(query)
        users = result.scalars().all()

        if not users:
            logger.warning("⚠️ Пользователей нет, индекс не построен.")
            return

        texts_to_encode = []
        temp_ids = []
        temp_user_data = {}

        for user in users:
            if not user.interests:
                continue

            interest_names = [i.name for i in user.interests]

            temp_user_data[user.id] = {"name": f"{user.first_name} {user.second_name}", "interests": interest_names}

            text_representation = ", ".join(interest_names)
            texts_to_encode.append(text_representation)
            temp_ids.append(user.id)

        if not texts_to_encode:
            return

        logger.info(f"🧠 Векторизация {len(texts_to_encode)} пользователей...")
        embeddings = await asyncio.to_thread(self.model.encode, texts_to_encode)

        await asyncio.to_thread(self._build_faiss_index, embeddings, temp_ids, temp_user_data)
        logger.info(f"✅ Индекс обновлен. В базе {self.index.ntotal} векторов.")

        self.is_ready = True
        logger.info("✅ Index updated and ready.")

    async def add_user_to_index(self, session: AsyncSession, user_id: int) -> bool:
        """
        Добавляет или обновляет данные одного пользователя в индексе.

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя для обновления

        Returns:
            bool: True если пользователь успешно добавлен/обновлен

        """
        try:
            # Загружаем модель если еще не загружена
            if self.model is None:
                await asyncio.to_thread(self.load_model)

            # Получаем данные пользователя с интересами
            query = select(User).options(selectinload(User.interests)).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user or not user.interests:
                logger.error(f"❌ Пользователь {user_id} не найден или у него нет интересов")
                return False

            # Подготавливаем данные для пользователя
            interest_names = [i.name for i in user.interests]
            text_representation = ", ".join(interest_names)

            logger.info(f"🔄 Векторизация интересов для пользователя {user_id}...")
            embedding = await asyncio.to_thread(self.model.encode, [text_representation], convert_to_tensor=False)

            # Если индекс еще не создан - создаем его
            if self.index is None or self.user_vectors is None:
                await self.update_index(session)
                return True

            # Обновляем данные пользователя
            user_data = {"name": f"{user.first_name} {user.second_name}", "interests": interest_names}

            # Обновляем или добавляем пользователя в индекс
            if user_id in self.index_to_user_id:
                # Обновляем существующего пользователя
                idx = self.index_to_user_id.index(user_id)
                # Удаляем старый вектор (FAISS не поддерживает прямое обновление)
                # Создаем новый индекс без этого вектора
                vectors = [v for i, v in enumerate(self.user_vectors) if i != idx]
                ids = [i for i in self.index_to_user_id if i != user_id]

                # Перестраиваем индекс
                new_index = faiss.IndexFlatL2(embedding.shape[1])
                if vectors:
                    new_index.add(np.vstack(vectors).astype("float32"))

                # Добавляем новый вектор
                new_index.add(embedding.astype("float32"))

                # Обновляем все данные
                self.index = new_index
                self.user_vectors = np.vstack([*vectors, embedding[0]])
                self.index_to_user_id = [*ids, user_id]
                self.user_data[user_id] = user_data
            else:
                # Добавляем нового пользователя
                self.index.add(embedding.astype("float32"))
                if self.user_vectors is None:
                    self.user_vectors = embedding
                else:
                    self.user_vectors = np.vstack([self.user_vectors, embedding[0]])
                self.index_to_user_id.append(user_id)
                self.user_data[user_id] = user_data

            logger.info(f"✅ Пользователь {user_id} успешно добавлен в индекс")
            return True  # noqa: TRY300

        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении пользователя {user_id} в индекс: {e}")
            return False

    def _build_faiss_index(self, embeddings: Any, ids: Any, data_map: Any) -> None:
        """
        Build FAISS index (run in separate thread).

        Args:
            embeddings: User interest embeddings from sentence transformer.
            ids: List of user IDs corresponding to embeddings.
            data_map: Mapping from user IDs to user data.

        """
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype("float32"))

        self.user_vectors = embeddings
        self.index_to_user_id = ids
        self.user_data = data_map

    async def search(self, user_id: int, session: AsyncSession, num_results: int = 10) -> list[dict]:
        """
        Search for similar users based on interests.

        Args:
            user_id: ID of the user to find matches for.
            session: Async database session for updating index if It's not ready
            num_results: Maximum number of results to return.

        Returns:
            List of dictionaries containing match information with keys:
            - id: User ID
            - name: User's full name
            - interests: List of user's interests
            - score: Similarity score (1 - distance)

        Note:
            Returns empty list if user not found in index or index not built.

        """
        try:
            logger.info(f"🔍 Поиск match-ей для пользователя {user_id}")

            if not self.is_ready or self.index is None or self.user_vectors is None:
                logger.warning(f"⚠️ Индекс не готов для пользователя {user_id}, запускаем обновление")
                await self.update_index(session)
                if not self.is_ready:
                    logger.error(f"❌ Индекс не удалось обновить для пользователя {user_id}")
                    return []

            internal_index = self.index_to_user_id.index(user_id)

            query_vector = self.user_vectors[internal_index : internal_index + 1]

            distances, indices = await asyncio.to_thread(
                self.index.search, query_vector.astype("float32"), num_results + 1
            )

            results = []
            for i, dist in zip(indices[0], distances[0], strict=False):
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
                        "score": float(1 - dist),
                    }
                )

            logger.info(f"✅ Найдено {len(results)} match-ей для пользователя {user_id}")
            logger.debug(f"📊 Результаты поиска: {results}")

            return results  # noqa: TRY300

        except Exception as e:
            logger.error(f"❌ Ошибка при поиске match-ей для пользователя {user_id}: {e!r}")
            logger.exception("🔍 Трейс ошибки поиска match-ей")
            return []


matcher_service = UserMatcher()
