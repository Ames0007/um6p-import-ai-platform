"""Schémas de l'assistant d'import (Excel / CSV)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TargetField(BaseModel):
    name: str
    label: str
    required: bool = False


class ImportPreviewResponse(BaseModel):
    """Aperçu d'un fichier chargé, avec proposition de correspondance."""

    token: str  # référence du fichier temporaire, réutilisée à la validation
    resource: str
    columns: list[str]
    sample_rows: list[dict]
    total_rows: int
    target_fields: list[TargetField]
    suggested_mapping: dict[str, str] = Field(default_factory=dict)


class ImportCommitRequest(BaseModel):
    token: str
    resource: str
    # correspondance colonne source -> champ cible
    mapping: dict[str, str]
    # met à jour les lignes existantes (au lieu de les ignorer) selon dedup_field
    update_existing: bool = True
    dedup_field: str | None = None
    reason: str | None = None


class ImportRowError(BaseModel):
    row: int
    message: str


class ImportReport(BaseModel):
    resource: str
    total: int
    created: int
    updated: int
    skipped: int
    errors: list[ImportRowError] = Field(default_factory=list)
