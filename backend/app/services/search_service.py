"""Recherche dans la base de connaissances (sémantique + repli plein texte).

- Si des embeddings sont disponibles (`EMBEDDINGS_ENABLED`), on classe les
  chunks par distance cosinus (pgvector).
- Sinon, on se rabat sur une recherche textuelle insensible à la casse.

Chaque résultat porte sa traçabilité (document / chapitre / page).
"""
from __future__ import annotations

import unicodedata
from typing import Sequence

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.ingestion.embeddings import get_embedding_provider
from app.models.document import Document
from app.models.knowledge import HsReference, TextChunk
from app.schemas.search import Citation, SearchHit, SearchResponse

EXCERPT_MAX = 320
_ACCENTS = "àâäáãéèêëíìîïóòôöõúùûüçñ"
_PLAIN = "aaaaaeeeeiiiiooooouuuucn"


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


class SearchService:
    def _hs_codes_for(
        self, db: Session, document_id, page: int | None
    ) -> list[str]:
        if page is None:
            return []
        rows = db.execute(
            select(distinct(HsReference.hs_code)).where(
                HsReference.document_id == document_id,
                HsReference.page == page,
            )
        ).scalars().all()
        return list(rows)

    def _excerpt(self, text: str) -> str:
        text = " ".join(text.split())
        return text[:EXCERPT_MAX] + ("…" if len(text) > EXCERPT_MAX else "")

    def _to_hit(
        self, db: Session, chunk: TextChunk, document: Document, score: float | None
    ) -> SearchHit:
        return SearchHit(
            chunk_id=chunk.id,
            excerpt=self._excerpt(chunk.chunk_text),
            score=score,
            hs_codes=self._hs_codes_for(db, document.id, chunk.page),
            citation=Citation(
                document_id=document.id,
                document_title=document.title,
                chapter=chunk.chapter,
                section=chunk.section,
                page=chunk.page,
            ),
        )

    def search(self, db: Session, query: str, *, limit: int = 20) -> SearchResponse:
        query = query.strip()
        if not query:
            return SearchResponse(query=query, mode="texte", total=0, hits=[])

        provider = get_embedding_provider()
        if provider.available:
            vector = provider.embed([query])[0]
            if vector is not None:
                return self._semantic_search(db, query, vector, limit)

        return self._text_search(db, query, limit)

    def _semantic_search(
        self, db: Session, query: str, vector, limit: int
    ) -> SearchResponse:
        distance = TextChunk.embedding.cosine_distance(vector).label("distance")
        stmt = (
            select(TextChunk, Document, distance)
            .join(Document, Document.id == TextChunk.document_id)
            .where(TextChunk.embedding.isnot(None))
            .order_by(distance)
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        hits = [
            self._to_hit(db, chunk, document, round(1 - float(dist), 4))
            for chunk, document, dist in rows
        ]
        return SearchResponse(
            query=query, mode="semantique", total=len(hits), hits=hits
        )

    def _text_search(self, db: Session, query: str, limit: int) -> SearchResponse:
        # Recherche plein texte insensible à la casse ET aux accents (portable).
        pattern = f"%{_norm(query)}%"
        folded = func.translate(func.lower(TextChunk.chunk_text), _ACCENTS, _PLAIN)
        stmt = (
            select(TextChunk, Document)
            .join(Document, Document.id == TextChunk.document_id)
            .where(folded.like(pattern))
            .limit(limit)
        )
        rows: Sequence = db.execute(stmt).all()
        hits = [self._to_hit(db, chunk, document, None) for chunk, document in rows]
        return SearchResponse(query=query, mode="texte", total=len(hits), hits=hits)


search_service = SearchService()
