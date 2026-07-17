"""Endpoints de l'assistant d'import (aperçu + validation)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_subject, get_db
from app.schemas.importer import (
    ImportCommitRequest,
    ImportPreviewResponse,
    ImportReport,
)
from app.services.importer import import_service
from app.services.importer.specs import SPECS

router = APIRouter(prefix="/import", tags=["Admin · Import"])


@router.get("/resources")
def importable_resources() -> dict:
    """Liste les ressources importables et leurs champs cibles."""
    return {
        name: [tf.model_dump() for tf in spec.target_fields]
        for name, spec in SPECS.items()
    }


@router.post("/preview", response_model=ImportPreviewResponse)
def preview_import(
    resource: str = Form(...),
    file: UploadFile = File(...),
) -> ImportPreviewResponse:
    if resource not in SPECS:
        raise HTTPException(status_code=404, detail="Ressource inconnue.")
    try:
        return import_service.preview(file, resource)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc


@router.post("/commit", response_model=ImportReport)
def commit_import(
    req: ImportCommitRequest,
    db: Session = Depends(get_db),
    subject: str | None = Depends(get_current_subject),
) -> ImportReport:
    if req.resource not in SPECS:
        raise HTTPException(status_code=404, detail="Ressource inconnue.")
    try:
        return import_service.commit(db, req, actor=subject or "système")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
