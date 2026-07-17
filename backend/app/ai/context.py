"""Construction du « paquet de contexte » envoyé à Claude.

Transforme les enregistrements récupérés en un bloc factuel compact + la liste
des sources, des citations et un niveau de confiance. Seul ce contexte (jamais
la base entière) est transmis au modèle.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.ai.retriever import RetrievalResult
from app.models.enums import AuthorizationStatus

Confidence = Literal["elevee", "moyenne", "faible", "aucune"]


@dataclass
class ContextPackage:
    text: str
    sources: list[dict] = field(default_factory=list)  # {type,label,id?}
    citations: list[dict] = field(default_factory=list)  # {document_title,chapter,page}
    confidence: Confidence = "aucune"

    @property
    def is_empty(self) -> bool:
        return self.confidence == "aucune"


def _fmt_pct(value) -> str:
    return f"{value:g} %" if value is not None else "non renseigné"


def _fmt_price(value, currency: str | None) -> str:
    if value is None:
        return "non renseigné"
    return f"{value:,.2f} {currency or 'MAD'}".replace(",", " ")


class ContextBuilder:
    def build(self, result: RetrievalResult) -> ContextPackage:
        lines: list[str] = []
        sources: list[dict] = []
        citations: list[dict] = []

        product = result.resolved_product
        if product is not None:
            lines.append("## Produit (Base Produits UM6P)")
            lines.append(f"- Nom : {product.name}")
            if product.reference:
                lines.append(f"- Référence interne : {product.reference}")
            if product.brand:
                lines.append(f"- Marque : {product.brand}")
            if product.manufacturer:
                lines.append(f"- Fabricant : {product.manufacturer}")
            if product.category:
                lines.append(f"- Catégorie : {product.category}")
            sources.append(
                {"type": "produit", "label": "Base Produits UM6P", "id": str(product.id)}
            )

        if result.is_broad and result.chapter_name:
            lines.append(f"## Aperçu — {result.chapter_name} (Référentiel officiel)")
            lines.append(
                f"{len(result.chapter_codes)} code(s) SH disponible(s) dans ce chapitre."
            )
            if result.chapter_headings:
                lines.append("\n### Principales catégories (positions)")
                for heading in result.chapter_headings[:20]:
                    lines.append(f"- {heading}")
            if result.chapter_codes:
                lines.append("\n### Codes SH disponibles")
                for hs_item in result.chapter_codes[:20]:
                    lines.append(f"- {hs_item.code} : {hs_item.description_fr}")
            sources.append(
                {"type": "chapitre", "label": f"Référentiel Codes SH — {result.chapter_name}"}
            )

        hs = result.hs_code
        if hs is not None:
            lines.append("\n## Code SH (Référentiel officiel)")
            lines.append(f"- Code : {hs.code}")
            lines.append(f"- Description : {hs.description_fr}")
            if hs.chapter:
                lines.append(f"- Chapitre : {hs.chapter}")
            sources.append(
                {"type": "hs_code", "label": "Référentiel Codes SH", "id": str(hs.id)}
            )

        if result.taxes:
            lines.append("\n## Taxes (Référentiel officiel)")
            for tax in result.taxes:
                parts = [
                    f"Droit d'importation : {_fmt_pct(tax.import_duty)}",
                    f"TVA : {_fmt_pct(tax.vat)}",
                ]
                if tax.parafiscal_tax is not None:
                    parts.append(f"Taxe parafiscale : {_fmt_pct(tax.parafiscal_tax)}")
                if tax.effective_date:
                    parts.append(f"en vigueur depuis {tax.effective_date.isoformat()}")
                lines.append(f"- {' ; '.join(parts)}")
            sources.append({"type": "taxe", "label": "Référentiel Taxes UM6P"})

        if result.authorizations:
            lines.append("\n## Autorisations (Référentiel officiel)")
            for auth in result.authorizations:
                status = (
                    auth.status.value
                    if isinstance(auth.status, AuthorizationStatus)
                    else str(auth.status)
                )
                detail = [f"Statut : {status}"]
                if auth.organization or auth.ministry:
                    detail.append(f"Organisme : {auth.organization or auth.ministry}")
                if auth.legal_reference:
                    detail.append(f"Référence : {auth.legal_reference}")
                if auth.processing_time_days is not None:
                    detail.append(f"Délai : {auth.processing_time_days} j")
                lines.append(f"- {' ; '.join(detail)}")
            sources.append(
                {"type": "autorisation", "label": "Référentiel Autorisations UM6P"}
            )

        if result.purchases:
            lines.append("\n## Historique des achats (UM6P)")
            stats = result.purchase_stats or {}
            currency = result.purchases[0].currency
            if stats.get("average_price") is not None:
                lines.append(
                    f"- Prix moyen : {_fmt_price(stats['average_price'], currency)} "
                    f"(sur {stats.get('count', 0)} achat(s))"
                )
            last = result.purchases[0]
            lines.append(
                f"- Dernier achat : {_fmt_price(float(last.unit_price), last.currency)} "
                f"le {last.purchased_at.date().isoformat()}"
                + (f" — facture {last.invoice_number}" if last.invoice_number else "")
            )
            sources.append(
                {"type": "historique", "label": "Historique des achats UM6P"}
            )

        if result.related_products:
            lines.append("\n## Produits liés (Base Produits UM6P)")
            for prod in result.related_products[:8]:
                lines.append(f"- {prod.name}" + (f" (réf. {prod.reference})" if prod.reference else ""))
            sources.append({"type": "produit", "label": "Base Produits UM6P"})

        if result.supplier is not None:
            sup = result.supplier
            lines.append("\n## Fournisseur (Base Fournisseurs UM6P)")
            lines.append(f"- Société : {sup.name}")
            if sup.contact_name:
                lines.append(f"- Contact : {sup.contact_name}")
            if sup.lead_time_days is not None:
                lines.append(f"- Délai d'approvisionnement : {sup.lead_time_days} j")
            sources.append(
                {"type": "fournisseur", "label": "Base Fournisseurs UM6P", "id": str(sup.id)}
            )

        if result.documents:
            lines.append("\n## Documents officiels (extraits)")
            for doc in result.documents:
                loc = " — ".join(
                    filter(
                        None,
                        [
                            doc.document_title,
                            doc.chapter,
                            f"Page {doc.page}" if doc.page is not None else None,
                        ],
                    )
                )
                lines.append(f"- {loc}" + (f" : « {doc.excerpt} »" if doc.excerpt else ""))
                citations.append(
                    {
                        "document_title": doc.document_title,
                        "chapter": doc.chapter,
                        "page": doc.page,
                    }
                )
                sources.append({"type": "document", "label": loc})

        confidence = self._confidence(result)
        return ContextPackage(
            text="\n".join(lines).strip(),
            sources=sources,
            citations=citations,
            confidence=confidence,
        )

    def _confidence(self, result: RetrievalResult) -> Confidence:
        strong = result.resolved_product is not None and (
            result.hs_code is not None
            or result.taxes
            or result.purchases
            or result.authorizations
        )
        if strong:
            return "elevee"
        if result.has_structured or result.documents:
            return "moyenne"
        if result.products:
            return "faible"
        return "aucune"


context_builder = ContextBuilder()
