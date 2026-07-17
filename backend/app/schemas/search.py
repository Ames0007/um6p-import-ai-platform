"""Schémas de la recherche dans la base de connaissances."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Traçabilité affichable : document / chapitre / page."""

    document_id: uuid.UUID
    document_title: str
    chapter: str | None = None
    section: str | None = None
    page: int | None = None

    def label(self) -> str:
        parts = [self.document_title]
        if self.chapter:
            parts.append(self.chapter)
        if self.page is not None:
            parts.append(f"Page {self.page}")
        return " — ".join(parts)


class SearchHit(BaseModel):
    chunk_id: uuid.UUID
    excerpt: str
    score: float | None = None
    hs_codes: list[str] = Field(default_factory=list)
    citation: Citation


class SearchResponse(BaseModel):
    query: str
    mode: str  # "semantique" | "texte"
    total: int
    hits: list[SearchHit] = Field(default_factory=list)
