"""Génération d'embeddings par « hooks » enfichables.

Par défaut, aucun embedding n'est calculé (NoOpEmbeddingProvider) : les chunks
sont stockés avec `embedding = NULL` et la recherche se rabat sur le texte
(trigramme / plein texte). Pour activer la recherche sémantique, mettre
`EMBEDDINGS_ENABLED=true` et brancher un fournisseur réel.
"""
from __future__ import annotations

from app.core.config import settings
from app.ingestion.embeddings.base import EmbeddingProvider
from app.ingestion.embeddings.noop import NoOpEmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    if settings.EMBEDDINGS_ENABLED:
        # Brancher ici un fournisseur réel (ex. service d'embeddings interne).
        # from app.ingestion.embeddings.remote import RemoteEmbeddingProvider
        # return RemoteEmbeddingProvider()
        return NoOpEmbeddingProvider()
    return NoOpEmbeddingProvider()


__all__ = ["EmbeddingProvider", "NoOpEmbeddingProvider", "get_embedding_provider"]
