"""Journalisation structurée centralisée (Phase 8).

Fournit une configuration de logging unique pour le backend ET le worker.
Format JSON par défaut (observabilité), format texte lisible en développement.
N'introduit AUCUNE dépendance externe et ne modifie aucune logique métier :
il se contente de router les logs existants (app, ingestion, ai, db, …) vers
une sortie structurée.
"""
from __future__ import annotations

import json
import logging
import sys
from logging.config import dictConfig

# Journaux applicatifs nommés utilisés à travers le projet.
APP_LOGGERS = (
    "app",
    "http",
    "startup",
    "shutdown",
    "db",
    "knowledge_index",
    "search",
    "ai",
    "claude",
    "ingestion",
    "compliance",
    "health",
    "security",
)


class JsonFormatter(logging.Formatter):
    """Formateur JSON minimal (une ligne par événement)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Champs additionnels transmis via logger.info(..., extra={"extra_fields": {...}})
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        # Trace d'exception : toujours rendue (type, message, pile complète) dès
        # qu'un exc_info est présent — quel que soit l'appelant (uvicorn inclus).
        if record.exc_info and record.exc_info[0] is not None:
            exc_type, exc_val, _ = record.exc_info
            payload.setdefault("exc_type", getattr(exc_type, "__name__", str(exc_type)))
            payload.setdefault("exc_message", str(exc_val))
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_CONFIGURED = False


def setup_logging(level: str = "INFO", fmt: str = "json") -> None:
    """Configure la journalisation du process (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    formatter: dict[str, object]
    if fmt.lower() == "text":
        formatter = {
            "format": "%(asctime)s %(levelname)-7s %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    else:
        formatter = {"()": "app.core.logging.JsonFormatter"}

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": formatter},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": sys.stdout,
                }
            },
            "root": {"level": level.upper(), "handlers": ["console"]},
            "loggers": {
                # Uvicorn/Gunicorn : on réutilise le même handler/format.
                "uvicorn": {"level": level.upper(), "handlers": ["console"], "propagate": False},
                "uvicorn.error": {"level": level.upper(), "handlers": ["console"], "propagate": False},
                "uvicorn.access": {"level": "WARNING", "handlers": ["console"], "propagate": False},
                "gunicorn.error": {"level": level.upper(), "handlers": ["console"], "propagate": False},
                "gunicorn.access": {"level": "WARNING", "handlers": ["console"], "propagate": False},
                **{
                    name: {"level": level.upper(), "handlers": ["console"], "propagate": False}
                    for name in APP_LOGGERS
                },
            },
        }
    )
    _CONFIGURED = True


def log_event(logger_name: str, message: str, level: int = logging.INFO, **fields: object) -> None:
    """Émet un log structuré avec des champs additionnels."""
    logging.getLogger(logger_name).log(level, message, extra={"extra_fields": fields})
