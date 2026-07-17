"""Hook OCR basé sur Tesseract (activé uniquement si les dépendances existent).

Dépendances (non incluses par défaut) :
    pip install pytesseract pdf2image
    + binaire système `tesseract-ocr` et `poppler`.

L'import est paresseux : l'application démarre même sans ces dépendances.
"""
from __future__ import annotations

from pathlib import Path

from app.ingestion.ocr.base import OcrProvider, OcrResult


class TesseractOcrProvider(OcrProvider):
    name = "tesseract"

    def __init__(self, lang: str = "fra") -> None:
        self.lang = lang
        self._ready = False
        try:  # imports paresseux — n'échoue pas au démarrage
            import pdf2image  # noqa: F401
            import pytesseract  # noqa: F401

            self._ready = True
        except ImportError:
            self._ready = False

    @property
    def available(self) -> bool:
        return self._ready

    def ocr_page(self, document_path: str | Path, page_number: int) -> OcrResult:
        if not self._ready:
            return OcrResult(
                text="",
                success=False,
                error="Dépendances OCR absentes (pytesseract / pdf2image).",
            )
        try:
            import pdf2image
            import pytesseract

            images = pdf2image.convert_from_path(
                str(document_path),
                first_page=page_number,
                last_page=page_number,
                dpi=200,
            )
            if not images:
                return OcrResult(text="", success=False, error="Page introuvable.")
            text = pytesseract.image_to_string(images[0], lang=self.lang)
            return OcrResult(text=text, success=True)
        except Exception as exc:  # échec OCR isolé, non bloquant
            return OcrResult(text="", success=False, error=f"Échec OCR : {exc}")
