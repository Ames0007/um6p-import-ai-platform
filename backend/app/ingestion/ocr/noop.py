"""Fournisseur OCR par défaut : ne fait rien, signale l'indisponibilité."""
from __future__ import annotations

from pathlib import Path

from app.ingestion.ocr.base import OcrProvider, OcrResult


class NoOpOcrProvider(OcrProvider):
    name = "noop"

    @property
    def available(self) -> bool:
        return False

    def ocr_page(self, document_path: str | Path, page_number: int) -> OcrResult:
        return OcrResult(
            text="",
            success=False,
            error="OCR non configuré (OCR_ENABLED=false).",
        )
