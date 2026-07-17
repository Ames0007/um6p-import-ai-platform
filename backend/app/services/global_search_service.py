"""Recherche globale de l'administration (multi-entités).

« centrifuge » → produits, alias, codes SH, fournisseurs, achats, autorisations.
"""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.authorization import Authorization
from app.models.hs_code import HsCode
from app.models.product import Product
from app.models.product_alias import ProductAlias
from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.schemas.global_search import GlobalSearchResponse, SearchEntity

PER_GROUP = 8


class GlobalSearchService:
    def search(self, db: Session, query: str) -> GlobalSearchResponse:
        q = query.strip()
        if not q:
            return GlobalSearchResponse(query=q)
        like = f"%{q}%"

        products = db.execute(
            select(Product)
            .where(
                or_(
                    Product.name.ilike(like),
                    Product.reference.ilike(like),
                    Product.brand.ilike(like),
                    Product.manufacturer.ilike(like),
                    Product.category.ilike(like),
                )
            )
            .limit(PER_GROUP)
        ).scalars().all()

        aliases = db.execute(
            select(ProductAlias).where(ProductAlias.alias.ilike(like)).limit(PER_GROUP)
        ).scalars().all()

        hs_codes = db.execute(
            select(HsCode)
            .where(or_(HsCode.code.ilike(like), HsCode.description_fr.ilike(like)))
            .limit(PER_GROUP)
        ).scalars().all()

        suppliers = db.execute(
            select(Supplier).where(Supplier.name.ilike(like)).limit(PER_GROUP)
        ).scalars().all()

        purchases = db.execute(
            select(PurchaseHistory)
            .where(PurchaseHistory.invoice_number.ilike(like))
            .limit(PER_GROUP)
        ).scalars().all()

        authorizations = db.execute(
            select(Authorization)
            .where(
                or_(
                    Authorization.organization.ilike(like),
                    Authorization.ministry.ilike(like),
                    Authorization.legal_reference.ilike(like),
                )
            )
            .limit(PER_GROUP)
        ).scalars().all()

        return GlobalSearchResponse(
            query=q,
            products=[
                SearchEntity(id=p.id, label=p.name, sublabel=p.reference or p.category)
                for p in products
            ],
            aliases=[
                SearchEntity(id=a.id, label=a.alias, sublabel="Alias produit")
                for a in aliases
            ],
            hs_codes=[
                SearchEntity(id=h.id, label=h.code, sublabel=h.description_fr[:80])
                for h in hs_codes
            ],
            suppliers=[
                SearchEntity(id=s.id, label=s.name, sublabel="Fournisseur")
                for s in suppliers
            ],
            purchases=[
                SearchEntity(
                    id=pu.id,
                    label=pu.invoice_number or "Achat",
                    sublabel=f"{pu.unit_price} {pu.currency}",
                )
                for pu in purchases
            ],
            authorizations=[
                SearchEntity(
                    id=au.id,
                    label=au.organization or au.ministry or "Autorisation",
                    sublabel=au.legal_reference,
                )
                for au in authorizations
            ],
        )


global_search_service = GlobalSearchService()
