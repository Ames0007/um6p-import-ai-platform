"""Schémas achats : Fournisseur, Produit, Historique des achats."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


# --- Fournisseur ---
class SupplierBase(BaseModel):
    name: str
    country_id: uuid.UUID | None = None
    email: str | None = None
    phone: str | None = None


class SupplierRead(TimestampedRead, SupplierBase):
    pass


# --- Produit ---
class ProductBase(BaseModel):
    name: str
    description_fr: str | None = None
    reference: str | None = None
    hs_code_id: uuid.UUID | None = None


class ProductCreate(ProductBase):
    pass


class ProductRead(TimestampedRead, ProductBase):
    pass


# --- Historique des achats ---
class PurchaseHistoryBase(BaseModel):
    product_id: uuid.UUID
    supplier_id: uuid.UUID | None = None
    unit_price: float
    currency: str = "MAD"
    quantity: int = 1
    purchased_at: datetime


class PurchaseHistoryRead(TimestampedRead, PurchaseHistoryBase):
    pass
