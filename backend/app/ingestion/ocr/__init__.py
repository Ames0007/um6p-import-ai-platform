"""Intégration OCR par « hooks » enfichables.

Par défaut, aucun OCR n'est exécuté (NoOpOcrProvider) : les pages scannées
sont signalées comme telles sans bloquer l'ingestion. Pour activer un OCR réel,
mettre `OCR_ENABLED=true` et fournir les dépendances (voir TesseractOcrProvider).
"""
from __future__ import annotations

from app.core.config import settings
from app.ingestion.ocr.base import OcrProvider, OcrResult
from app.ingestion.ocr.noop import NoOpOcrProvider
from app.ingestion.ocr.tesseract import TesseractOcrProvider


def get_ocr_provider() -> OcrProvider:
    """Fabrique le fournisseur OCR selon la configuration."""
    if settings.OCR_ENABLED:
        return TesseractOcrProvider()
    return NoOpOcrProvider()


__all__ = [
    "OcrProvider",
    "OcrResult",
    "NoOpOcrProvider",
    "TesseractOcrProvider",
    "get_ocr_provider",
]
