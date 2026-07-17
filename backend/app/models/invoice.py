"""Modèle Facture (fichier importé + statut d'analyse)."""
from __future__ import annotations

from sqlalchemy import BigInteger, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import InvoiceStatus


class Invoice(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "invoices"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(InvoiceStatus, name="invoice_status"),
        default=InvoiceStatus.RECUE,
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Invoice {self.filename} [{self.status.value}]>"
