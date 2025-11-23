import asyncio

import faiss
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Импортируем твои модели
from ..core.models import User


class UserMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Загрузка модели — тяжелая операция, лучше делать при старте, но один раз
        self.model = None
        self.index = None
        self.user_data = {}
        # Флаг, чтобы понимать, готова ли система
        self.is_ready = False

    def load_model(self):
        """Синхронная загрузка модели (тяжелая)"""
        if self.model is None:
            print("🚀 Start loading NLP model...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ NLP model loaded.")

    async def update_index(self, session):
        """Полный цикл обновления: загрузка модели -> данные -> индекс"""
        # 1. Если модель еще не загружена — грузим (в треде, чтобы не блочить FastAPI)
        if self.model is None:
            await asyncio.to_thread(self.load_model)

        # 2. Загружаем данные и строим индекс (как в прошлом коде)
        # ... (тут твой код load_and_process_users и build_index) ...
        query = select(User).options(selectinload(User.interests))
        result = await session.execute(query)
        users = result.scalars().all()

        if not users:
            print("⚠️ Пользователей нет, индекс не построен.")
            return

        # Подготовка текстовых данных (это быстро, можно оставить в главном потоке)
        texts_to_encode = []
        temp_ids = []
        temp_user_data = {}

        for user in users:
            if not user.interests:
                continue

            interest_names = [i.name for i in user.interests]

            # Сохраняем данные для быстрого доступа при поиске
            temp_user_data[user.id] = {"name": f"{user.first_name} {user.second_name}", "interests": interest_names}

            # Формируем строку для векторизации
            text_representation = ", ".join(interest_names)
            texts_to_encode.append(text_representation)
            temp_ids.append(user.id)

        if not texts_to_encode:
            return

        # 2. Векторизация (CPU bound) -> Выносим в тред!
        # Бот продолжит отвечать другим юзерам, пока это считается
        print(f"🧠 Векторизация {len(texts_to_encode)} пользователей...")
        embeddings = await asyncio.to_thread(self.model.encode, texts_to_encode)

        # 3. Построение индекса FAISS (CPU bound) -> Тоже в тред
        await asyncio.to_thread(self._build_faiss_index, embeddings, temp_ids, temp_user_data)
        print(f"✅ Индекс обновлен. В базе {self.index.ntotal} векторов.")

        self.is_ready = True
        print("✅ Index updated and ready.")

    def _build_faiss_index(self, embeddings, ids, data_map):
        """Синхронный метод построения индекса, запускаемый внутри треда."""
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype("float32"))

        # Атомарное обновление состояния (подменяем ссылки)
        self.user_vectors = embeddings
        self.index_to_user_id = ids
        self.user_data = data_map

    async def search(self, user_id: int, num_results: int = 3):
        """Поиск похожих пользователей."""
        if self.index is None or self.user_vectors is None:
            return []

        try:
            # Находим внутренний индекс вектора пользователя
            internal_index = self.index_to_user_id.index(user_id)
        except ValueError:
            return []  # Пользователь еще не попал в индекс

        query_vector = self.user_vectors[internal_index : internal_index + 1]

        # Поиск в FAISS обычно быстрый (<1мс для тысяч записей),
        # но для гарантии можно тоже обернуть в to_thread
        distances, indices = self.index.search(query_vector, num_results + 1)

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

        return results


# Создаем глобальный экземпляр (Singleton)
matcher_service = UserMatcher()
