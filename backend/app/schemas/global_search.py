"""Schémas de la recherche globale de l'administration."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class SearchEntity(BaseModel):
    """Résultat léger et cliquable."""

    id: uuid.UUID
    label: str
    sublabel: str | None = None


class GlobalSearchResponse(BaseModel):
    query: str
    products: list[SearchEntity] = Field(default_factory=list)
    aliases: list[SearchEntity] = Field(default_factory=list)
    hs_codes: list[SearchEntity] = Field(default_factory=list)
    suppliers: list[SearchEntity] = Field(default_factory=list)
    purchases: list[SearchEntity] = Field(default_factory=list)
    authorizations: list[SearchEntity] = Field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(
            len(x)
            for x in (
                self.products,
                self.aliases,
                self.hs_codes,
                self.suppliers,
                self.purchases,
                self.authorizations,
            )
        )
