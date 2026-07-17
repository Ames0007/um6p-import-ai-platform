"""Modèle Historique des achats."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.country import Country
    from app.models.product import Product
    from app.models.supplier import Supplier


class PurchaseHistory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "purchase_history"

    product_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True, index=True
    )
    country_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True
    )

    invoice_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="MAD", nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    incoterm: Mapped[str | None] = mapped_column(String(10), nullable=True)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    product: Mapped["Product"] = relationship(back_populates="purchases")
    supplier: Mapped["Supplier | None"] = relationship(back_populates="purchases")
    country: Mapped["Country | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PurchaseHistory {self.unit_price} {self.currency}>"
