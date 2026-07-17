"""Couche d'exécution asynchrone de l'ingestion (RQ + repli thread)."""
from __future__ import annotations

from app.workers.dispatch import dispatch_analysis, dispatch_ingestion

__all__ = ["dispatch_ingestion", "dispatch_analysis"]
