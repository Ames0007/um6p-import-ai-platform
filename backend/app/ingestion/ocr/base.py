"""Contrat des fournisseurs OCR."""
from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OcrResult:
    text: str
    success: bool
    error: str | None = None


class OcrProvider(abc.ABC):
    """Reconnaît le texte d'une page scannée d'un document."""

    name: str = "base"

    @property
    @abc.abstractmethod
    def available(self) -> bool:
        """Indique si le fournisseur est réellement opérationnel."""

    @abc.abstractmethod
    def ocr_page(self, document_path: str | Path, page_number: int) -> OcrResult:
        """Exécute l'OCR sur une page précise (1-indexée)."""
