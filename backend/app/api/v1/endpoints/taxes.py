"""Endpoints Taxes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reference import TaxRead
from app.services.reference_service import tax_service

router = APIRouter(prefix="/taxes", tags=["Taxes"])


@router.get("/hs-code/{hs_code_id}", response_model=list[TaxRead])
def taxes_by_hs_code(
    hs_code_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[TaxRead]:
    return list(tax_service.by_hs_code(db, hs_code_id))
