"""Modèle Fournisseur."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.country import Country
    from app.models.purchase_history import PurchaseHistory


class Supplier(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    country_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True
    )
    website: Mapped[str | None] = mapped_column(String(300), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Délai d'approvisionnement moyen (jours).
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    country: Mapped["Country | None"] = relationship(back_populates="suppliers")
    purchases: Mapped[list["PurchaseHistory"]] = relationship(
        back_populates="supplier"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Supplier {self.name}>"
