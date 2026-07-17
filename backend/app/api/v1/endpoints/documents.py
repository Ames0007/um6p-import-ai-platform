"""Endpoints de la bibliothèque documentaire et du moteur d'ingestion."""
from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.ingestion.extractors.base import UnsupportedFormatError
from app.models.enums import DocumentCategory
from app.schemas.document import (
    DocumentRead,
    DocumentUpdateMeta,
    ImportDispatchResult,
    ImportRunRead,
)
from app.services.document_service import DuplicateDocumentError, document_service

router = APIRouter(prefix="/documents", tags=["Bibliothèque documentaire"])


@router.get("", response_model=list[DocumentRead])
def list_documents(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    docs = document_service.list(db, skip=skip, limit=limit)
    return [document_service.to_read(db, d) for d in docs]


@router.post("/import", response_model=ImportDispatchResult, status_code=201)
def import_documents(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    category: DocumentCategory | None = Form(None),
    version: str | None = Form(None),
    publication_date: date | None = Form(None),
    language: str | None = Form(None),
    allow_duplicate: bool = Form(False),
    db: Session = Depends(get_db),
) -> ImportDispatchResult:
    """Importe un document (PDF, DOCX, XLSX, CSV) ou une archive ZIP de PDF.

    L'ingestion est planifiée en arrière-plan ; suivez la progression via
    `GET /documents/{id}/progress`.
    """
    meta = DocumentUpdateMeta(
        title=title,
        category=category,
        version=version,
        publication_date=publication_date,
        language=language,
    )
    try:
        created, duplicates, mode = document_service.ingest_upload(
            db, file, meta=meta, allow_duplicate=allow_duplicate
        )
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    if not created and duplicates:
        raise HTTPException(
            status_code=409,
            detail=f"Document(s) déjà présent(s) : {', '.join(duplicates)}",
        )

    return ImportDispatchResult(
        documents=[document_service.to_read(db, d) for d in created],
        mode=mode,
        duplicates=duplicates,
    )


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> DocumentRead:
    document = document_service.get(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    return document_service.to_read(db, document)


@router.get("/{document_id}/progress", response_model=ImportRunRead | None)
def get_progress(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> ImportRunRead | None:
    document = document_service.get(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    return document_service.to_read(db, document).last_import


@router.post("/{document_id}/reimport", response_model=dict)
def reimport_document(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> dict:
    document = document_service.get(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    mode = document_service.reimport(db, document)
    return {"mode": mode, "document_id": str(document.id)}


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: uuid.UUID, db: Session = Depends(get_db)
):
    document = document_service.get(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    document_service.delete(db, document)


@router.get("/{document_id}/file")
def download_document(
    document_id: uuid.UUID,
    inline: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Télécharge (`inline=false`) ou affiche (`inline=true`) le fichier source."""
    document = document_service.get(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    path = Path(document.storage_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Fichier source introuvable.")
    disposition = "inline" if inline else "attachment"
    return FileResponse(
        path,
        filename=document.filename,
        content_disposition_type=disposition,
    )
