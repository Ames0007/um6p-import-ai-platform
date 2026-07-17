"""Vues de détail enrichies : Produit et Code SH (avec traçabilité documents)."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.authorization import Authorization
from app.models.document import Document
from app.models.hs_code import HsCode
from app.models.knowledge import DocumentReference, HsReference
from app.models.product import Product
from app.models.purchase_history import PurchaseHistory
from app.models.tax import Tax
from app.schemas.admin import (
    AuthorizationRead,
    CountryRead,
    HsCodeRead,
    ProductAliasRead,
    ProductRead,
    PurchaseRead,
    SupplierRead,
    TaxRead,
)
from app.schemas.detail import (
    DocumentCitation,
    HsCodeDetail,
    ProductDetail,
    PurchaseStats,
)


class DetailService:
    def product_detail(self, db: Session, product_id: uuid.UUID) -> ProductDetail | None:
        product = db.get(Product, product_id)
        if product is None:
            return None

        stats_row = db.execute(
            select(
                func.count(PurchaseHistory.id),
                func.avg(PurchaseHistory.unit_price),
                func.min(PurchaseHistory.unit_price),
                func.max(PurchaseHistory.unit_price),
            ).where(PurchaseHistory.product_id == product_id)
        ).one()

        latest = db.execute(
            select(PurchaseHistory)
            .where(PurchaseHistory.product_id == product_id)
            .order_by(PurchaseHistory.purchased_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        stats = PurchaseStats(
            count=int(stats_row[0] or 0),
            average_price=float(stats_row[1]) if stats_row[1] is not None else None,
            min_price=float(stats_row[2]) if stats_row[2] is not None else None,
            max_price=float(stats_row[3]) if stats_row[3] is not None else None,
            latest_price=float(latest.unit_price) if latest else None,
            latest_date=latest.purchased_at.isoformat() if latest else None,
            currency=latest.currency if latest else None,
        )

        citations = [
            DocumentCitation(
                document_id=doc.id, document_title=doc.title, page=ref.page
            )
            for ref, doc in db.execute(
                select(DocumentReference, Document)
                .join(Document, Document.id == DocumentReference.document_id)
                .where(DocumentReference.product_id == product_id)
                .limit(50)
            ).all()
        ]

        detail = ProductDetail.model_validate(product)
        detail.aliases = [ProductAliasRead.model_validate(a) for a in product.aliases]
        detail.purchases = [
            PurchaseRead.model_validate(p)
            for p in sorted(
                product.purchases, key=lambda x: x.purchased_at, reverse=True
            )
        ]
        detail.hs_code = (
            HsCodeRead.model_validate(product.hs_code) if product.hs_code else None
        )
        detail.preferred_supplier = (
            SupplierRead.model_validate(product.preferred_supplier)
            if product.preferred_supplier
            else None
        )
        detail.country_of_origin = (
            CountryRead.model_validate(product.country_of_origin)
            if product.country_of_origin
            else None
        )
        detail.purchase_stats = stats
        detail.document_references = citations
        return detail

    def hs_code_detail(self, db: Session, hs_code_id: uuid.UUID) -> HsCodeDetail | None:
        hs = db.get(HsCode, hs_code_id)
        if hs is None:
            return None

        products = db.execute(
            select(Product).where(Product.hs_code_id == hs_code_id)
        ).scalars().all()
        taxes = db.execute(
            select(Tax).where(Tax.hs_code_id == hs_code_id)
            .order_by(Tax.effective_date.desc().nullslast())
        ).scalars().all()
        authorizations = db.execute(
            select(Authorization).where(Authorization.hs_code_id == hs_code_id)
        ).scalars().all()

        citations = [
            DocumentCitation(
                document_id=doc.id,
                document_title=doc.title,
                page=ref.page,
                chapter=ref.chapter,
            )
            for ref, doc in db.execute(
                select(HsReference, Document)
                .join(Document, Document.id == HsReference.document_id)
                .where(HsReference.hs_code == hs.code)
                .limit(50)
            ).all()
        ]

        detail = HsCodeDetail.model_validate(hs)
        detail.products = [ProductRead.model_validate(p) for p in products]
        detail.taxes = [TaxRead.model_validate(t) for t in taxes]
        detail.authorizations = [
            AuthorizationRead.model_validate(a) for a in authorizations
        ]
        detail.document_references = citations
        return detail


detail_service = DetailService()
