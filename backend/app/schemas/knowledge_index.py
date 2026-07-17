"""Schémas de la recherche par concept dans l'Index de connaissance (lecture seule).

Exposent le service `knowledge_index_search` existant sans passer par l'IA :
recherche instantanée (cartes structurées) et suggestions (autocomplétion).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeResult(BaseModel):
    """Un concept recherchable (code SH, produit, chapitre, document…)."""

    id: str
    type: str  # HS_CODE | PRODUCT | CHAPTER | SECTION | DOCUMENT | SUPPLIER | AUTHORIZATION | TAX
    reference: str | None = None
    title: str | None = None
    chapter: str | None = None
    section: str | None = None
    document_id: str | None = None
    document_title: str | None = None
    page: int | None = None
    description: str | None = None
    taxes: str | None = None
    authorizations: str | None = None
    source_table: str
    source_pk: str | None = None
    score: float


class LookupResponse(BaseModel):
    query: str
    # exact_hs | chapter | product | document | ranked | empty
    mode: str
    results: list[KnowledgeResult] = Field(default_factory=list)
    # Aperçu chapitre : codes SH du chapitre (quand mode == "chapter").
    chapter_codes: list[KnowledgeResult] = Field(default_factory=list)


class Suggestion(BaseModel):
    label: str
    sublabel: str | None = None
    type: str
    reference: str | None = None


class SuggestResponse(BaseModel):
    query: str
    suggestions: list[Suggestion] = Field(default_factory=list)
