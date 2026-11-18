"""
HTTP calls from the bot process to the FastAPI backend.

The FAISS index lives in the FastAPI process, so the bot never touches it
directly: it asks the backend to rebuild the index after the data changes.
"""

import aiohttp

from ..core import logger
from ..core.config import config

REINDEX_TIMEOUT = aiohttp.ClientTimeout(total=5)


async def request_reindex() -> bool:
    """
    Ask the backend to rebuild the matching index in the background.

    Best-effort: on failure the periodic rebuild in the backend picks the
    change up later.

    Returns:
        bool: True if the backend accepted the request.

    """
    url = f"{config.BACKEND_URL}/reindex"
    try:
        async with aiohttp.ClientSession(timeout=REINDEX_TIMEOUT) as session, session.post(url) as resp:
            if resp.ok:
                logger.info("🔄 Запрошено обновление индекса")
                return True
            logger.warning(f"⚠️ Backend отклонил запрос на переиндексацию: {resp.status}")
    except aiohttp.ClientError as e:
        logger.warning(f"⚠️ Не удалось запросить переиндексацию: {e!r}")
    return False
