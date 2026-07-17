"""Modèle Alias Produit (autres désignations d'un produit).

Améliore la recherche de l'IA : « Microscope Leica », « Leica DM750 »,
« Microscope biologique »… pointent tous vers le même produit.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.product import Product


class ProductAlias(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "product_aliases"

    product_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    product: Mapped["Product"] = relationship(back_populates="aliases")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProductAlias {self.alias}>"
