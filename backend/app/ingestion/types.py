"""Structures de données partagées par le pipeline d'ingestion."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExtractedPage:
    """Contenu texte d'une page/feuille et indicateurs d'extraction."""

    number: int  # 1-indexé
    text: str
    needs_ocr: bool = False
    ocr_used: bool = False
    error: str | None = None

    @property
    def char_count(self) -> int:
        return len(self.text.strip())


@dataclass
class DetectedHsCode:
    code: str
    page: int | None
    chapter: str | None = None
    section: str | None = None
    description: str | None = None
    import_duty: float | None = None   # droit d'importation lu dans la table tarifaire
    vat: float | None = None           # TVA si présente dans la table


@dataclass
class ChunkDraft:
    """Fragment prêt à être stocké (avant embedding)."""

    chunk_index: int
    text: str
    page: int | None = None
    chapter: str | None = None
    section: str | None = None


@dataclass
class IngestionResult:
    """Bilan d'une exécution du pipeline."""

    total_pages: int = 0
    processed_pages: int = 0
    chunks_created: int = 0
    hs_codes_found: int = 0           # occurrences de codes SH rencontrées
    hs_codes_created: int = 0         # codes SH nouvellement insérés
    duplicates: int = 0              # occurrences d'un code SH déjà connu (mis à jour)
    descriptions_found: int = 0       # occurrences avec description officielle
    sections_count: int = 0           # sections distinctes rencontrées
    chapters_count: int = 0           # chapitres distincts rencontrés
    references_created: int = 0       # références documentaires (traçabilité)
    execution_ms: int = 0             # temps d'exécution de l'import
    taxes_created: int = 0            # taxes rattachées à un code SH
    authorizations_created: int = 0   # autorisations rattachées à un code SH
    tax_tables_found: int = 0
    authorizations_found: int = 0
    ocr_pages: int = 0
    warnings: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    def as_stats(self) -> dict:
        return {
            "total_pages": self.total_pages,
            "processed_pages": self.processed_pages,
            "chunks_created": self.chunks_created,
            "hs_codes_found": self.hs_codes_found,
            "hs_codes_created": self.hs_codes_created,
            "duplicates": self.duplicates,
            "descriptions_found": self.descriptions_found,
            "sections_count": self.sections_count,
            "chapters_count": self.chapters_count,
            "references_created": self.references_created,
            "execution_ms": self.execution_ms,
            "taxes_created": self.taxes_created,
            "authorizations_created": self.authorizations_created,
            "tax_tables_found": self.tax_tables_found,
            "authorizations_found": self.authorizations_found,
            "ocr_pages": self.ocr_pages,
            "warnings": len(self.warnings),
            "errors": len(self.errors),
        }
