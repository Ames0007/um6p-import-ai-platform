"""Endpoints de détail enrichi : Produit et Code SH."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.detail import HsCodeDetail, ProductDetail
from app.services.detail_service import detail_service

router = APIRouter(tags=["Admin · Détails"])


@router.get("/products/{product_id}/detail", response_model=ProductDetail)
def product_detail(product_id: uuid.UUID, db: Session = Depends(get_db)) -> ProductDetail:
    detail = detail_service.product_detail(db, product_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return detail


@router.get("/hs-codes/{hs_code_id}/detail", response_model=HsCodeDetail)
def hs_code_detail(hs_code_id: uuid.UUID, db: Session = Depends(get_db)) -> HsCodeDetail:
    detail = detail_service.hs_code_detail(db, hs_code_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Code SH introuvable.")
    return detail
