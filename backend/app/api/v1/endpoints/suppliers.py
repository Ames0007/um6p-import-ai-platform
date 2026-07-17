"""Endpoints Fournisseurs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.procurement import SupplierRead
from app.services.procurement_service import supplier_service

router = APIRouter(prefix="/suppliers", tags=["Fournisseurs"])


@router.get("", response_model=list[SupplierRead])
def list_suppliers(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> list[SupplierRead]:
    return list(supplier_service.list(db, skip=skip, limit=limit))
