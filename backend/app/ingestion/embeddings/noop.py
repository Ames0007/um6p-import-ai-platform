"""Fournisseur d'embeddings par défaut : ne calcule rien (stockage NULL)."""
from __future__ import annotations

from app.ingestion.embeddings.base import EmbeddingProvider


class NoOpEmbeddingProvider(EmbeddingProvider):
    name = "noop"

    @property
    def available(self) -> bool:
        return False

    def embed(self, texts: list[str]) -> list[list[float] | None]:
        return [None for _ in texts]
