"""Client Redis partagé (cache / files d'attente légères)."""
from __future__ import annotations

import redis

from app.core.config import settings

redis_client: redis.Redis = redis.from_url(
    settings.REDIS_URL, decode_responses=True
)


def get_redis() -> redis.Redis:
    """Dépendance FastAPI : fournit le client Redis."""
    return redis_client
