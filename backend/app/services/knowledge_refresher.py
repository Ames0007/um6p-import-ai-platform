"""Rafraîchisseur d'Index de connaissance en arrière-plan (Phase 7).

Objectif : les RECHERCHES ne reconstruisent JAMAIS l'index (aucune écriture sur
le chemin de lecture). La reconstruction n'a lieu que lorsque les données source
changent — imports réussis, mises à jour de taxes / autorisations / base — ce que
les déclencheurs SQL signalent déjà via `knowledge_index_state.dirty`.

Ce module consomme ce drapeau HORS du chemin des requêtes :
- au démarrage du backend (reconstruction si « sale » ou vide) ;
- périodiquement, dans un thread dédié, protégé par un verrou d'avis PostgreSQL
  (`pg_try_advisory_lock`) pour un rebuild « single-flight » même avec plusieurs
  workers Gunicorn.

Ne modifie NI la construction de l'index NI la logique de recherche : il ne fait
qu'appeler l'`ensure_fresh` existant au bon moment.
"""
from __future__ import annotations

import logging
import threading
import time

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.knowledge_index import knowledge_index_builder

log = logging.getLogger("knowledge_index")

# Clé arbitraire mais stable pour le verrou d'avis (single-flight du rebuild).
_ADVISORY_LOCK_KEY = 823_417_001


def refresh_once() -> bool:
    """Reconstruit l'index s'il est marqué « sale » (idempotent, verrouillé).

    Retourne True si le verrou a été acquis (le contrôle a eu lieu), False si un
    autre process détenait déjà le verrou (rebuild concurrent évité).
    """
    db = SessionLocal()
    try:
        got = db.execute(
            text("SELECT pg_try_advisory_lock(:k)"), {"k": _ADVISORY_LOCK_KEY}
        ).scalar()
        if not got:
            return False
        try:
            start = time.monotonic()
            knowledge_index_builder.ensure_fresh(db)
            log.info(
                "Index de connaissance vérifié/reconstruit.",
                extra={"extra_fields": {"ms": round((time.monotonic() - start) * 1000, 1)}},
            )
        finally:
            db.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _ADVISORY_LOCK_KEY})
        return True
    finally:
        db.close()


class KnowledgeRefresher:
    """Thread de fond qui réconcilie l'index quand les données changent."""

    def __init__(self, interval: int) -> None:
        self.interval = max(5, int(interval))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._loop, name="ki-refresher", daemon=True
        )
        self._thread.start()
        log.info(
            "Rafraîchisseur d'index démarré.",
            extra={"extra_fields": {"interval_s": self.interval}},
        )

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                refresh_once()
            except Exception:  # ne jamais tuer le thread de fond
                log.warning("Échec du rafraîchissement de l'index.", exc_info=True)
            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        log.info("Rafraîchisseur d'index arrêté.")


# Singleton partagé (démarré/arrêté par le cycle de vie de l'application).
refresher = KnowledgeRefresher(settings.KI_REFRESH_INTERVAL_SECONDS)
