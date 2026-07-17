"""Récupération des données de conformité d'un produit (base UM6P + documents).

Ne renvoie que des informations vérifiées ; aucune valeur n'est inventée.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.authorization import Authorization
from app.models.document import Document
from app.models.hs_code import HsCode
from app.models.knowledge import HsReference
from app.models.product import Product
from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.models.tax import Tax

DOC_LIMIT = 5


@dataclass
class ProductEnrichment:
    hs_code: HsCode | None = None
    taxes: list[Tax] = field(default_factory=list)
    authorizations: list[Authorization] = field(default_factory=list)
    supplier: Supplier | None = None
    purchases: list[PurchaseHistory] = field(default_factory=list)
    purchase_stats: dict | None = None
    documents: list[dict] = field(default_factory=list)


class EnrichmentService:
    def enrich(self, db: Session, product: Product) -> ProductEnrichment:
        enr = ProductEnrichment()

        if product.hs_code_id:
            enr.hs_code = db.get(HsCode, product.hs_code_id)
            enr.taxes = list(
                db.execute(
                    select(Tax)
                    .where(Tax.hs_code_id == product.hs_code_id)
                    .order_by(Tax.effective_date.desc().nullslast())
                ).scalars().all()
            )
            enr.authorizations = list(
                db.execute(
                    select(Authorization).where(
                        Authorization.hs_code_id == product.hs_code_id
                    )
                ).scalars().all()
            )
            if enr.hs_code is not None:
                enr.documents = self._documents(db, enr.hs_code.code)

        enr.purchases = list(
            db.execute(
                select(PurchaseHistory)
                .where(PurchaseHistory.product_id == product.id)
                .order_by(PurchaseHistory.purchased_at.desc())
                .limit(50)
            ).scalars().all()
        )
        enr.purchase_stats = self._stats(db, product.id)
        enr.supplier = self._supplier(db, product, enr.purchases)
        return enr

    def _stats(self, db: Session, product_id: uuid.UUID) -> dict | None:
        row = db.execute(
            select(
                func.count(PurchaseHistory.id),
                func.avg(PurchaseHistory.unit_price),
                func.min(PurchaseHistory.unit_price),
                func.max(PurchaseHistory.unit_price),
            ).where(PurchaseHistory.product_id == product_id)
        ).one()
        if not row[0]:
            return None
        return {
            "count": int(row[0]),
            "average_price": float(row[1]) if row[1] is not None else None,
            "min_price": float(row[2]) if row[2] is not None else None,
            "max_price": float(row[3]) if row[3] is not None else None,
        }

    def _supplier(
        self, db: Session, product: Product, purchases: list[PurchaseHistory]
    ) -> Supplier | None:
        if product.preferred_supplier_id:
            return db.get(Supplier, product.preferred_supplier_id)
        for p in purchases:
            if p.supplier_id:
                return db.get(Supplier, p.supplier_id)
        return None

    def _documents(self, db: Session, hs_code: str) -> list[dict]:
        rows = db.execute(
            select(HsReference, Document)
            .join(Document, Document.id == HsReference.document_id)
            .where(HsReference.hs_code == hs_code)
            .limit(DOC_LIMIT)
        ).all()
        return [
            {
                "document_title": doc.title,
                "chapter": ref.chapter,
                "page": ref.page,
            }
            for ref, doc in rows
        ]


enrichment_service = EnrichmentService()
