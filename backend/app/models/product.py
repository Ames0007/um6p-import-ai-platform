"""Modèle Produit (référentiel interne — base de connaissances)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import ProductStatus
from app.models.hs_code import EMBEDDING_DIM

if TYPE_CHECKING:
    from app.models.country import Country
    from app.models.hs_code import HsCode
    from app.models.product_alias import ProductAlias
    from app.models.purchase_history import PurchaseHistory
    from app.models.supplier import Supplier


class Product(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "products"

    # Identité
    reference: Mapped[str | None] = mapped_column(
        String(120), nullable=True, index=True  # référence interne
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list, server_default="{}", nullable=False
    )

    # Rattachements
    country_of_origin_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True
    )
    preferred_supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True, index=True
    )
    hs_code_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("hs_codes.id"), nullable=True, index=True
    )

    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(ProductStatus, name="product_status"),
        default=ProductStatus.ACTIF,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Recherche sémantique (pgvector)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True
    )

    # Relations
    hs_code: Mapped["HsCode | None"] = relationship(back_populates="products")
    country_of_origin: Mapped["Country | None"] = relationship(
        foreign_keys=[country_of_origin_id]
    )
    preferred_supplier: Mapped["Supplier | None"] = relationship(
        foreign_keys=[preferred_supplier_id]
    )
    aliases: Mapped[list["ProductAlias"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    purchases: Mapped[list["PurchaseHistory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Product {self.name}>"
