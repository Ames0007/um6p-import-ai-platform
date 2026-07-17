"""Endpoints Historique des achats."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.procurement import PurchaseHistoryRead
from app.services.procurement_service import purchase_history_service

router = APIRouter(prefix="/purchase-history", tags=["Historique des achats"])


@router.get("", response_model=list[PurchaseHistoryRead])
def list_purchase_history(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> list[PurchaseHistoryRead]:
    return list(purchase_history_service.list(db, skip=skip, limit=limit))


@router.get("/product/{product_id}", response_model=list[PurchaseHistoryRead])
def purchase_history_by_product(
    product_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[PurchaseHistoryRead]:
    return list(purchase_history_service.by_product(db, product_id))
