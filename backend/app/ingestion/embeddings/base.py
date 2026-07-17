"""Contrat des fournisseurs d'embeddings."""
from __future__ import annotations

import abc


class EmbeddingProvider(abc.ABC):
    name: str = "base"

    @property
    @abc.abstractmethod
    def available(self) -> bool:
        """Indique si des embeddings réels sont produits."""

    @abc.abstractmethod
    def embed(self, texts: list[str]) -> list[list[float] | None]:
        """Retourne un vecteur (ou None) par texte, dans le même ordre."""
