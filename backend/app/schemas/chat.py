"""Schémas du copilote IA achats & import."""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["elevee", "moyenne", "faible", "aucune"]


class Source(BaseModel):
    """Origine d'une information (traçabilité)."""

    type: str  # ex. "produit", "taxe", "historique", "document"
    label: str
    id: str | None = None


class DocumentCitationOut(BaseModel):
    document_title: str
    chapter: str | None = None
    page: int | None = None


class Candidate(BaseModel):
    """Proposition lorsqu'une désambiguïsation est nécessaire."""

    id: str
    label: str
    sublabel: str | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    conversation_id: uuid.UUID | None = None
    attachment_ids: list[uuid.UUID] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    conversation_id: uuid.UUID
    intent: str
    confidence: ConfidenceLevel
    sources: list[Source] = Field(default_factory=list)
    citations: list[DocumentCitationOut] = Field(default_factory=list)
    # Liste de sélection quand plusieurs produits correspondent.
    candidates: list[Candidate] = Field(default_factory=list)
    needs_clarification: bool = False
