"""Extracteurs de texte par format de fichier."""
from __future__ import annotations

from pathlib import Path

from app.ingestion.extractors.base import Extractor, UnsupportedFormatError
from app.ingestion.extractors.csv_ext import CsvExtractor
from app.ingestion.extractors.docx_ext import DocxExtractor
from app.ingestion.extractors.pdf import PdfExtractor
from app.ingestion.extractors.xlsx_ext import XlsxExtractor

_EXTRACTORS: list[Extractor] = [
    PdfExtractor(),
    DocxExtractor(),
    XlsxExtractor(),
    CsvExtractor(),
]


def get_extractor(path: str | Path) -> Extractor:
    """Retourne l'extracteur adapté à l'extension du fichier."""
    suffix = Path(path).suffix.lower()
    for extractor in _EXTRACTORS:
        if suffix in extractor.extensions:
            return extractor
    raise UnsupportedFormatError(f"Format non pris en charge : {suffix}")


__all__ = [
    "Extractor",
    "UnsupportedFormatError",
    "get_extractor",
    "PdfExtractor",
    "DocxExtractor",
    "XlsxExtractor",
    "CsvExtractor",
]
