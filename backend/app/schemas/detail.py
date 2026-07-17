"""Schémas de détail enrichis (pages Produit et Code SH)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.schemas.admin import (
    AuthorizationRead,
    CountryRead,
    HsCodeRead,
    ProductAliasRead,
    ProductRead,
    PurchaseRead,
    SupplierRead,
    TaxRead,
)


class DocumentCitation(BaseModel):
    document_id: uuid.UUID
    document_title: str
    page: int | None = None
    chapter: str | None = None


class PurchaseStats(BaseModel):
    count: int = 0
    average_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    latest_price: float | None = None
    latest_date: str | None = None
    currency: str | None = None


class ProductDetail(ProductRead):
    aliases: list[ProductAliasRead] = []
    purchases: list[PurchaseRead] = []
    hs_code: HsCodeRead | None = None
    preferred_supplier: SupplierRead | None = None
    country_of_origin: CountryRead | None = None
    purchase_stats: PurchaseStats = PurchaseStats()
    document_references: list[DocumentCitation] = []


class HsCodeDetail(HsCodeRead):
    products: list[ProductRead] = []
    taxes: list[TaxRead] = []
    authorizations: list[AuthorizationRead] = []
    document_references: list[DocumentCitation] = []
