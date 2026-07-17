"""File d'attente RQ adossée à Redis."""
from __future__ import annotations

from functools import lru_cache

from redis import Redis
from rq import Queue

from app.core.config import settings


@lru_cache
def get_redis_connection() -> Redis:
    return Redis.from_url(settings.REDIS_URL)


@lru_cache
def get_queue() -> Queue:
    return Queue(
        settings.INGESTION_QUEUE_NAME,
        connection=get_redis_connection(),
        default_timeout=settings.JOB_TIMEOUT_SECONDS,
    )
