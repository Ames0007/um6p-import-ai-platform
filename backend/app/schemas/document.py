"""Schémas de la bibliothèque documentaire et du moteur d'ingestion."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    DocumentCategory,
    DocumentStatus,
    ImportStatus,
)
from app.schemas.common import ORMModel


class ImportRunRead(ORMModel):
    id: uuid.UUID
    status: ImportStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    current_page: int = 0
    total_pages: int = 0
    message: str | None = None
    errors: list | None = None
    stats: dict | None = None
    duration_seconds: float | None = None


class DocumentRead(ORMModel):
    id: uuid.UUID
    title: str
    filename: str
    category: DocumentCategory
    version: str | None = None
    publication_date: date | None = None
    upload_date: datetime
    number_of_pages: int
    processed_pages: int
    language: str
    status: DocumentStatus
    checksum: str
    mime_type: str | None = None
    size_bytes: int | None = None
    is_scanned: bool
    ocr_used: bool
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    # Champs calculés (renseignés par le service).
    extracted_hs_count: int = 0
    extraction_errors_count: int = 0
    processing_time_seconds: float | None = None
    progress_percent: float = 0.0
    last_import: ImportRunRead | None = None


class DocumentUpdateMeta(BaseModel):
    """Métadonnées éditables lors de l'import."""

    title: str | None = None
    category: DocumentCategory | None = None
    version: str | None = None
    publication_date: date | None = None
    language: str | None = None


class ImportDispatchResult(BaseModel):
    """Résultat d'un import : documents créés + mode d'exécution."""

    documents: list[DocumentRead] = Field(default_factory=list)
    mode: str  # "queued" | "inline"
    duplicates: list[str] = Field(default_factory=list)  # titres/fichiers ignorés
