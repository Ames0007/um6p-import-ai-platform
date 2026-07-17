"""Services Fournisseurs et Historique des achats."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.services.base import BaseService


class SupplierService(BaseService[Supplier]):
    def __init__(self) -> None:
        super().__init__(Supplier)


class PurchaseHistoryService(BaseService[PurchaseHistory]):
    def __init__(self) -> None:
        super().__init__(PurchaseHistory)

    def by_product(
        self, db: Session, product_id: uuid.UUID
    ) -> Sequence[PurchaseHistory]:
        stmt = (
            select(PurchaseHistory)
            .where(PurchaseHistory.product_id == product_id)
            .order_by(PurchaseHistory.purchased_at.desc())
        )
        return db.execute(stmt).scalars().all()


supplier_service = SupplierService()
purchase_history_service = PurchaseHistoryService()
