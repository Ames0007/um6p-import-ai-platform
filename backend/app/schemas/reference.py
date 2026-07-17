"""Schémas des données de référence : Pays, Code SH, Taxe, Autorisation."""
from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.models.enums import AuthorizationStatus
from app.schemas.common import ORMModel, TimestampedRead


# --- Pays ---
class CountryBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=2)
    name_fr: str


class CountryRead(TimestampedRead, CountryBase):
    pass


# --- Code SH ---
class HsCodeBase(BaseModel):
    code: str
    description_fr: str
    chapter: str | None = None


class HsCodeRead(TimestampedRead, HsCodeBase):
    pass


class HsCodeSearchResult(ORMModel):
    id: uuid.UUID
    code: str
    description_fr: str
    score: float | None = None


# --- Taxe ---
class TaxBase(BaseModel):
    import_duty: float | None = None
    vat: float | None = None
    parafiscal_tax: float | None = None
    additional_taxes: list | None = None
    effective_date: date | None = None
    notes_fr: str | None = None


class TaxRead(TimestampedRead, TaxBase):
    hs_code_id: uuid.UUID
    country_id: uuid.UUID | None = None


# --- Autorisation ---
class AuthorizationBase(BaseModel):
    status: AuthorizationStatus
    ministry: str | None = None
    description_fr: str | None = None


class AuthorizationRead(TimestampedRead, AuthorizationBase):
    hs_code_id: uuid.UUID
