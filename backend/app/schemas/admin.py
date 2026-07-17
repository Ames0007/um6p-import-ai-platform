"""Schémas CRUD de l'administration (Phase 3).

Pour chaque entité : `*Create`, `*Update` (tous champs optionnels) et `*Read`.
Les schémas restent « plats » (identifiants de rattachement) pour alimenter la
fabrique de routes CRUD générique ; des schémas de détail enrichis existent
séparément (voir `schemas/detail.py`).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    AuditAction,
    AuthorizationStatus,
    ProductStatus,
)
from app.schemas.common import TimestampedRead


# ============================ Pays ============================
class CountryCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=2)
    name_fr: str


class CountryUpdate(BaseModel):
    code: str | None = Field(None, min_length=2, max_length=2)
    name_fr: str | None = None


class CountryRead(TimestampedRead):
    code: str
    name_fr: str


# ============================ Code SH ============================
class HsCodeCreate(BaseModel):
    code: str
    description_fr: str
    chapter: str | None = None


class HsCodeUpdate(BaseModel):
    code: str | None = None
    description_fr: str | None = None
    chapter: str | None = None


class HsCodeRead(TimestampedRead):
    code: str
    description_fr: str
    chapter: str | None = None


# ============================ Taxe ============================
class TaxCreate(BaseModel):
    hs_code_id: uuid.UUID
    country_id: uuid.UUID | None = None
    import_duty: float | None = None
    vat: float | None = None
    parafiscal_tax: float | None = None
    additional_taxes: list | None = None
    effective_date: date | None = None
    notes_fr: str | None = None


class TaxUpdate(BaseModel):
    hs_code_id: uuid.UUID | None = None
    country_id: uuid.UUID | None = None
    import_duty: float | None = None
    vat: float | None = None
    parafiscal_tax: float | None = None
    additional_taxes: list | None = None
    effective_date: date | None = None
    notes_fr: str | None = None


class TaxRead(TimestampedRead):
    hs_code_id: uuid.UUID
    country_id: uuid.UUID | None = None
    import_duty: float | None = None
    vat: float | None = None
    parafiscal_tax: float | None = None
    additional_taxes: list | None = None
    effective_date: date | None = None
    notes_fr: str | None = None


# ============================ Autorisation ============================
class AuthorizationCreate(BaseModel):
    hs_code_id: uuid.UUID
    status: AuthorizationStatus = AuthorizationStatus.NON_REQUISE
    organization: str | None = None
    ministry: str | None = None
    required_documents: list | None = None
    legal_reference: str | None = None
    processing_time_days: int | None = None
    comments: str | None = None
    description_fr: str | None = None


class AuthorizationUpdate(BaseModel):
    hs_code_id: uuid.UUID | None = None
    status: AuthorizationStatus | None = None
    organization: str | None = None
    ministry: str | None = None
    required_documents: list | None = None
    legal_reference: str | None = None
    processing_time_days: int | None = None
    comments: str | None = None
    description_fr: str | None = None


class AuthorizationRead(TimestampedRead):
    hs_code_id: uuid.UUID
    status: AuthorizationStatus
    organization: str | None = None
    ministry: str | None = None
    required_documents: list | None = None
    legal_reference: str | None = None
    processing_time_days: int | None = None
    comments: str | None = None
    description_fr: str | None = None


# ============================ Fournisseur ============================
class SupplierCreate(BaseModel):
    name: str
    country_id: uuid.UUID | None = None
    website: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    lead_time_days: int | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    country_id: uuid.UUID | None = None
    website: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    lead_time_days: int | None = None


class SupplierRead(TimestampedRead):
    name: str
    country_id: uuid.UUID | None = None
    website: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    lead_time_days: int | None = None


# ============================ Produit ============================
class ProductCreate(BaseModel):
    reference: str | None = None
    name: str
    manufacturer: str | None = None
    brand: str | None = None
    category: str | None = None
    description_fr: str | None = None
    keywords: list[str] = Field(default_factory=list)
    country_of_origin_id: uuid.UUID | None = None
    preferred_supplier_id: uuid.UUID | None = None
    hs_code_id: uuid.UUID | None = None
    status: ProductStatus = ProductStatus.ACTIF
    notes: str | None = None


class ProductUpdate(BaseModel):
    reference: str | None = None
    name: str | None = None
    manufacturer: str | None = None
    brand: str | None = None
    category: str | None = None
    description_fr: str | None = None
    keywords: list[str] | None = None
    country_of_origin_id: uuid.UUID | None = None
    preferred_supplier_id: uuid.UUID | None = None
    hs_code_id: uuid.UUID | None = None
    status: ProductStatus | None = None
    notes: str | None = None


class ProductRead(TimestampedRead):
    reference: str | None = None
    name: str
    manufacturer: str | None = None
    brand: str | None = None
    category: str | None = None
    description_fr: str | None = None
    keywords: list[str] = Field(default_factory=list)
    country_of_origin_id: uuid.UUID | None = None
    preferred_supplier_id: uuid.UUID | None = None
    hs_code_id: uuid.UUID | None = None
    status: ProductStatus
    notes: str | None = None


# ============================ Alias Produit ============================
class ProductAliasCreate(BaseModel):
    product_id: uuid.UUID
    alias: str


class ProductAliasUpdate(BaseModel):
    product_id: uuid.UUID | None = None
    alias: str | None = None


class ProductAliasRead(TimestampedRead):
    product_id: uuid.UUID
    alias: str


# ============================ Historique des achats ============================
class PurchaseCreate(BaseModel):
    product_id: uuid.UUID
    supplier_id: uuid.UUID | None = None
    country_id: uuid.UUID | None = None
    invoice_number: str | None = None
    unit_price: float
    currency: str = "MAD"
    quantity: int = 1
    incoterm: str | None = None
    purchased_at: datetime


class PurchaseUpdate(BaseModel):
    product_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    country_id: uuid.UUID | None = None
    invoice_number: str | None = None
    unit_price: float | None = None
    currency: str | None = None
    quantity: int | None = None
    incoterm: str | None = None
    purchased_at: datetime | None = None


class PurchaseRead(TimestampedRead):
    product_id: uuid.UUID
    supplier_id: uuid.UUID | None = None
    country_id: uuid.UUID | None = None
    invoice_number: str | None = None
    unit_price: float
    currency: str
    quantity: int
    incoterm: str | None = None
    purchased_at: datetime


# ============================ Audit ============================
class AuditLogRead(TimestampedRead):
    entity_type: str
    entity_id: uuid.UUID | None = None
    action: AuditAction
    actor: str
    changes: dict | None = None
    reason: str | None = None
