"""Piste d'audit : journalise chaque modification du référentiel."""
from __future__ import annotations

import uuid

from sqlalchemy import Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import AuditAction


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, name="audit_action"), nullable=False, index=True
    )
    actor: Mapped[str] = mapped_column(String(200), default="système", nullable=False)
    # {champ: {"old": ..., "new": ...}}
    changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog {self.action.value} {self.entity_type}>"
