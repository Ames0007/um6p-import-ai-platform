"""Service Chat — délègue au pipeline IA (Phase 4).

⚠️ Toute réponse est ancrée dans les données vérifiées (PostgreSQL + documents
officiels). En l'absence de contexte, aucune réponse n'est inventée.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.ai.pipeline import ai_pipeline
from app.schemas.chat import AskRequest, AskResponse


class ChatService:
    def ask(self, db: Session, payload: AskRequest) -> AskResponse:
        return ai_pipeline.ask(
            db, payload.question, conversation_id=payload.conversation_id
        )

    def stream(self, db: Session, payload: AskRequest) -> Iterator[dict]:
        return ai_pipeline.stream(
            db, payload.question, conversation_id=payload.conversation_id
        )


chat_service = ChatService()
