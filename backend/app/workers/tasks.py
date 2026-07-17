"""Tâches exécutables par un worker (chemins d'import stables pour RQ)."""
from __future__ import annotations

import logging
import uuid

from app.ingestion.pipeline import run_ingestion

logger = logging.getLogger("ingestion.tasks")


def ingest_document(document_id: str, resume: bool = True) -> dict:
    """Point d'entrée de la tâche d'ingestion (sérialisable par RQ)."""
    doc_uuid = uuid.UUID(str(document_id))
    logger.info("Ingestion démarrée : %s (resume=%s)", doc_uuid, resume)
    result = run_ingestion(doc_uuid, resume=resume)
    logger.info("Ingestion terminée : %s (%s)", doc_uuid, result.as_stats())
    return result.as_stats()


def analyze_invoice(analysis_id: str, resume: bool = True) -> str:
    """Tâche d'analyse de conformité d'une facture (sérialisable par RQ)."""
    from app.compliance.pipeline import run_analysis

    an_uuid = uuid.UUID(str(analysis_id))
    logger.info("Analyse import démarrée : %s (resume=%s)", an_uuid, resume)
    run_analysis(an_uuid, resume=resume)
    logger.info("Analyse import terminée : %s", an_uuid)
    return str(an_uuid)
