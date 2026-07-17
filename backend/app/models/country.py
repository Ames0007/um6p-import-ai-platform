"""Modèle Pays."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.supplier import Supplier
    from app.models.tax import Tax


class Country(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), unique=True, index=True)  # ISO 3166-1
    name_fr: Mapped[str] = mapped_column(String(120), nullable=False)

    suppliers: Mapped[list["Supplier"]] = relationship(back_populates="country")
    taxes: Mapped[list["Tax"]] = relationship(back_populates="country")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Country {self.code} {self.name_fr}>"
