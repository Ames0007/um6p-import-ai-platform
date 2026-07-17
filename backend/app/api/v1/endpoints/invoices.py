"""Endpoints Factures."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.invoice import InvoiceRead
from app.services.invoice_service import invoice_service

router = APIRouter(prefix="/invoices", tags=["Factures"])


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> list[InvoiceRead]:
    return list(invoice_service.list(db, skip=skip, limit=limit))


@router.post("/upload", response_model=InvoiceRead, status_code=201)
def upload_invoice(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> InvoiceRead:
    """Importe une facture (PDF, Excel, Word, image).

    Le fichier est persisté ; l'analyse IA sera ajoutée ultérieurement.
    """
    return invoice_service.save_upload(db, file)  # type: ignore[return-value]


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db)) -> InvoiceRead:
    invoice = invoice_service.get(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    return invoice  # type: ignore[return-value]
