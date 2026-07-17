"""Schémas de l'analyse de conformité à l'import (Phase 5)."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    AnalysisStatus,
    ItemStatus,
    MatchMethod,
    RiskLevel,
)
from app.schemas.common import ORMModel


class AnalysisItemRead(ORMModel):
    id: uuid.UUID
    line_number: int
    raw_text: str | None = None
    raw_product_name: str | None = None
    raw_quantity: float | None = None
    raw_unit_price: float | None = None
    raw_currency: str | None = None
    matched_product_id: uuid.UUID | None = None
    match_confidence: float | None = None
    match_reason: str | None = None
    match_method: MatchMethod
    hs_code: str | None = None
    import_duty: float | None = None
    vat: float | None = None
    parafiscal_tax: float | None = None
    authorizations: list | None = None
    required_documents: list | None = None
    purchase_count: int = 0
    avg_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    last_price: float | None = None
    last_date: date | None = None
    price_variation_percent: float | None = None
    price_alert_level: RiskLevel | None = None
    status: ItemStatus


class FindingRead(ORMModel):
    id: uuid.UUID
    item_id: uuid.UUID | None = None
    type: str
    risk: RiskLevel
    message: str


class AnalysisListItem(ORMModel):
    id: uuid.UUID
    original_filename: str
    supplier_name_raw: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    currency: str | None = None
    status: AnalysisStatus
    overall_risk: RiskLevel | None = None
    confidence: str | None = None
    total_items: int
    processed_items: int
    created_at: datetime

    @property
    def progress_percent(self) -> float:
        if not self.total_items:
            return 0.0
        return round(100 * self.processed_items / self.total_items, 1)


class AnalysisDetail(AnalysisListItem):
    incoterm: str | None = None
    ocr_provider: str | None = None
    execution_ms: int | None = None
    summary: str | None = None
    error_message: str | None = None
    items: list[AnalysisItemRead] = Field(default_factory=list)
    findings: list[FindingRead] = Field(default_factory=list)
    report: dict | None = None


class AnalysisProgress(BaseModel):
    id: uuid.UUID
    status: AnalysisStatus
    total_items: int
    processed_items: int
    progress_percent: float
    overall_risk: RiskLevel | None = None


class AnalysisDispatchResult(BaseModel):
    analyses: list[AnalysisListItem] = Field(default_factory=list)
    mode: str
