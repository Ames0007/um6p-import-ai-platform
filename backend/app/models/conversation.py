"""Modèles Conversation et Message (historique du chat IA)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import MessageRole

if TYPE_CHECKING:
    pass


class Conversation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Références de la base ayant servi à la réponse (traçabilité).
    sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
