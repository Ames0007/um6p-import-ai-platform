"""Modèle Taxe (droits de douane, TVA, taxes parafiscales)."""
from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.country import Country
    from app.models.hs_code import HsCode


class Tax(UUIDMixin, TimestampMixin, Base):
    """Barème de taxes pour un code SH. L'historique = plusieurs lignes
    ordonnées par `effective_date`."""

    __tablename__ = "taxes"

    hs_code_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("hs_codes.id", ondelete="CASCADE"), index=True
    )
    country_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True
    )

    # Composantes de taxation (en pourcentage).
    import_duty: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    vat: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    parafiscal_tax: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    # Taxes additionnelles : [{"label": ..., "rate_percent": ...}]
    additional_taxes: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    notes_fr: Mapped[str | None] = mapped_column(Text, nullable=True)

    hs_code: Mapped["HsCode"] = relationship(back_populates="taxes")
    country: Mapped["Country | None"] = relationship(back_populates="taxes")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tax hs={self.hs_code_id} DI={self.import_duty} TVA={self.vat}>"
