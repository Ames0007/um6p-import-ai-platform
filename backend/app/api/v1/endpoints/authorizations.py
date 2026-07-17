"""Endpoints Autorisations."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reference import AuthorizationRead
from app.services.reference_service import authorization_service

router = APIRouter(prefix="/authorizations", tags=["Autorisations"])


@router.get("/hs-code/{hs_code_id}", response_model=list[AuthorizationRead])
def authorizations_by_hs_code(
    hs_code_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[AuthorizationRead]:
    return list(authorization_service.by_hs_code(db, hs_code_id))
