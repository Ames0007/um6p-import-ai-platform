"""Endpoints de l'analyse de conformité à l'import."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.compliance import (
    AnalysisDetail,
    AnalysisDispatchResult,
    AnalysisListItem,
    AnalysisProgress,
)
from app.services.compliance_service import compliance_service
from app.workers import dispatch_analysis

router = APIRouter(prefix="/import-analysis", tags=["Analyse d'importation"])


@router.post("/upload", response_model=AnalysisDispatchResult, status_code=201)
def upload_invoices(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> AnalysisDispatchResult:
    """Importe une ou plusieurs factures et lance leur analyse en arrière-plan."""
    analyses, mode = compliance_service.create_from_uploads(db, files)
    return AnalysisDispatchResult(
        analyses=[compliance_service.to_list_item(a) for a in analyses],
        mode=mode,
    )


@router.get("", response_model=list[AnalysisListItem])
def list_analyses(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
) -> list[AnalysisListItem]:
    return [
        compliance_service.to_list_item(a)
        for a in compliance_service.list(db, skip=skip, limit=limit)
    ]


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: uuid.UUID, db: Session = Depends(get_db)) -> AnalysisDetail:
    analysis = compliance_service.get(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable.")
    return compliance_service.detail(db, analysis)


@router.get("/{analysis_id}/progress", response_model=AnalysisProgress)
def get_progress(analysis_id: uuid.UUID, db: Session = Depends(get_db)) -> AnalysisProgress:
    analysis = compliance_service.get(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable.")
    return compliance_service.progress(analysis)


@router.post("/{analysis_id}/reanalyze", response_model=dict)
def reanalyze(analysis_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    analysis = compliance_service.get(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable.")
    mode = dispatch_analysis(analysis.id, resume=False)
    return {"mode": mode, "analysis_id": str(analysis.id)}


@router.get("/{analysis_id}/export")
def export_analysis(
    analysis_id: uuid.UUID,
    format: str = Query("pdf", pattern="^(pdf|xlsx|csv)$"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    analysis = compliance_service.get(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable.")
    data, media_type, filename = compliance_service.export(db, analysis, format)
    return StreamingResponse(
        iter([data]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
