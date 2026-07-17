"""Modèles de connaissance extraite : chunks, références SH, citations."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base_class import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.product import Product


class TextChunk(UUIDMixin, TimestampMixin, Base):
    """Fragment de texte recherchable, avec traçabilité (page/section)."""

    __tablename__ = "text_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    chapter: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Embedding pour la recherche sémantique (alimenté par un hook, jamais le LLM).
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.EMBEDDING_DIM), nullable=True
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TextChunk doc={self.document_id} p={self.page} #{self.chunk_index}>"


class HsReference(UUIDMixin, TimestampMixin, Base):
    """Occurrence d'un code SH détectée dans un document (avec localisation)."""

    __tablename__ = "hs_references"

    document_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    hs_code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapter: Mapped[str | None] = mapped_column(String(120), nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="hs_references")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<HsReference {self.hs_code} p={self.page}>"


class DocumentReference(UUIDMixin, TimestampMixin, Base):
    """Citation reliant un produit interne à un passage précis d'un document.

    Support de la traçabilité affichée par l'IA :
    « Source : Code des Douanes 2022 — Chapitre 84 — Page 154 ».
    """

    __tablename__ = "document_references"

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paragraph: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation: Mapped[str | None] = mapped_column(String(500), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="document_references")
    product: Mapped["Product | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DocumentReference doc={self.document_id} p={self.page}>"
