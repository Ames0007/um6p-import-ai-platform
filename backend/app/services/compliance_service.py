"""Service de l'analyse de conformité à l'import : orchestration + requêtes."""
from __future__ import annotations

import uuid
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance import exports
from app.core.config import settings
from app.models.compliance import AnalysisReport, ImportAnalysis
from app.models.enums import AnalysisStatus
from app.schemas.compliance import (
    AnalysisDetail,
    AnalysisItemRead,
    AnalysisListItem,
    AnalysisProgress,
    FindingRead,
)
from app.services.invoice_service import invoice_service
from app.workers import dispatch_analysis


class ComplianceService:
    # -------- création --------
    def create_from_uploads(
        self, db: Session, files: list[UploadFile]
    ) -> tuple[list[ImportAnalysis], str]:
        analyses: list[ImportAnalysis] = []
        mode = "inline"
        for file in files:
            invoice = invoice_service.save_upload(db, file)
            analysis = ImportAnalysis(
                invoice_id=invoice.id,
                original_filename=invoice.filename,
                storage_path=invoice.stored_path,
                ocr_provider=settings.OCR_PROVIDER,
                status=AnalysisStatus.EN_ATTENTE,
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            analyses.append(analysis)
            mode = dispatch_analysis(analysis.id, resume=True)
        return analyses, mode

    # -------- lecture --------
    def list(
        self, db: Session, *, skip: int = 0, limit: int = 50
    ) -> Sequence[ImportAnalysis]:
        return db.execute(
            select(ImportAnalysis)
            .order_by(ImportAnalysis.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).scalars().all()

    def get(self, db: Session, analysis_id: uuid.UUID) -> ImportAnalysis | None:
        return db.get(ImportAnalysis, analysis_id)

    def detail(self, db: Session, analysis: ImportAnalysis) -> AnalysisDetail:
        detail = AnalysisDetail.model_validate(analysis)
        detail.items = [AnalysisItemRead.model_validate(i) for i in analysis.items]
        detail.findings = [FindingRead.model_validate(f) for f in analysis.findings]
        detail.report = analysis.report.content if analysis.report else None
        return detail

    def progress(self, analysis: ImportAnalysis) -> AnalysisProgress:
        pct = (
            round(100 * analysis.processed_items / analysis.total_items, 1)
            if analysis.total_items else 0.0
        )
        return AnalysisProgress(
            id=analysis.id,
            status=analysis.status,
            total_items=analysis.total_items,
            processed_items=analysis.processed_items,
            progress_percent=pct,
            overall_risk=analysis.overall_risk,
        )

    def to_list_item(self, analysis: ImportAnalysis) -> AnalysisListItem:
        return AnalysisListItem.model_validate(analysis)

    # -------- reprise --------
    def resume_interrupted(self, db: Session) -> int:
        stuck = db.execute(
            select(ImportAnalysis).where(
                ImportAnalysis.status == AnalysisStatus.EN_COURS
            )
        ).scalars().all()
        for analysis in stuck:
            dispatch_analysis(analysis.id, resume=True)
        return len(stuck)

    # -------- exports --------
    def export(
        self, db: Session, analysis: ImportAnalysis, fmt: str
    ) -> tuple[bytes, str, str]:
        report = db.execute(
            select(AnalysisReport).where(AnalysisReport.analysis_id == analysis.id)
        ).scalar_one_or_none()
        content = report.content if report else {"detected_products": []}
        base = f"analyse_{analysis.invoice_number or str(analysis.id)[:8]}"

        if fmt == "csv":
            return exports.to_csv(content), "text/csv", f"{base}.csv"
        if fmt == "xlsx":
            return (
                exports.to_xlsx(content),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                f"{base}.xlsx",
            )
        if fmt == "pdf":
            pdf = exports.build_pdf(content)
            if pdf is not None:
                return pdf, "application/pdf", f"{base}.pdf"
            # Repli HTML si reportlab absent.
            return (
                exports.build_html(content).encode("utf-8"),
                "text/html",
                f"{base}.html",
            )
        raise ValueError(f"Format d'export non pris en charge : {fmt}")


compliance_service = ComplianceService()
