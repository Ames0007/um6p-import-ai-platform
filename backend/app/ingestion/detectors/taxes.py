"""Détection des tables de taxes (droits d'importation, TVA, quotités)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ingestion.detectors.patterns import PERCENT_RE, TAX_KEYWORDS_RE


@dataclass
class TaxDetection:
    detected: bool = False
    percent_hits: int = 0
    lines: list[str] = field(default_factory=list)


def detect_tax_tables(text: str) -> TaxDetection:
    """Repère les lignes évoquant des taxes avec un taux en pourcentage.

    NOTE : on ne fait que DÉTECTER et LOCALISER ; aucune valeur n'est
    interprétée comme faisant autorité à ce stade. Le texte reste consultable
    via la recherche pour vérification humaine.
    """
    result = TaxDetection()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        has_percent = bool(PERCENT_RE.search(line))
        has_keyword = bool(TAX_KEYWORDS_RE.search(line))
        if has_percent and (has_keyword or _looks_like_tax_row(line)):
            result.percent_hits += 1
            if len(result.lines) < 50:
                result.lines.append(line)
    result.detected = result.percent_hits > 0
    return result


def _looks_like_tax_row(line: str) -> bool:
    """Heuristique : ligne courte contenant un pourcentage (ligne de barème)."""
    return len(line) <= 120 and "%" in line


# Un mot-clé de taxe doit précéder directement le pourcentage (fidélité stricte).
_DI_RE = re.compile(
    r"(?:droit\s+d[’'\s]?importation|\bd\.?\s?i\.?\b|quotit[eé])"
    r"[^%\d]{0,25}(\d{1,3}(?:[.,]\d+)?)\s*%",
    re.IGNORECASE,
)
_TVA_RE = re.compile(
    r"\bt\.?\s?v\.?\s?a\.?\b[^%\d]{0,25}(\d{1,3}(?:[.,]\d+)?)\s*%", re.IGNORECASE
)
_PARA_RE = re.compile(
    r"taxe\s+parafiscale[^%\d]{0,25}(\d{1,3}(?:[.,]\d+)?)\s*%", re.IGNORECASE
)


def _num(match) -> float | None:
    return float(match.group(1).replace(",", ".")) if match else None


def parse_line_taxes(line: str) -> dict | None:
    """Extrait les composantes de taxation d'une ligne (DI, TVA, parafiscale).

    Conservateur : ne renvoie une valeur que si un mot-clé de taxe précède
    directement le pourcentage. Retourne None si rien n'est identifiable, afin
    de ne jamais interpréter un pourcentage isolé comme une taxe.
    """
    di = _num(_DI_RE.search(line))
    tva = _num(_TVA_RE.search(line))
    para = _num(_PARA_RE.search(line))
    if di is None and tva is None and para is None:
        return None
    return {"import_duty": di, "vat": tva, "parafiscal_tax": para}
