"""Extraction de texte PDF (pypdf) avec détection des pages scannées."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from app.core.config import settings
from app.ingestion.extractors.base import CorruptedDocumentError, Extractor
from app.ingestion.types import ExtractedPage


class PdfExtractor(Extractor):
    extensions = {".pdf"}

    def _open(self, path: str | Path):
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "pypdf n'est pas installé (requirements.txt)."
            ) from exc

        try:
            return PdfReader(str(path))
        except Exception as exc:  # pypdf lève diverses erreurs sur fichiers corrompus
            raise CorruptedDocumentError(
                f"PDF illisible ou corrompu : {exc}"
            ) from exc

    def count_pages(self, path: str | Path) -> int:
        reader = self._open(path)
        return len(reader.pages)

    def iter_pages(self, path: str | Path) -> Iterator[ExtractedPage]:
        reader = self._open(path)
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # page illisible : on continue
                yield ExtractedPage(
                    number=index, text="", error=f"Extraction échouée : {exc}"
                )
                continue

            needs_ocr = len(text.strip()) < settings.OCR_MIN_CHARS_PER_PAGE
            yield ExtractedPage(number=index, text=text, needs_ocr=needs_ocr)
