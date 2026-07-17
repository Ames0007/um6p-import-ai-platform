"""Génération du rapport de conformité à l'import (structure JSON)."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.compliance.rules import Finding, max_risk
from app.models.enums import FindingType, RiskLevel

NO_DATA = "Aucune information vérifiée disponible."

_RECOMMENDATIONS = {
    FindingType.PRODUIT_ABSENT: "Créer et valider le produit dans le référentiel UM6P.",
    FindingType.CODE_SH_MANQUANT: "Rattacher un code SH officiel au produit.",
    FindingType.AUTORISATION_MANQUANTE: "Vérifier les conditions d'autorisation avant import.",
    FindingType.PRODUIT_RESTREINT: "Obtenir l'autorisation requise auprès de l'organisme compétent.",
    FindingType.DONNEES_INCOMPLETES: "Compléter les données manquantes (prix, taxes).",
    FindingType.REGLEMENTATION_EXPIREE: "Vérifier la mise à jour du barème réglementaire.",
    FindingType.ALERTE_PRIX: "Justifier l'écart de prix ou renégocier avec le fournisseur.",
    FindingType.FOURNISSEUR_ABSENT: "Enregistrer le fournisseur dans la base UM6P.",
}


@dataclass
class ItemReport:
    line: int
    raw_name: str
    matched_name: str | None
    confidence: float
    method: str
    status: str
    hs_code: str | None = None
    import_duty: float | None = None
    vat: float | None = None
    parafiscal_tax: float | None = None
    authorizations: list[str] = field(default_factory=list)
    required_documents: list[str] = field(default_factory=list)
    documents: list[dict] = field(default_factory=list)
    purchase_count: int = 0
    average_price: float | None = None
    last_price: float | None = None
    last_date: str | None = None
    invoice_price: float | None = None
    price_variation_percent: float | None = None
    findings: list[Finding] = field(default_factory=list)


@dataclass
class ReportResult:
    content: dict
    confidence: str
    overall_risk: RiskLevel
    summary: str


class ReportBuilder:
    def build(self, analysis, items: list[ItemReport]) -> ReportResult:
        all_findings = [f for it in items for f in it.findings]
        overall_risk = max_risk([f.risk for f in all_findings]) if all_findings else RiskLevel.FAIBLE
        confidence = self._confidence(items)

        warnings = [
            {"risk": f.risk.value, "message": f.message}
            for it in items
            for f in it.findings
            if f.risk in {RiskLevel.MOYEN, RiskLevel.ELEVE}
        ]
        recommendations = self._recommendations(all_findings)

        sources = self._sources(items)
        citations = self._citations(items)

        content = {
            "supplier": {
                "raw": analysis.supplier_name_raw,
                "matched_id": str(analysis.supplier_id) if analysis.supplier_id else None,
            },
            "invoice_summary": {
                "invoice_number": analysis.invoice_number,
                "invoice_date": analysis.invoice_date.isoformat()
                if analysis.invoice_date else None,
                "currency": analysis.currency,
                "incoterm": analysis.incoterm,
                "line_count": len(items),
            },
            "detected_products": [self._item_dict(it) for it in items],
            "compliance_analysis": {
                "overall_risk": overall_risk.value,
                "findings": [
                    {"type": f.type.value, "risk": f.risk.value, "message": f.message}
                    for f in all_findings
                ],
            },
            "taxes": [
                {
                    "product": it.matched_name or it.raw_name,
                    "hs_code": it.hs_code,
                    "import_duty": it.import_duty,
                    "vat": it.vat,
                    "parafiscal_tax": it.parafiscal_tax,
                }
                for it in items if it.hs_code
            ],
            "required_authorizations": [
                {"product": it.matched_name or it.raw_name, "authorizations": it.authorizations}
                for it in items if it.authorizations
            ],
            "required_documents": sorted(
                {doc for it in items for doc in it.required_documents}
            ),
            "purchase_history": [
                {
                    "product": it.matched_name or it.raw_name,
                    "count": it.purchase_count,
                    "average_price": it.average_price,
                    "last_price": it.last_price,
                    "last_date": it.last_date,
                }
                for it in items if it.purchase_count
            ],
            "price_comparison": [
                {
                    "product": it.matched_name or it.raw_name,
                    "invoice_price": it.invoice_price,
                    "average_price": it.average_price,
                    "variation_percent": it.price_variation_percent,
                }
                for it in items if it.invoice_price is not None
            ],
            "warnings": warnings,
            "recommendations": recommendations,
            "sources": sources,
            "citations": citations,
            "confidence": confidence,
        }
        summary = self._summary(items, overall_risk, confidence)
        return ReportResult(content, confidence, overall_risk, summary)

    def _item_dict(self, it: ItemReport) -> dict:
        return {
            "line": it.line,
            "raw_name": it.raw_name,
            "matched_name": it.matched_name,
            "confidence": round(it.confidence, 2),
            "method": it.method,
            "status": it.status,
            "hs_code": it.hs_code,
            "import_duty": it.import_duty,
            "vat": it.vat,
            "authorizations": it.authorizations,
            "required_documents": it.required_documents,
            "purchase_count": it.purchase_count,
            "invoice_price": it.invoice_price,
            "price_variation_percent": it.price_variation_percent,
        }

    def _confidence(self, items: list[ItemReport]) -> str:
        if not items:
            return "aucune"
        matched = [it for it in items if it.matched_name]
        if not matched:
            return "aucune"
        avg = sum(it.confidence for it in matched) / len(matched)
        ratio = len(matched) / len(items)
        if avg >= 0.85 and ratio >= 0.9:
            return "elevee"
        if avg >= 0.6 and ratio >= 0.5:
            return "moyenne"
        return "faible"

    def _recommendations(self, findings: list[Finding]) -> list[str]:
        seen: dict[FindingType, str] = {}
        for f in findings:
            if f.type not in seen and f.type in _RECOMMENDATIONS:
                seen[f.type] = _RECOMMENDATIONS[f.type]
        return list(seen.values())

    def _sources(self, items: list[ItemReport]) -> list[str]:
        sources: set[str] = set()
        for it in items:
            if it.matched_name:
                sources.add("Base Produits UM6P")
            if it.hs_code:
                sources.add("Référentiel Codes SH UM6P")
            if it.import_duty is not None or it.vat is not None:
                sources.add("Référentiel Taxes UM6P")
            if it.authorizations:
                sources.add("Référentiel Autorisations UM6P")
            if it.purchase_count:
                sources.add("Historique des achats UM6P")
            for doc in it.documents:
                sources.add(doc.get("document_title", "Document officiel"))
        return sorted(sources)

    def _citations(self, items: list[ItemReport]) -> list[dict]:
        seen: set[tuple] = set()
        citations: list[dict] = []
        for it in items:
            for doc in it.documents:
                key = (doc.get("document_title"), doc.get("page"))
                if key in seen:
                    continue
                seen.add(key)
                citations.append(doc)
        return citations

    def _summary(self, items, risk: RiskLevel, confidence: str) -> str:
        if not items:
            return NO_DATA
        matched = sum(1 for it in items if it.matched_name)
        return (
            f"{len(items)} ligne(s) analysée(s), {matched} produit(s) rapproché(s). "
            f"Risque global : {risk.value}. Confiance : {confidence}."
        )


report_builder = ReportBuilder()
