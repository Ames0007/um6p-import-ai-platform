"""Schémas Facture."""
from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import InvoiceStatus
from app.schemas.common import TimestampedRead


class InvoiceBase(BaseModel):
    filename: str
    mime_type: str | None = None
    size_bytes: int | None = None
    status: InvoiceStatus = InvoiceStatus.RECUE


class InvoiceRead(TimestampedRead, InvoiceBase):
    pass
