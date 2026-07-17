"""Extraction CSV (stdlib). Une « page » logique = le fichier entier."""
from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

from app.ingestion.extractors.base import CorruptedDocumentError, Extractor
from app.ingestion.types import ExtractedPage


class CsvExtractor(Extractor):
    extensions = {".csv"}

    def count_pages(self, path: str | Path) -> int:
        return 1

    def iter_pages(self, path: str | Path) -> Iterator[ExtractedPage]:
        try:
            with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
                sample = fh.read(4096)
                fh.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
                except csv.Error:
                    dialect = csv.excel
                reader = csv.reader(fh, dialect)
                lines = [" | ".join(row) for row in reader if any(row)]
        except UnicodeDecodeError as exc:
            raise CorruptedDocumentError(f"CSV illisible (encodage) : {exc}") from exc
        yield ExtractedPage(number=1, text="\n".join(lines))
