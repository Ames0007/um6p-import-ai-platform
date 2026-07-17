"""Modèle Historique d'import (exécutions du pipeline d'ingestion)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import ImportStatus

if TYPE_CHECKING:
    from app.models.document import Document


class ImportHistory(UUIDMixin, TimestampMixin, Base):
    """Trace d'une exécution d'ingestion : temps, statut, erreurs, progression."""

    __tablename__ = "import_history"

    document_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[ImportStatus] = mapped_column(
        SAEnum(ImportStatus, name="import_status"),
        default=ImportStatus.EN_COURS,
        nullable=False,
    )

    # Progression (pour l'affichage temps réel côté client).
    current_page: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Erreurs détaillées et statistiques d'extraction (structuré).
    errors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="imports")

    @property
    def duration_seconds(self) -> float | None:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ImportHistory doc={self.document_id} [{self.status.value}]>"
