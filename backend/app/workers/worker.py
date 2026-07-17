"""Point d'entrée d'un worker RQ.

Utilisation :
    python -m app.workers.worker
ou via Docker (service `worker`).
"""
from __future__ import annotations

import logging

from rq import Worker

from app.core.config import settings
from app.core.logging import setup_logging
from app.workers.queue import get_queue, get_redis_connection

setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)


def main() -> None:
    queue = get_queue()
    worker = Worker([queue], connection=get_redis_connection())
    logging.getLogger("ingestion").info(
        "Worker RQ démarré sur la file « %s »", settings.INGESTION_QUEUE_NAME
    )
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
