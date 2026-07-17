"""Extraction des codes SH présents dans une page."""
from __future__ import annotations

import re

from app.ingestion.detectors.patterns import HS_DOTTED_RE, HS_HEADING_RE
from app.ingestion.types import DetectedHsCode


def extract_hs_codes(text: str) -> list[str]:
    """Retourne la liste dédupliquée (ordre préservé) des codes SH détectés.

    Priorité aux formes les plus spécifiques (sous-positions) ; les positions
    à deux niveaux (84.21) ne sont conservées que si elles ne sont pas déjà
    couvertes par une sous-position détectée.
    """
    seen: dict[str, None] = {}

    for match in HS_DOTTED_RE.finditer(text):
        seen.setdefault(match.group(1), None)

    dotted_prefixes = {code[:5] for code in seen}  # ex. "8421" de "8421.19"
    for match in HS_HEADING_RE.finditer(text):
        code = match.group(1)
        # "84.21" -> préfixe "8421" ; évite les doublons avec les sous-positions.
        if code.replace(".", "") not in dotted_prefixes:
            seen.setdefault(code, None)

    return list(seen.keys())


# --- Analyse structurée de la table tarifaire (fidèle à la mise en page réelle) ---
# Sous-position (code national) en tête de ligne, avec chiffre de contrôle facultatif
# en marge gauche (ex. « 5 3102.21 00 00 – – Sulfate… »).
_SUBHEADING_RE = re.compile(r"^\s*(?:\d\s+)?(\d{4}\.\d{2})\b")
# Position (heading) en tête de ligne (ex. « 31.02 Engrais… »).
_HEADING_START_RE = re.compile(r"^\s*(\d{2}\.\d{2})\b")
_EMBEDDED_SUB_RE = re.compile(r"(\d{4}\.\d{2})")
# Droit d'importation : nombre situé APRÈS les points de conduite (colonne tarifaire).
_DI_RE = re.compile(r"\.{3,}\s*(\d{1,3}(?:[.,]\d+)?)")
# Étiquette de groupe : UN seul tiret en tête, se terminant par « : » (ex. « – Superphosphates: »).
_GROUP_LABEL_RE = re.compile(r"^\s*[-–—]\s+(?![-–—])\S.*:\s*$")
# Lignes de bruit (en-têtes/pieds de page de la nomenclature).
_NOISE_RE = re.compile(
    r"^(codification|tarif des droits|edition|unit[eé]\b|de quantit|normalis|droit\b"
    r"|d[’']?importation|unit[eé]s comp|l[eé]mentaires|\d+\s*/\s*chap)",
    re.IGNORECASE,
)
_LEAD_STRIP_RE = re.compile(r"^[\s\d.\-–—•)]+")
_TAIL_DOTS_RE = re.compile(r"\.{2,}.*$")
_TAIL_UNITS_RE = re.compile(
    r"\s+\d{1,3}(?:[.,]\d+)?\s+(?:kg|u|l|t|hl|m2?|m3?|paire|100\s*kg)\b.*$",
    re.IGNORECASE,
)


def _di_value(line: str) -> float | None:
    m = _DI_RE.search(line)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _clean_tariff_desc(fragment: str) -> str | None:
    """Isole la désignation d'une ligne tarifaire (sans code, suffixes, colonnes)."""
    frag = _TAIL_DOTS_RE.sub("", fragment)     # coupe « ....... 2,5 kg kgN2 »
    frag = _TAIL_UNITS_RE.sub("", frag)
    frag = _LEAD_STRIP_RE.sub("", frag)         # retire « 00 00 – – » en tête
    frag = " ".join(frag.split()).rstrip(" :;.-–—")
    if len(frag) < 2 or not re.search(r"[A-Za-zÀ-ÿ]", frag):
        return None
    return frag


def _compose(*parts: str | None) -> str | None:
    """Assemble la description hiérarchique : position — groupe — sous-position."""
    seen: list[str] = []
    for p in parts:
        if p and p not in seen:
            seen.append(p)
    return " — ".join(seen) if seen else None


def extract_hs_entries(text: str) -> list[DetectedHsCode]:
    """Analyse structurée de la table tarifaire d'une page.

    Ne retient que les VRAIES lignes tarifaires (code en tête de ligne) :
    les références croisées présentes dans les notes explicatives
    (« … du n° 05.11 »), toujours en milieu de ligne, sont ignorées — ce qui
    élimine le « chapter bleed ». La description est reconstituée de façon
    hiérarchique (position → groupe → sous-position) et le droit d'importation
    est lu dans la colonne tarifaire (après les points de conduite), puis
    rattaché à la sous-position courante. Aucune donnée n'est inventée.
    """
    entries: dict[str, DetectedHsCode] = {}
    heading_label: str | None = None
    group_label: str | None = None
    current: DetectedHsCode | None = None

    def _upsert(code: str, desc: str | None, di: float | None) -> DetectedHsCode:
        entry = entries.get(code) or DetectedHsCode(code=code, page=None)
        if desc and (not entry.description or len(desc) > len(entry.description)):
            entry.description = desc
        if di is not None and entry.import_duty is None:
            entry.import_duty = di
        entries[code] = entry
        return entry

    for raw_line in text.splitlines():
        s = raw_line.strip()
        if not s or _NOISE_RE.match(s):
            continue

        m_sub = _SUBHEADING_RE.match(s)
        m_head = None if m_sub else _HEADING_START_RE.match(s)

        if m_sub:
            code = m_sub.group(1)
            desc = _clean_tariff_desc(s[m_sub.end():])
            current = _upsert(code, _compose(heading_label, group_label, desc), _di_value(s))
            continue

        if m_head:
            rest = s[m_head.end():]
            emb = _EMBEDDED_SUB_RE.search(rest)
            if emb:  # ligne « 31.01 3101.00 00 Engrais… » : la sous-position prime
                current = _upsert(
                    emb.group(1), _clean_tariff_desc(rest[emb.end():]), _di_value(s)
                )
                heading_label = group_label = None
            else:  # position pure « 31.02 Engrais minéraux… »
                heading_label = _clean_tariff_desc(rest)
                group_label = None
                current = None
                _upsert(m_head.group(1), heading_label, None)
            continue

        if _GROUP_LABEL_RE.match(s):
            group_label = _clean_tariff_desc(s)
            continue

        # Ligne feuille / continuation : rattache un éventuel DI à la sous-position.
        di = _di_value(s)
        if di is not None and current is not None and current.import_duty is None:
            current.import_duty = di

    return list(entries.values())
