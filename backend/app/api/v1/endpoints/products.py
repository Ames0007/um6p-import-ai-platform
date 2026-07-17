"""Endpoints Produits."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.procurement import ProductRead
from app.services.product_service import product_service

router = APIRouter(prefix="/products", tags=["Produits"])


@router.get("", response_model=list[ProductRead])
def list_products(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> list[ProductRead]:
    return list(product_service.list(db, skip=skip, limit=limit))


@router.get("/search", response_model=list[ProductRead])
def search_products(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> list[ProductRead]:
    return list(product_service.search(db, q))


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)) -> ProductRead:
    product = product_service.get(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return product  # type: ignore[return-value]
