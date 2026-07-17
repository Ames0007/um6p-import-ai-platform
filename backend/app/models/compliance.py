"""Entités du moteur de conformité à l'import (Phase 5)."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import (
    AnalysisStatus,
    CandidateStatus,
    FindingType,
    ItemStatus,
    MatchMethod,
    RiskLevel,
)

if TYPE_CHECKING:
    pass

# Type PostgreSQL partagé (une seule création malgré plusieurs colonnes).
_RISK_ENUM = SAEnum(RiskLevel, name="risk_level")


def _fk(target: str, **kw):
    return mapped_column(PgUUID(as_uuid=True), ForeignKey(target, **kw))


class ImportAnalysis(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "import_analyses"

    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Métadonnées extraites de la facture.
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    supplier_name_raw: Mapped[str | None] = mapped_column(String(300), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    incoterm: Mapped[str | None] = mapped_column(String(10), nullable=True)

    status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus, name="analysis_status"),
        default=AnalysisStatus.EN_ATTENTE, nullable=False, index=True,
    )
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ocr_provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    execution_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    overall_risk: Mapped[RiskLevel | None] = mapped_column(_RISK_ENUM, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    items: Mapped[list["ImportAnalysisItem"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan",
        order_by="ImportAnalysisItem.line_number",
    )
    ocr_results: Mapped[list["OCRResult"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    findings: Mapped[list["ComplianceFinding"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    candidates: Mapped[list["ProductCandidate"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    report: Mapped["AnalysisReport | None"] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", uselist=False
    )


class ImportAnalysisItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "import_analysis_items"

    analysis_id: Mapped[uuid.UUID] = _fk("import_analyses.id", ondelete="CASCADE")
    line_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Texte brut extrait
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_product_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_unit_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    raw_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Rapprochement produit
    matched_product_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    match_method: Mapped[MatchMethod] = mapped_column(
        SAEnum(MatchMethod, name="match_method"),
        default=MatchMethod.AUCUNE, nullable=False,
    )

    # Snapshot conformité
    hs_code_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("hs_codes.id"), nullable=True
    )
    hs_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    import_duty: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    vat: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    parafiscal_tax: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    authorizations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    required_documents: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Snapshot historique / prix
    purchase_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    min_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    last_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    last_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    price_variation_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_alert_level: Mapped[RiskLevel | None] = mapped_column(_RISK_ENUM, nullable=True)

    status: Mapped[ItemStatus] = mapped_column(
        SAEnum(ItemStatus, name="item_status"),
        default=ItemStatus.SANS_DONNEES, nullable=False,
    )

    analysis: Mapped["ImportAnalysis"] = relationship(back_populates="items")
    price_alerts: Mapped[list["PriceAlert"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class OCRResult(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ocr_results"

    analysis_id: Mapped[uuid.UUID] = _fk("import_analyses.id", ondelete="CASCADE")
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    analysis: Mapped["ImportAnalysis"] = relationship(back_populates="ocr_results")


class ProductCandidate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "product_candidates"

    analysis_id: Mapped[uuid.UUID] = _fk("import_analyses.id", ondelete="CASCADE")
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("import_analysis_items.id", ondelete="CASCADE"),
        nullable=True,
    )
    raw_name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    suggested_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[CandidateStatus] = mapped_column(
        SAEnum(CandidateStatus, name="candidate_status"),
        default=CandidateStatus.A_VALIDER, nullable=False, index=True,
    )

    analysis: Mapped["ImportAnalysis"] = relationship(back_populates="candidates")


class PriceAlert(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "price_alerts"

    analysis_id: Mapped[uuid.UUID] = _fk("import_analyses.id", ondelete="CASCADE")
    item_id: Mapped[uuid.UUID] = _fk("import_analysis_items.id", ondelete="CASCADE")
    level: Mapped[RiskLevel] = mapped_column(_RISK_ENUM, nullable=False)
    current_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    average_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    min_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    variation_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    item: Mapped["ImportAnalysisItem"] = relationship(back_populates="price_alerts")


class ComplianceFinding(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "compliance_findings"

    analysis_id: Mapped[uuid.UUID] = _fk("import_analyses.id", ondelete="CASCADE")
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("import_analysis_items.id", ondelete="CASCADE"),
        nullable=True,
    )
    type: Mapped[FindingType] = mapped_column(
        SAEnum(FindingType, name="finding_type"), nullable=False
    )
    risk: Mapped[RiskLevel] = mapped_column(_RISK_ENUM, nullable=False)
    message: Mapped[str] = mapped_column(String(700), nullable=False)

    analysis: Mapped["ImportAnalysis"] = relationship(back_populates="findings")


class AnalysisReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "analysis_reports"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("import_analyses.id", ondelete="CASCADE"),
        unique=True, index=True,
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped["ImportAnalysis"] = relationship(back_populates="report")
