"""Détection d'intention (heuristique française, sans appel au LLM).

Déterministe et peu coûteux. La détection tient compte des questions de suivi
(ellipses) : « Et les taxes ? » est classé « taxe » même sans nom de produit.
"""
from __future__ import annotations

import enum
import re
import unicodedata


class Intent(str, enum.Enum):
    PRODUCT_SEARCH = "product_search"
    HS_CODE = "hs_code"
    TAX = "tax"
    AUTHORIZATION = "authorization"
    PURCHASE_HISTORY = "purchase_history"
    SUPPLIER = "supplier"
    DOCUMENT_SEARCH = "document_search"
    GENERAL_PROCUREMENT = "general_procurement"
    INVOICE_ANALYSIS = "invoice_analysis"
    UNKNOWN = "unknown"


INTENT_LABELS_FR: dict[Intent, str] = {
    Intent.PRODUCT_SEARCH: "Recherche de produit",
    Intent.HS_CODE: "Code SH",
    Intent.TAX: "Taxes",
    Intent.AUTHORIZATION: "Autorisation",
    Intent.PURCHASE_HISTORY: "Historique des achats",
    Intent.SUPPLIER: "Fournisseur",
    Intent.DOCUMENT_SEARCH: "Recherche documentaire",
    Intent.GENERAL_PROCUREMENT: "Achats (général)",
    Intent.INVOICE_ANALYSIS: "Analyse de facture",
    Intent.UNKNOWN: "Indéterminé",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


# Motifs par intention (sur texte normalisé sans accents). Ordre = priorité.
_PATTERNS: list[tuple[Intent, re.Pattern]] = [
    (Intent.INVOICE_ANALYSIS, re.compile(r"\bfacture|proforma|analyser? (la|une) facture")),
    (Intent.HS_CODE, re.compile(r"\bcode ?sh\b|\bcode\b.*\bdouanier|nomenclature|\bsh\b|position tarifaire")),
    (Intent.TAX, re.compile(r"\btaxe|droits? de douane|\bdroit d.importation|\btva\b|\bdi\b|parafiscale|quotite|taxation")),
    (Intent.AUTHORIZATION, re.compile(r"autorisation|licence|agrement|ministere|controle|autorise|permis")),
    (Intent.PURCHASE_HISTORY, re.compile(r"\bprix\b|achat|achete|combien|dernier.*(prix|achat)|historique|paye|cout|coute")),
    (Intent.SUPPLIER, re.compile(r"fournisseur|achete chez|aupres de qui|quel fabricant")),
    (Intent.DOCUMENT_SEARCH, re.compile(r"document|circulaire|code des douanes|texte officiel|reglement|montre.*document|chapitre|annexe")),
]

_PRODUCT_HINT = re.compile(r"produit|reference|article|\bsh\b|microscope|centrifug|machine|appareil|equipement")
_GREETING = re.compile(r"^\s*(bonjour|salut|merci|bonsoir|coucou|hello|test)\b")
# Suivi elliptique : commence par « et », « et les », « et le »…
_FOLLOWUP = re.compile(r"^\s*et\b|^\s*et les\b|^\s*et le\b|^\s*et la\b")


def detect_intent(text: str, *, has_focus: bool = False) -> Intent:
    """Classe le message. `has_focus` = un produit/HS est déjà en contexte."""
    norm = _normalize(text)

    for intent, pattern in _PATTERNS:
        if pattern.search(norm):
            return intent

    if _GREETING.match(norm) and not has_focus:
        return Intent.UNKNOWN

    if _PRODUCT_HINT.search(norm):
        return Intent.PRODUCT_SEARCH

    # Question de suivi sans mot-clé explicite : on reste sur le produit courant.
    if has_focus and (_FOLLOWUP.match(norm) or len(norm.split()) <= 4):
        return Intent.PRODUCT_SEARCH

    return Intent.GENERAL_PROCUREMENT


def is_followup(text: str) -> bool:
    return bool(_FOLLOWUP.match(_normalize(text)))
