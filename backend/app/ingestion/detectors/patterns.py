"""Expressions régulières partagées par les détecteurs.

Ces motifs ciblent la structure des documents douaniers marocains (chapitres,
sections, codes du Système Harmonisé, tables de taxes).
"""
from __future__ import annotations

import re

# --- Structure ---
CHAPTER_RE = re.compile(r"chapitre\s+(\d{1,3})", re.IGNORECASE)
# En-tête de chapitre RÉEL (en début de ligne) — évite les mentions en prose
# comme « … du chapitre 29 … » qui provoquaient le « chapter bleed ».
CHAPTER_HEADER_RE = re.compile(r"^\s*chapitre\s+(\d{1,3})\b", re.IGNORECASE)
# Marqueur de pied/en-tête de page « 3 / Chap 31 » présent sur chaque page.
CHAP_MARKER_RE = re.compile(r"\bchap\.?\s+(\d{1,3})\b", re.IGNORECASE)
SECTION_RE = re.compile(r"\bsection\s+([IVXLCDM]{1,7})\b", re.IGNORECASE)

# --- Codes SH ---
# Sous-positions et positions nationales : 8421.19.00.00, 8421.19
HS_DOTTED_RE = re.compile(r"\b(\d{4}\.\d{2}(?:\.\d{2}){0,2})\b")
# Position à deux niveaux (84.21), isolée : ni précédée ni suivie d'un
# chiffre/point (évite de capturer un fragment d'un code plus long).
HS_HEADING_RE = re.compile(r"(?<![\d.])(\d{2}\.\d{2})(?![\d.])")

# --- Taxes ---
PERCENT_RE = re.compile(r"\b\d{1,3}(?:[.,]\d+)?\s*%")
TAX_KEYWORDS_RE = re.compile(
    r"droit\s+d[’'\s]?importation|\bd\.?i\.?\b|\bt\.?v\.?a\.?\b|quotit[eé]"
    r"|taxe\s+parafiscale|taxe\s+int[eé]rieure",
    re.IGNORECASE,
)

# --- Autorisations ---
AUTH_KEYWORDS_RE = re.compile(
    r"autorisation|licence\s+d[’']?importation|agr[eé]ment|visa\s+technique"
    r"|certificat|produit\s+contr[oô]l[eé]|soumis\s+au\s+contr[oô]le",
    re.IGNORECASE,
)
MINISTRY_RE = re.compile(r"minist[eè]re[^.\n]{0,90}", re.IGNORECASE)
