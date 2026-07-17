"""Points de contrôle de santé (Phase 4).

- `/health`     : compat rétro — état simple.
- `/live`       : LIVENESS — le process répond (jamais de dépendance, toujours 200).
- `/ready`      : READINESS — vérifie Base / Index de connaissance / Redis / Worker.
- `/readiness`  : alias de `/ready`.

La readiness renvoie 503 si une dépendance CRITIQUE est indisponible (base de
données ; Redis lorsque la file d'attente est activée). L'état de l'index
(« sale ») et l'absence de worker sont signalés mais n'entraînent pas 503 :
les lectures restent possibles.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

log = logging.getLogger("health")

router = APIRouter(tags=["Santé"])


def _check_database() -> dict:
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - dépend du runtime
        return {"status": "down", "detail": str(exc)[:200]}


def _check_knowledge_index() -> dict:
    try:
        db = SessionLocal()
        try:
            count = db.execute(text("SELECT count(*) FROM knowledge_index")).scalar()
            state = db.execute(
                text("SELECT dirty, last_built_at FROM knowledge_index_state WHERE id = 1")
            ).first()
        finally:
            db.close()
        dirty = bool(state[0]) if state else None
        last_built = str(state[1]) if state and state[1] else None
        return {
            "status": "ok" if (count or 0) > 0 else "empty",
            "rows": int(count or 0),
            "dirty": dirty,
            "last_built_at": last_built,
        }
    except Exception as exc:
        return {"status": "down", "detail": str(exc)[:200]}


def _check_redis() -> dict:
    if not settings.USE_TASK_QUEUE:
        return {"status": "disabled"}
    try:
        from app.workers.queue import get_redis_connection

        get_redis_connection().ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "down", "detail": str(exc)[:200]}


def _check_worker() -> dict:
    if not settings.USE_TASK_QUEUE:
        return {"status": "disabled"}
    try:
        from rq import Worker

        from app.workers.queue import get_queue, get_redis_connection

        workers = Worker.all(connection=get_redis_connection())
        queue_name = get_queue().name
        attached = [w for w in workers if queue_name in {q.name for q in w.queues}]
        return {"status": "ok" if attached else "absent", "count": len(attached)}
    except Exception as exc:
        return {"status": "unknown", "detail": str(exc)[:200]}


@router.get("/health")
def health() -> dict[str, str]:
    """État simple (compat rétro)."""
    return {"status": "ok"}


@router.get("/live")
def live() -> dict[str, str]:
    """Liveness : le process est vivant (aucune dépendance vérifiée)."""
    return {"status": "alive"}


def _readiness(response: Response) -> dict:
    database = _check_database()
    redis = _check_redis()
    knowledge_index = _check_knowledge_index()
    worker = _check_worker()

    # Dépendances critiques pour SERVIR : base OK, et Redis OK si file activée.
    ready = database["status"] == "ok" and redis["status"] in {"ok", "disabled"}

    body = {
        "status": "ready" if ready else "not_ready",
        "environment": settings.APP_ENV,
        "components": {
            "database": database,
            "knowledge_index": knowledge_index,
            "redis": redis,
            "worker": worker,
        },
    }
    if not ready:
        response.status_code = 503
        log.warning("Readiness KO", extra={"extra_fields": body})
    return body


@router.get("/ready")
def ready(response: Response) -> dict:
    """Readiness : prêt à servir le trafic ? (503 sinon)."""
    return _readiness(response)


@router.get("/readiness")
def readiness(response: Response) -> dict:
    """Alias de `/ready`."""
    return _readiness(response)
