"""Détection de la structure (chapitre / section) avec état inter-pages.

Le chapitre/section courant est « collant » : une fois détecté, il s'applique
aux pages suivantes jusqu'à la prochaine occurrence.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.ingestion.detectors.patterns import (
    CHAP_MARKER_RE,
    CHAPTER_HEADER_RE,
    SECTION_RE,
)


@dataclass
class StructureState:
    chapter: str | None = None
    section: str | None = None


class StructureTracker:
    """Suit le chapitre et la section courants au fil des pages.

    Le chapitre n'est mis à jour que sur un en-tête réel (début de ligne
    « Chapitre N ») ou un marqueur de page (« N / Chap 31 »), jamais sur une
    mention en prose (« … du chapitre 29 … ») — ce qui évite le « chapter bleed ».
    Le libellé est normalisé (« Chapitre 31 ») pour rester cohérent avec le
    chapitre déduit du code SH lui-même.
    """

    def __init__(self) -> None:
        self.state = StructureState()

    def update(self, text: str) -> StructureState:
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            m = CHAPTER_HEADER_RE.match(line) or CHAP_MARKER_RE.search(line)
            if m:
                self.state.chapter = f"Chapitre {int(m.group(1))}"
            section_match = SECTION_RE.search(line)
            if section_match:
                self.state.section = f"Section {section_match.group(1).upper()}"
        return self.state
