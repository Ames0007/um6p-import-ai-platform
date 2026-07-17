"""Services des données de référence : Code SH, Taxe, Autorisation."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.authorization import Authorization
from app.models.hs_code import HsCode
from app.models.tax import Tax
from app.services.base import BaseService


class HsCodeService(BaseService[HsCode]):
    def __init__(self) -> None:
        super().__init__(HsCode)

    def search(
        self, db: Session, query: str, *, limit: int = 20
    ) -> Sequence[HsCode]:
        pattern = f"%{query.strip()}%"
        stmt = (
            select(HsCode)
            .where(
                or_(
                    HsCode.code.ilike(pattern),
                    HsCode.description_fr.ilike(pattern),
                )
            )
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()


class TaxService(BaseService[Tax]):
    def __init__(self) -> None:
        super().__init__(Tax)

    def by_hs_code(self, db: Session, hs_code_id: uuid.UUID) -> Sequence[Tax]:
        stmt = select(Tax).where(Tax.hs_code_id == hs_code_id)
        return db.execute(stmt).scalars().all()


class AuthorizationService(BaseService[Authorization]):
    def __init__(self) -> None:
        super().__init__(Authorization)

    def by_hs_code(
        self, db: Session, hs_code_id: uuid.UUID
    ) -> Sequence[Authorization]:
        stmt = select(Authorization).where(Authorization.hs_code_id == hs_code_id)
        return db.execute(stmt).scalars().all()


hs_code_service = HsCodeService()
tax_service = TaxService()
authorization_service = AuthorizationService()
