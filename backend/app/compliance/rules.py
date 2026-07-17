"""Moteur de conformité : génère les constats (findings) et le niveau de risque."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.compliance.enrichment import ProductEnrichment
from app.compliance.matching import MatchResult
from app.compliance.pricing import PriceAnalysis
from app.models.enums import AuthorizationStatus, FindingType, RiskLevel

_RISK_ORDER = {RiskLevel.FAIBLE: 0, RiskLevel.MOYEN: 1, RiskLevel.ELEVE: 2}
_REGULATION_MAX_AGE_YEARS = 5


@dataclass
class Finding:
    type: FindingType
    risk: RiskLevel
    message: str


def max_risk(risks: list[RiskLevel]) -> RiskLevel:
    if not risks:
        return RiskLevel.FAIBLE
    return max(risks, key=lambda r: _RISK_ORDER[r])


def evaluate_item(
    *,
    raw_name: str,
    raw_unit_price: float | None,
    match: MatchResult,
    enrichment: ProductEnrichment | None,
    price: PriceAnalysis,
    today: date | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    today = today or date.today()

    if not match.found or enrichment is None:
        findings.append(
            Finding(
                FindingType.PRODUIT_ABSENT, RiskLevel.ELEVE,
                f"Produit « {raw_name} » introuvable dans la base UM6P "
                "(candidat créé, à valider).",
            )
        )
        return findings

    if enrichment.hs_code is None:
        findings.append(
            Finding(
                FindingType.CODE_SH_MANQUANT, RiskLevel.ELEVE,
                "Aucun code SH rattaché à ce produit.",
            )
        )
    else:
        if not enrichment.taxes:
            findings.append(
                Finding(
                    FindingType.DONNEES_INCOMPLETES, RiskLevel.MOYEN,
                    f"Aucune taxe renseignée pour le code SH {enrichment.hs_code.code}.",
                )
            )
        for auth in enrichment.authorizations:
            status = auth.status
            if status == AuthorizationStatus.REQUISE:
                org = auth.organization or auth.ministry or "organisme non précisé"
                findings.append(
                    Finding(
                        FindingType.PRODUIT_RESTREINT, RiskLevel.ELEVE,
                        f"Autorisation requise ({org}) avant importation.",
                    )
                )
            elif status == AuthorizationStatus.CONDITIONNELLE:
                findings.append(
                    Finding(
                        FindingType.AUTORISATION_MANQUANTE, RiskLevel.MOYEN,
                        "Autorisation conditionnelle : vérifier les conditions.",
                    )
                )
        for tax in enrichment.taxes:
            if tax.effective_date and (
                today.year - tax.effective_date.year > _REGULATION_MAX_AGE_YEARS
            ):
                findings.append(
                    Finding(
                        FindingType.REGLEMENTATION_EXPIREE, RiskLevel.MOYEN,
                        f"Barème de taxes ancien (en vigueur depuis "
                        f"{tax.effective_date.isoformat()}) : à vérifier.",
                    )
                )
                break

    if raw_unit_price is None:
        findings.append(
            Finding(
                FindingType.DONNEES_INCOMPLETES, RiskLevel.FAIBLE,
                "Prix unitaire non détecté sur la facture.",
            )
        )

    if price.has_alert and price.level is not None:
        findings.append(
            Finding(FindingType.ALERTE_PRIX, price.level, price.message or "Écart de prix.")
        )

    return findings
