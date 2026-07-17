"""Service Produits (recherche texte, à étendre avec pgvector)."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.base import BaseService


class ProductService(BaseService[Product]):
    def __init__(self) -> None:
        super().__init__(Product)

    def search(
        self, db: Session, query: str, *, limit: int = 20
    ) -> Sequence[Product]:
        """Recherche floue sur le nom, la référence et la description.

        La recherche sémantique (pgvector) pourra être ajoutée ici sans changer
        le contrat de l'API.
        """
        pattern = f"%{query.strip()}%"
        stmt = (
            select(Product)
            .where(
                or_(
                    Product.name.ilike(pattern),
                    Product.reference.ilike(pattern),
                    Product.description_fr.ilike(pattern),
                )
            )
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()


product_service = ProductService()
