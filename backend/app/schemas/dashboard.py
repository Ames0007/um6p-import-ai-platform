"""Schémas du tableau de bord de l'administration."""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.admin import AuditLogRead


class DashboardCards(BaseModel):
    products: int = 0
    hs_codes: int = 0
    suppliers: int = 0
    invoices: int = 0
    purchases: int = 0
    countries: int = 0
    documents: int = 0
    aliases: int = 0


class ChartPoint(BaseModel):
    label: str
    value: float


class RecentImport(BaseModel):
    document_title: str
    status: str
    when: str | None = None


class DashboardResponse(BaseModel):
    cards: DashboardCards
    products_by_category: list[ChartPoint]
    purchases_by_country: list[ChartPoint]
    purchases_by_supplier: list[ChartPoint]
    top_hs_codes: list[ChartPoint]
    recent_imports: list[RecentImport]
    recent_modifications: list[AuditLogRead]
