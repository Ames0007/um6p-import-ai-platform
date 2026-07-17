"""Journal des requêtes IA (observabilité).

Interne uniquement : n'est jamais renvoyé au client (le prompt et les données
récupérées ne doivent pas fuiter côté API).
"""
from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDMixin


class AiRequestLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ai_request_logs"

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # Compréhension du langage (JSON produit par Claude à l'étape 1).
    understanding: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Requête réellement transmise au retriever (jamais la phrase brute).
    retriever_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SQL exécuté pendant la récupération (traçabilité).
    executed_sql: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Récapitulatifs structurés (pas la base entière).
    retrieved_records: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    retrieved_documents: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)

    execution_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AiRequestLog {self.intent} {self.confidence}>"
