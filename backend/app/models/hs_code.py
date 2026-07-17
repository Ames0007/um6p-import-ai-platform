"""Modèle Code SH (Système Harmonisé)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.authorization import Authorization
    from app.models.product import Product
    from app.models.tax import Tax

# Dimension du vecteur d'embedding (à ajuster selon le modèle utilisé).
EMBEDDING_DIM = 1536


class HsCode(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "hs_codes"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description_fr: Mapped[str] = mapped_column(Text, nullable=False)
    chapter: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Recherche sémantique (pgvector) — alimentée hors ligne, jamais par le LLM.
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True
    )

    taxes: Mapped[list["Tax"]] = relationship(
        back_populates="hs_code", cascade="all, delete-orphan"
    )
    authorizations: Mapped[list["Authorization"]] = relationship(
        back_populates="hs_code", cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship(back_populates="hs_code")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<HsCode {self.code}>"
