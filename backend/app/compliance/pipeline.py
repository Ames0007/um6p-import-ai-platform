"""Orchestrateur de l'analyse de conformité à l'import.

OCR → extraction → rapprochement → enrichissement → prix → conformité →
rapport. Traitement ligne par ligne, reprenable (resume) et idempotent, avec
suivi de progression persisté.
"""
from __future__ import annotations

import logging
import time
import uuid

from sqlalchemy import func, select

from app.compliance.enrichment import ProductEnrichment, enrichment_service
from app.compliance.matching import product_matcher
from app.compliance.ocr import extract_document
from app.compliance.parser import ParsedLine, invoice_parser
from app.compliance.pricing import analyze_price
from app.compliance.report import ItemReport, report_builder
from app.compliance.rules import Finding, evaluate_item
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.compliance import (
    AnalysisReport,
    ComplianceFinding,
    ImportAnalysis,
    ImportAnalysisItem,
    OCRResult,
    PriceAlert,
    ProductCandidate,
)
from app.models.enums import (
    AnalysisStatus,
    CandidateStatus,
    FindingType,
    ItemStatus,
    RiskLevel,
)
from app.models.product import Product
from app.models.supplier import Supplier

logger = logging.getLogger("compliance")


def run_analysis(analysis_id: uuid.UUID, *, resume: bool = True) -> None:
    db = SessionLocal()
    try:
        _AnalysisRun(db, analysis_id, resume=resume).execute()
    finally:
        db.close()


class _AnalysisRun:
    def __init__(self, db, analysis_id: uuid.UUID, *, resume: bool) -> None:
        self.db = db
        self.analysis_id = analysis_id
        self.resume = resume

    def execute(self) -> None:
        analysis = self.db.get(ImportAnalysis, self.analysis_id)
        if analysis is None:
            raise ValueError(f"Analyse introuvable : {self.analysis_id}")

        start = time.perf_counter()
        analysis.status = AnalysisStatus.EN_COURS
        analysis.error_message = None
        self.db.commit()

        try:
            self._process(analysis, start)
        except Exception as exc:  # échec global
            analysis.status = AnalysisStatus.ERREUR
            analysis.error_message = str(exc)[:2000]
            analysis.execution_ms = int((time.perf_counter() - start) * 1000)
            self.db.commit()
            logger.exception("Échec analyse %s", self.analysis_id)
            raise

    # ---------------- traitement ----------------
    def _process(self, analysis: ImportAnalysis, start: float) -> None:
        path = analysis.storage_path
        if not path:
            raise ValueError("Fichier de facture introuvable pour l'analyse.")

        if not self.resume:
            self._reset(analysis)

        # OCR / extraction (une fois).
        already_ocr = self.db.execute(
            select(func.count()).select_from(OCRResult).where(
                OCRResult.analysis_id == analysis.id
            )
        ).scalar_one()
        ocr_started = time.perf_counter()
        extraction = extract_document(path, analysis.ocr_provider)
        analysis.ocr_provider = extraction.provider
        if not already_ocr:
            self.db.add(
                OCRResult(
                    analysis_id=analysis.id,
                    provider=extraction.provider,
                    raw_text=extraction.text[:500_000] if extraction.text else "",
                    pages=extraction.pages,
                    confidence=extraction.confidence,
                    duration_ms=int((time.perf_counter() - ocr_started) * 1000),
                )
            )

        parsed = invoice_parser.parse(extraction.text)
        self._apply_metadata(analysis, parsed)

        lines = parsed.lines
        analysis.total_items = len(lines)
        self.db.commit()

        if not lines:
            self._finalize(analysis, start, no_lines=True)
            return

        start_index = analysis.processed_items if self.resume else 0
        for line in lines:
            if line.line_number <= start_index:
                continue
            self._process_line(analysis, line)
            analysis.processed_items = line.line_number
            self.db.commit()

        self._finalize(analysis, start)

    def _apply_metadata(self, analysis: ImportAnalysis, parsed) -> None:
        if not analysis.invoice_number:
            analysis.invoice_number = parsed.invoice_number
        if not analysis.invoice_date:
            analysis.invoice_date = parsed.invoice_date
        if not analysis.currency:
            analysis.currency = parsed.currency
        if not analysis.incoterm:
            analysis.incoterm = parsed.incoterm
        if not analysis.supplier_name_raw:
            analysis.supplier_name_raw = parsed.supplier_name

        if parsed.supplier_name and not analysis.supplier_id:
            supplier = self.db.execute(
                select(Supplier)
                .where(func.lower(Supplier.name).like(f"%{parsed.supplier_name.lower()}%"))
                .limit(1)
            ).scalar_one_or_none()
            if supplier:
                analysis.supplier_id = supplier.id

    def _process_line(self, analysis: ImportAnalysis, line: ParsedLine) -> None:
        match = product_matcher.match(self.db, line.product_name)
        unit_price = float(line.unit_price) if line.unit_price is not None else None

        item = ImportAnalysisItem(
            analysis_id=analysis.id,
            line_number=line.line_number,
            raw_text=line.raw_text,
            raw_product_name=line.product_name,
            raw_quantity=line.quantity,
            raw_unit_price=line.unit_price,
            raw_currency=line.currency,
            match_method=match.method,
            match_confidence=match.confidence,
            match_reason=match.reason,
        )

        enrichment: ProductEnrichment | None = None
        price = analyze_price(unit_price, None)

        if match.found and match.product is not None:
            product = match.product
            enrichment = enrichment_service.enrich(self.db, product)
            price = analyze_price(unit_price, enrichment.purchase_stats)
            self._fill_item(item, product, enrichment, price)
            item.status = ItemStatus.RAPPROCHE
        else:
            item.status = ItemStatus.A_VALIDER

        self.db.add(item)
        self.db.flush()

        # Candidat si non trouvé.
        if not match.found:
            self.db.add(
                ProductCandidate(
                    analysis_id=analysis.id,
                    item_id=item.id,
                    raw_name=line.product_name,
                    normalized_name=line.product_name.lower(),
                    status=CandidateStatus.A_VALIDER,
                )
            )

        # Constats de conformité.
        findings = evaluate_item(
            raw_name=line.product_name,
            raw_unit_price=unit_price,
            match=match,
            enrichment=enrichment,
            price=price,
        )
        for f in findings:
            self.db.add(
                ComplianceFinding(
                    analysis_id=analysis.id, item_id=item.id,
                    type=f.type, risk=f.risk, message=f.message,
                )
            )

        # Alerte de prix.
        if price.has_alert and price.level is not None:
            self.db.add(
                PriceAlert(
                    analysis_id=analysis.id, item_id=item.id, level=price.level,
                    current_price=unit_price, average_price=price.average_price,
                    min_price=price.min_price, max_price=price.max_price,
                    variation_percent=price.variation_percent, message=price.message,
                )
            )

    def _fill_item(self, item, product, enr: ProductEnrichment, price) -> None:
        item.matched_product_id = product.id
        item.hs_code_id = product.hs_code_id
        if enr.hs_code is not None:
            item.hs_code = enr.hs_code.code
        if enr.taxes:
            tax = enr.taxes[0]
            item.import_duty = tax.import_duty
            item.vat = tax.vat
            item.parafiscal_tax = tax.parafiscal_tax
        item.authorizations = [
            {
                "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                "organization": a.organization or a.ministry,
                "legal_reference": a.legal_reference,
            }
            for a in enr.authorizations
        ]
        docs: list[str] = []
        for a in enr.authorizations:
            for d in (a.required_documents or []):
                if d not in docs:
                    docs.append(d)
        item.required_documents = docs
        if enr.purchase_stats:
            item.purchase_count = enr.purchase_stats.get("count", 0)
            item.avg_price = enr.purchase_stats.get("average_price")
            item.min_price = enr.purchase_stats.get("min_price")
            item.max_price = enr.purchase_stats.get("max_price")
        if enr.purchases:
            last = enr.purchases[0]
            item.last_price = last.unit_price
            item.last_date = last.purchased_at.date()
        item.price_variation_percent = price.variation_percent
        item.price_alert_level = price.level

    # ---------------- finalisation ----------------
    def _finalize(self, analysis: ImportAnalysis, start: float, *, no_lines: bool = False) -> None:
        item_reports = self._build_item_reports(analysis)
        result = report_builder.build(analysis, item_reports)

        report = self.db.execute(
            select(AnalysisReport).where(AnalysisReport.analysis_id == analysis.id)
        ).scalar_one_or_none()
        if report is None:
            report = AnalysisReport(analysis_id=analysis.id, content=result.content)
            self.db.add(report)
        report.content = result.content
        report.confidence = result.confidence
        report.summary = result.summary

        analysis.overall_risk = result.overall_risk
        analysis.confidence = result.confidence
        analysis.summary = result.summary
        analysis.execution_ms = int((time.perf_counter() - start) * 1000)
        analysis.status = AnalysisStatus.PARTIEL if no_lines else AnalysisStatus.TERMINE
        self.db.commit()

    def _build_item_reports(self, analysis: ImportAnalysis) -> list[ItemReport]:
        items = self.db.execute(
            select(ImportAnalysisItem)
            .where(ImportAnalysisItem.analysis_id == analysis.id)
            .order_by(ImportAnalysisItem.line_number)
        ).scalars().all()

        findings_by_item: dict[uuid.UUID, list[Finding]] = {}
        for f in self.db.execute(
            select(ComplianceFinding).where(ComplianceFinding.analysis_id == analysis.id)
        ).scalars().all():
            findings_by_item.setdefault(f.item_id, []).append(
                Finding(type=f.type, risk=f.risk, message=f.message)
            )

        reports: list[ItemReport] = []
        for item in items:
            matched_name = None
            documents: list[dict] = []
            if item.matched_product_id:
                product = self.db.get(Product, item.matched_product_id)
                matched_name = product.name if product else None
                if item.hs_code:
                    documents = enrichment_service._documents(self.db, item.hs_code)
            reports.append(
                ItemReport(
                    line=item.line_number,
                    raw_name=item.raw_product_name or "",
                    matched_name=matched_name,
                    confidence=item.match_confidence or 0.0,
                    method=item.match_method.value,
                    status=item.status.value,
                    hs_code=item.hs_code,
                    import_duty=float(item.import_duty) if item.import_duty is not None else None,
                    vat=float(item.vat) if item.vat is not None else None,
                    parafiscal_tax=float(item.parafiscal_tax) if item.parafiscal_tax is not None else None,
                    authorizations=[
                        a.get("status", "") + (f" ({a['organization']})" if a.get("organization") else "")
                        for a in (item.authorizations or [])
                    ],
                    required_documents=item.required_documents or [],
                    documents=documents,
                    purchase_count=item.purchase_count,
                    average_price=float(item.avg_price) if item.avg_price is not None else None,
                    last_price=float(item.last_price) if item.last_price is not None else None,
                    last_date=item.last_date.isoformat() if item.last_date else None,
                    invoice_price=float(item.raw_unit_price) if item.raw_unit_price is not None else None,
                    price_variation_percent=item.price_variation_percent,
                    findings=findings_by_item.get(item.id, []),
                )
            )
        return reports

    def _reset(self, analysis: ImportAnalysis) -> None:
        for model in (
            PriceAlert, ComplianceFinding, ProductCandidate,
            ImportAnalysisItem, OCRResult,
        ):
            self.db.query(model).filter(model.analysis_id == analysis.id).delete()
        analysis.processed_items = 0
        self.db.commit()


analysis_pipeline_run = run_analysis
