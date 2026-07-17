"""Contrat commun des extracteurs."""
from __future__ import annotations

import abc
from collections.abc import Iterator
from pathlib import Path

from app.ingestion.types import ExtractedPage


class UnsupportedFormatError(Exception):
    """Format de fichier non pris en charge."""


class CorruptedDocumentError(Exception):
    """Document illisible ou corrompu."""


class Extractor(abc.ABC):
    """Extrait le texte d'un document, page par page (ou feuille/section)."""

    #: Extensions gérées (avec le point), ex. {".pdf"}
    extensions: set[str] = set()

    @abc.abstractmethod
    def count_pages(self, path: str | Path) -> int:
        """Nombre total de pages/feuilles (pour la progression)."""

    @abc.abstractmethod
    def iter_pages(self, path: str | Path) -> Iterator[ExtractedPage]:
        """Itère paresseusement sur les pages extraites (adapté aux gros fichiers)."""
