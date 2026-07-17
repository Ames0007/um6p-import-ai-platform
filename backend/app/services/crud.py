"""Service CRUD générique : pagination, filtrage, tri, audit.

Utilisé par la fabrique de routes de l'administration pour éviter la
duplication. Toute écriture est journalisée dans la piste d'audit.
"""
from __future__ import annotations

import uuid
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import func, inspect, or_, select
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.models.enums import AuditAction
from app.services.audit_service import audit_service, diff_changes

ModelT = TypeVar("ModelT", bound=Base)


def model_to_dict(obj: Base) -> dict[str, Any]:
    """Instantané des colonnes d'un objet ORM (pour l'audit)."""
    mapper = inspect(obj).mapper
    return {
        attr.key: getattr(obj, attr.key)
        for attr in mapper.column_attrs
        if attr.key != "embedding"  # vecteur volumineux, non pertinent en audit
    }


class CRUDService(Generic[ModelT]):
    def __init__(
        self,
        model: type[ModelT],
        *,
        entity_type: str,
        search_fields: Sequence[str] = (),
        sortable_fields: Sequence[str] = (),
        default_sort: str = "created_at",
    ) -> None:
        self.model = model
        self.entity_type = entity_type
        self.search_fields = tuple(search_fields)
        self.sortable_fields = set(sortable_fields) | {"created_at", "updated_at"}
        self.default_sort = default_sort

    # -------- lecture --------
    def get(self, db: Session, obj_id: uuid.UUID) -> ModelT | None:
        return db.get(self.model, obj_id)

    def _apply_filters(self, stmt, *, q: str | None, filters: dict[str, Any]):
        if q and self.search_fields:
            pattern = f"%{q.strip()}%"
            clauses = [
                getattr(self.model, field).ilike(pattern)
                for field in self.search_fields
            ]
            stmt = stmt.where(or_(*clauses))
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        return stmt

    def list(
        self,
        db: Session,
        *,
        page: int = 1,
        size: int = 25,
        sort: str | None = None,
        order: str = "desc",
        q: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[Sequence[ModelT], int]:
        filters = filters or {}
        base = self._apply_filters(select(self.model), q=q, filters=filters)

        total = int(
            db.execute(
                self._apply_filters(
                    select(func.count()).select_from(self.model),
                    q=q,
                    filters=filters,
                )
            ).scalar_one()
        )

        sort_field = sort if sort in self.sortable_fields else self.default_sort
        column = getattr(self.model, sort_field, None)
        if column is not None:
            base = base.order_by(
                column.asc() if order == "asc" else column.desc()
            )

        base = base.offset((max(page, 1) - 1) * size).limit(size)
        items = db.execute(base).scalars().all()
        return items, total

    # -------- écriture (avec audit) --------
    def create(
        self, db: Session, data: dict, *, actor: str = "système", reason: str | None = None
    ) -> ModelT:
        obj = self.model(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        audit_service.log(
            db,
            entity_type=self.entity_type,
            action=AuditAction.CREATION,
            entity_id=obj.id,  # type: ignore[attr-defined]
            changes=diff_changes({}, model_to_dict(obj)),
            actor=actor,
            reason=reason,
        )
        return obj

    def update(
        self,
        db: Session,
        obj: ModelT,
        data: dict,
        *,
        actor: str = "système",
        reason: str | None = None,
    ) -> ModelT:
        before = model_to_dict(obj)
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        changes = diff_changes(before, model_to_dict(obj))
        if changes:
            audit_service.log(
                db,
                entity_type=self.entity_type,
                action=AuditAction.MODIFICATION,
                entity_id=obj.id,  # type: ignore[attr-defined]
                changes=changes,
                actor=actor,
                reason=reason,
            )
        return obj

    def delete(
        self, db: Session, obj: ModelT, *, actor: str = "système", reason: str | None = None
    ) -> None:
        entity_id = obj.id  # type: ignore[attr-defined]
        snapshot = model_to_dict(obj)
        db.delete(obj)
        db.commit()
        audit_service.log(
            db,
            entity_type=self.entity_type,
            action=AuditAction.SUPPRESSION,
            entity_id=entity_id,
            changes=diff_changes(snapshot, {}),
            actor=actor,
            reason=reason,
        )
