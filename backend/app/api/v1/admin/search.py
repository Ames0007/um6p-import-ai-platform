"""Endpoint de recherche globale de l'administration."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.global_search import GlobalSearchResponse
from app.services.global_search_service import global_search_service

router = APIRouter(prefix="/search", tags=["Admin · Recherche"])


@router.get("", response_model=GlobalSearchResponse)
def global_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> GlobalSearchResponse:
    return global_search_service.search(db, q)
