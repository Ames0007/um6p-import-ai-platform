"""Détecteurs appliqués au texte extrait (structure, codes SH, taxes, autorisations)."""
from __future__ import annotations

from app.ingestion.detectors.authorizations import (
    classify_authorization,
    detect_authorizations,
)
from app.ingestion.detectors.hs_codes import extract_hs_codes, extract_hs_entries
from app.ingestion.detectors.structure import StructureTracker
from app.ingestion.detectors.taxes import detect_tax_tables, parse_line_taxes

__all__ = [
    "StructureTracker",
    "extract_hs_codes",
    "extract_hs_entries",
    "detect_tax_tables",
    "parse_line_taxes",
    "detect_authorizations",
    "classify_authorization",
]
