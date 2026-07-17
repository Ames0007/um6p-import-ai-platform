"""Répartition des tâches d'ingestion : RQ (durable) ou thread (repli)."""
from __future__ import annotations

import logging
import threading
import uuid

from app.core.config import settings
from app.workers.tasks import analyze_invoice, ingest_document

logger = logging.getLogger("ingestion.dispatch")


def _run_in_thread(document_id: str, resume: bool) -> None:
    thread = threading.Thread(
        target=ingest_document,
        args=(document_id, resume),
        name=f"ingest-{document_id[:8]}",
        daemon=True,
    )
    thread.start()


def dispatch_ingestion(document_id: uuid.UUID, *, resume: bool = True) -> str:
    """Planifie l'ingestion d'un document. Retourne le mode d'exécution.

    - `USE_TASK_QUEUE=true`  → enfilement RQ (traité par un worker séparé).
    - sinon                  → exécution dans un thread d'arrière-plan.
    En cas d'échec d'enfilement RQ (Redis indisponible), repli en thread si
    `INGESTION_INLINE_FALLBACK=true`.
    """
    doc_id = str(document_id)

    if settings.USE_TASK_QUEUE:
        try:
            from app.workers.queue import get_queue

            get_queue().enqueue(
                ingest_document,
                doc_id,
                resume,
                job_timeout=settings.JOB_TIMEOUT_SECONDS,
            )
            logger.info("Tâche d'ingestion enfilée (RQ) : %s", doc_id)
            return "queued"
        except Exception as exc:  # Redis indisponible, etc.
            logger.warning("Enfilement RQ impossible (%s).", exc)
            if not settings.INGESTION_INLINE_FALLBACK:
                raise

    _run_in_thread(doc_id, resume)
    logger.info("Ingestion lancée en thread d'arrière-plan : %s", doc_id)
    return "inline"


def dispatch_analysis(analysis_id: uuid.UUID, *, resume: bool = True) -> str:
    """Planifie l'analyse de conformité d'une facture (RQ ou thread)."""
    an_id = str(analysis_id)

    if settings.USE_TASK_QUEUE:
        try:
            from app.workers.queue import get_queue

            get_queue().enqueue(
                analyze_invoice, an_id, resume,
                job_timeout=settings.JOB_TIMEOUT_SECONDS,
            )
            logger.info("Analyse enfilée (RQ) : %s", an_id)
            return "queued"
        except Exception as exc:
            logger.warning("Enfilement RQ impossible (%s).", exc)
            if not settings.INGESTION_INLINE_FALLBACK:
                raise

    threading.Thread(
        target=analyze_invoice, args=(an_id, resume),
        name=f"analyze-{an_id[:8]}", daemon=True,
    ).start()
    logger.info("Analyse lancée en thread d'arrière-plan : %s", an_id)
    return "inline"
