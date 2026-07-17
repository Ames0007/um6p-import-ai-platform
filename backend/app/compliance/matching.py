"""Rapprochement produit : facture → référentiel UM6P.

Priorité : nom exact → référence interne → alias → marque → fabricant →
similarité sémantique. Ne crée jamais de produit ; si rien ne correspond, la
ligne devient un « candidat à valider ».
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import MatchMethod
from app.models.product import Product
from app.models.product_alias import ProductAlias


@dataclass
class MatchResult:
    product: Product | None
    confidence: float
    reason: str
    method: MatchMethod

    @property
    def found(self) -> bool:
        return self.product is not None


def _normalize(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def _tokens(name: str) -> list[str]:
    return [t for t in re.split(r"[^\wàâçéèêëîïôûùüÿñ]+", name) if len(t) >= 3]


class ProductMatcher:
    def match(self, db: Session, raw_name: str) -> MatchResult:
        norm = _normalize(raw_name)
        if not norm:
            return MatchResult(None, 0.0, "Nom vide", MatchMethod.AUCUNE)

        # 1) Nom exact
        p = db.execute(
            select(Product).where(func.lower(Product.name) == norm).limit(1)
        ).scalars().first()
        if p:
            return MatchResult(p, 1.0, "Nom exact", MatchMethod.NOM_EXACT)

        # 2) Référence interne exacte
        p = db.execute(
            select(Product).where(func.lower(Product.reference) == norm).limit(1)
        ).scalars().first()
        if p:
            return MatchResult(p, 0.98, "Référence interne", MatchMethod.REFERENCE)

        # 3) Alias (exact puis partiel)
        p = db.execute(
            select(Product)
            .join(ProductAlias, ProductAlias.product_id == Product.id)
            .where(func.lower(ProductAlias.alias) == norm)
            .limit(1)
        ).scalars().first()
        if p:
            return MatchResult(p, 0.9, "Alias exact", MatchMethod.ALIAS)

        like = f"%{norm}%"
        p = db.execute(
            select(Product).where(func.lower(Product.name).like(like)).limit(1)
        ).scalars().first()
        if p:
            return MatchResult(p, 0.78, "Nom similaire", MatchMethod.SEMANTIQUE)

        p = db.execute(
            select(Product)
            .join(ProductAlias, ProductAlias.product_id == Product.id)
            .where(func.lower(ProductAlias.alias).like(like))
            .limit(1)
        ).scalars().first()
        if p:
            return MatchResult(p, 0.72, "Alias similaire", MatchMethod.ALIAS)

        tokens = _tokens(norm)

        # 4) Marque / 5) Fabricant (égalité sur un jeton)
        for token in tokens:
            p = db.execute(
                select(Product).where(func.lower(Product.brand) == token).limit(1)
            ).scalars().first()
            if p:
                return MatchResult(p, 0.6, f"Marque « {token} »", MatchMethod.MARQUE)
        for token in tokens:
            p = db.execute(
                select(Product)
                .where(func.lower(Product.manufacturer) == token)
                .limit(1)
            ).scalars().first()
            if p:
                return MatchResult(
                    p, 0.55, f"Fabricant « {token} »", MatchMethod.FABRICANT
                )

        # 6) Similarité sémantique (jeton présent dans le nom)
        for token in tokens:
            p = db.execute(
                select(Product)
                .where(func.lower(Product.name).like(f"%{token}%"))
                .limit(1)
            ).scalars().first()
            if p:
                return MatchResult(
                    p, 0.4, f"Similarité « {token} »", MatchMethod.SEMANTIQUE
                )

        return MatchResult(None, 0.0, "Aucune correspondance vérifiée", MatchMethod.AUCUNE)


product_matcher = ProductMatcher()
