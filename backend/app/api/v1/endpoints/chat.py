"""Endpoints du copilote IA (question/réponse + streaming SSE)."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.session import SessionLocal
from app.schemas.chat import AskRequest, AskResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)) -> AskResponse:
    """Pose une question à l'assistant (réponse complète, non diffusée).

    La réponse est exclusivement fondée sur la base de connaissances UM6P et
    les documents officiels. Aucune donnée n'est inventée.
    """
    return chat_service.ask(db, payload)


@router.post("/stream")
def stream(payload: AskRequest) -> StreamingResponse:
    """Réponse diffusée en Server-Sent Events (`text/event-stream`).

    Chaque ligne : `data: {json}` — types d'événements : meta, delta, done.
    """

    def event_generator():
        # Session dédiée : le générateur survit à la requête pendant le streaming.
        db = SessionLocal()
        try:
            for event in chat_service.stream(db, payload):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
