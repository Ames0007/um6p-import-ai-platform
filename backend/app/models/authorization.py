"""Modèle Autorisation (exigence réglementaire d'importation)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import AuthorizationStatus

if TYPE_CHECKING:
    from app.models.hs_code import HsCode


class Authorization(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "authorizations"

    hs_code_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("hs_codes.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[AuthorizationStatus] = mapped_column(
        SAEnum(AuthorizationStatus, name="authorization_status"),
        default=AuthorizationStatus.NON_REQUISE,
        nullable=False,
    )
    # Organisme / ministère émetteur.
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ministry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Documents requis : ["Certificat X", "Facture proforma", ...]
    required_documents: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    legal_reference: Mapped[str | None] = mapped_column(String(300), nullable=True)
    processing_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)

    hs_code: Mapped["HsCode"] = relationship(back_populates="authorizations")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Authorization {self.status.value}>"
