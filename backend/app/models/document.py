"""Modèle Document (base de connaissances officielle)."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import DocumentCategory, DocumentStatus

if TYPE_CHECKING:
    from app.models.import_history import ImportHistory
    from app.models.knowledge import DocumentReference, HsReference, TextChunk


class Document(UUIDMixin, TimestampMixin, Base):
    """Document officiel importé dans la bibliothèque documentaire."""

    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(
        SAEnum(DocumentCategory, name="document_category"),
        default=DocumentCategory.AUTRE,
        nullable=False,
        index=True,
    )
    version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    number_of_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="fr", nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status"),
        default=DocumentStatus.EN_ATTENTE,
        nullable=False,
        index=True,
    )

    # Empreinte SHA-256 du fichier — détection des doublons / versions modifiées.
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_scanned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ocr_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Relations
    chunks: Mapped[list["TextChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    hs_references: Mapped[list["HsReference"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    document_references: Mapped[list["DocumentReference"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    imports: Mapped[list["ImportHistory"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ImportHistory.start_time.desc()",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Document {self.title} [{self.status.value}]>"
