"""Endpoints Codes SH."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reference import HsCodeRead
from app.services.reference_service import hs_code_service

router = APIRouter(prefix="/hs-codes", tags=["Codes SH"])


@router.get("", response_model=list[HsCodeRead])
def list_hs_codes(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> list[HsCodeRead]:
    return list(hs_code_service.list(db, skip=skip, limit=limit))


@router.get("/search", response_model=list[HsCodeRead])
def search_hs_codes(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> list[HsCodeRead]:
    return list(hs_code_service.search(db, q))
