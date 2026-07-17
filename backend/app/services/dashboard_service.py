"""Agrégations du tableau de bord de l'administration."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.country import Country
from app.models.document import Document
from app.models.hs_code import HsCode
from app.models.import_history import ImportHistory
from app.models.invoice import Invoice
from app.models.product import Product
from app.models.product_alias import ProductAlias
from app.models.purchase_history import PurchaseHistory
from app.models.supplier import Supplier
from app.schemas.admin import AuditLogRead
from app.schemas.dashboard import (
    ChartPoint,
    DashboardCards,
    DashboardResponse,
    RecentImport,
)

TOP_N = 8


class DashboardService:
    def _count(self, db: Session, model) -> int:
        return int(db.execute(select(func.count()).select_from(model)).scalar_one())

    def _chart(self, rows) -> list[ChartPoint]:
        return [
            ChartPoint(label=str(label) if label is not None else "—", value=float(value))
            for label, value in rows
        ]

    def build(self, db: Session) -> DashboardResponse:
        cards = DashboardCards(
            products=self._count(db, Product),
            hs_codes=self._count(db, HsCode),
            suppliers=self._count(db, Supplier),
            invoices=self._count(db, Invoice),
            purchases=self._count(db, PurchaseHistory),
            countries=self._count(db, Country),
            documents=self._count(db, Document),
            aliases=self._count(db, ProductAlias),
        )

        products_by_category = self._chart(
            db.execute(
                select(Product.category, func.count())
                .group_by(Product.category)
                .order_by(func.count().desc())
                .limit(TOP_N)
            ).all()
        )

        purchases_by_country = self._chart(
            db.execute(
                select(Country.name_fr, func.count(PurchaseHistory.id))
                .join(Country, Country.id == PurchaseHistory.country_id)
                .group_by(Country.name_fr)
                .order_by(func.count(PurchaseHistory.id).desc())
                .limit(TOP_N)
            ).all()
        )

        purchases_by_supplier = self._chart(
            db.execute(
                select(Supplier.name, func.count(PurchaseHistory.id))
                .join(Supplier, Supplier.id == PurchaseHistory.supplier_id)
                .group_by(Supplier.name)
                .order_by(func.count(PurchaseHistory.id).desc())
                .limit(TOP_N)
            ).all()
        )

        top_hs_codes = self._chart(
            db.execute(
                select(HsCode.code, func.count(Product.id))
                .join(Product, Product.hs_code_id == HsCode.id)
                .group_by(HsCode.code)
                .order_by(func.count(Product.id).desc())
                .limit(TOP_N)
            ).all()
        )

        recent_imports = [
            RecentImport(
                document_title=doc_title or "—",
                status=status.value if hasattr(status, "value") else str(status),
                when=when.isoformat() if when else None,
            )
            for doc_title, status, when in db.execute(
                select(Document.title, ImportHistory.status, ImportHistory.end_time)
                .join(Document, Document.id == ImportHistory.document_id)
                .order_by(ImportHistory.start_time.desc().nullslast())
                .limit(TOP_N)
            ).all()
        ]

        recent_modifications = [
            AuditLogRead.model_validate(entry)
            for entry in db.execute(
                select(AuditLog).order_by(AuditLog.created_at.desc()).limit(TOP_N)
            ).scalars().all()
        ]

        return DashboardResponse(
            cards=cards,
            products_by_category=products_by_category,
            purchases_by_country=purchases_by_country,
            purchases_by_supplier=purchases_by_supplier,
            top_hs_codes=top_hs_codes,
            recent_imports=recent_imports,
            recent_modifications=recent_modifications,
        )


dashboard_service = DashboardService()
