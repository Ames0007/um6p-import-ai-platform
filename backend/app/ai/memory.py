"""Mémoire conversationnelle : historique + « focus » courant (produit / code SH).

Le focus permet de résoudre les questions de suivi (« Et les taxes ? » →
le produit évoqué précédemment). Il est stocké dans `Message.sources["_focus"]`
du dernier message de l'assistant, sans modifier le schéma.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation, Message
from app.models.enums import MessageRole


@dataclass
class Focus:
    product_id: str | None = None
    product_name: str | None = None
    hs_code_id: str | None = None
    hs_code: str | None = None

    def is_empty(self) -> bool:
        return not (self.product_id or self.hs_code_id)

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "hs_code_id": self.hs_code_id,
            "hs_code": self.hs_code,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "Focus":
        data = data or {}
        return cls(
            product_id=data.get("product_id"),
            product_name=data.get("product_name"),
            hs_code_id=data.get("hs_code_id"),
            hs_code=data.get("hs_code"),
        )


class ConversationMemory:
    def get_or_create(
        self, db: Session, conversation_id: uuid.UUID | None
    ) -> Conversation:
        if conversation_id:
            conv = db.get(Conversation, conversation_id)
            if conv:
                return conv
        conv = Conversation()
        db.add(conv)
        db.flush()
        return conv

    def history(self, db: Session, conversation_id: uuid.UUID) -> list[dict]:
        """Derniers messages (rôle/contenu), limités à AI_HISTORY_TURNS."""
        rows = db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(settings.AI_HISTORY_TURNS)
        ).scalars().all()
        return [
            {"role": m.role.value, "content": m.content} for m in reversed(rows)
        ]

    def current_focus(self, db: Session, conversation_id: uuid.UUID) -> Focus:
        row = db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role == MessageRole.ASSISTANT,
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if row and isinstance(row.sources, dict):
            return Focus.from_dict(row.sources.get("_focus"))
        return Focus()

    def save_turn(
        self,
        db: Session,
        conversation: Conversation,
        *,
        question: str,
        answer: str,
        sources: list[dict] | None = None,
        focus: Focus | None = None,
    ) -> None:
        db.add(
            Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=question,
            )
        )
        payload = {"items": sources or []}
        if focus and not focus.is_empty():
            payload["_focus"] = focus.to_dict()
        db.add(
            Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=answer,
                sources=payload,
            )
        )
        db.commit()


memory = ConversationMemory()
