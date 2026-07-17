"""Détection des exigences d'autorisation et des ministères émetteurs."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ingestion.detectors.patterns import AUTH_KEYWORDS_RE, MINISTRY_RE


@dataclass
class AuthorizationDetection:
    detected: bool = False
    keyword_hits: int = 0
    ministries: list[str] = field(default_factory=list)


def detect_authorizations(text: str) -> AuthorizationDetection:
    """Repère les mentions d'autorisation/licence/contrôle et les ministères."""
    result = AuthorizationDetection()
    result.keyword_hits = len(AUTH_KEYWORDS_RE.findall(text))
    result.detected = result.keyword_hits > 0

    for match in MINISTRY_RE.finditer(text):
        mention = " ".join(match.group(0).split())
        if mention not in result.ministries and len(result.ministries) < 20:
            result.ministries.append(mention)

    return result


# Mentions « fortes » impliquant une autorisation requise (vs conditionnelle).
_STRONG_AUTH_RE = re.compile(
    r"licence\s+d[’']?importation|soumis\s+au\s+contr[oô]le|interdit"
    r"|obligatoire|agr[eé]ment\s+pr[eé]alable",
    re.IGNORECASE,
)


def classify_authorization(line: str) -> tuple[str, str | None] | None:
    """Classe une exigence d'autorisation présente sur une ligne.

    Retourne `(statut, ministère)` ou None si aucune mention n'est détectée.
    Statut : « requise » en présence d'une mention forte (licence, contrôle,
    interdiction), sinon « conditionnelle ». Aucune valeur inventée.
    """
    if not AUTH_KEYWORDS_RE.search(line):
        return None
    ministry_match = MINISTRY_RE.search(line)
    ministry = " ".join(ministry_match.group(0).split()) if ministry_match else None
    status = "requise" if _STRONG_AUTH_RE.search(line) else "conditionnelle"
    return status, ministry
