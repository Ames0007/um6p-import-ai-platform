"""Analyse de prix : comparaison facture ↔ historique des achats."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.models.enums import RiskLevel


@dataclass
class PriceAnalysis:
    current_price: float | None
    average_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    variation_percent: float | None = None
    level: RiskLevel | None = None
    message: str | None = None

    @property
    def has_alert(self) -> bool:
        return self.level in {RiskLevel.MOYEN, RiskLevel.ELEVE}


def analyze_price(current_price: float | None, stats: dict | None) -> PriceAnalysis:
    """Compare le prix facturé au prix moyen historique et évalue l'écart."""
    result = PriceAnalysis(current_price=current_price)
    if not stats:
        return result

    result.average_price = stats.get("average_price")
    result.min_price = stats.get("min_price")
    result.max_price = stats.get("max_price")

    if current_price is None or not result.average_price:
        return result

    variation = ((current_price - result.average_price) / result.average_price) * 100
    result.variation_percent = round(variation, 2)

    threshold = settings.PRICE_ALERT_THRESHOLD_PERCENT
    magnitude = abs(variation)
    if magnitude <= threshold:
        result.level = RiskLevel.FAIBLE
    elif magnitude <= 2 * threshold:
        result.level = RiskLevel.MOYEN
    else:
        result.level = RiskLevel.ELEVE

    sense = "supérieur" if variation > 0 else "inférieur"
    result.message = (
        f"Prix facturé {sense} de {abs(result.variation_percent):g} % "
        f"au prix moyen historique ({result.average_price:g})."
    )
    return result
