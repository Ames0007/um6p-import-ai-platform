"""Amorçage base de données (Phase 3).

- `wait_for_db`   : attend que PostgreSQL réponde (démarrage ordonné).
- `ensure_extensions` : crée les extensions requises (pgcrypto, vector, pg_trgm)
  de façon idempotente — garantit que les migrations Alembic (qui utilisent des
  colonnes `vector`) s'appliquent sur une base vierge.

Exécutable comme module dans le service `migrate` :
    python -m app.db.bootstrap && alembic upgrade head

Ne touche à aucune logique métier : uniquement l'infrastructure de démarrage.
"""
from __future__ import annotations

import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings

log = logging.getLogger("db")

_EXTENSIONS = ("pgcrypto", "vector", "pg_trgm")


def wait_for_db(timeout: float = 60.0, interval: float = 2.0) -> None:
    """Bloque jusqu'à ce que la base réponde à `SELECT 1` ou expire."""
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info(
                "Base de données joignable.",
                extra={"extra_fields": {"attempt": attempt, "host": settings.POSTGRES_HOST,
                                        "port": settings.POSTGRES_PORT}},
            )
            engine.dispose()
            return
        except OperationalError as exc:
            if time.monotonic() >= deadline:
                engine.dispose()
                raise RuntimeError(
                    f"Base de données injoignable après {timeout}s "
                    f"({settings.POSTGRES_HOST}:{settings.POSTGRES_PORT})."
                ) from exc
            log.warning(
                "Base indisponible, nouvelle tentative…",
                extra={"extra_fields": {"attempt": attempt}},
            )
            time.sleep(interval)


def ensure_extensions() -> None:
    """Crée les extensions PostgreSQL requises (idempotent)."""
    engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            for ext in _EXTENSIONS:
                conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}"'))
        log.info(
            "Extensions PostgreSQL prêtes.",
            extra={"extra_fields": {"extensions": list(_EXTENSIONS)}},
        )
    finally:
        engine.dispose()


def main() -> None:
    from app.core.logging import setup_logging

    setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
    wait_for_db()
    ensure_extensions()


if __name__ == "__main__":
    main()
