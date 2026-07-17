"""Service de journalisation (piste d'audit).

Toute modification du référentiel doit être tracée : qui, quand, ancienne et
nouvelle valeur, motif.
"""
from __future__ import annotations

import uuid
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction


def _jsonable(value: Any) -> Any:
    """Rend une valeur sérialisable en JSON pour le stockage de l'audit."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value"):  # Enum
        return value.value
    return value


def diff_changes(before: dict | None, after: dict | None) -> dict:
    """Construit un dictionnaire {champ: {old, new}} des différences."""
    before = before or {}
    after = after or {}
    changes: dict[str, dict] = {}
    for key in set(before) | set(after):
        old = _jsonable(before.get(key))
        new = _jsonable(after.get(key))
        if old != new:
            changes[key] = {"old": old, "new": new}
    return changes


class AuditService:
    def log(
        self,
        db: Session,
        *,
        entity_type: str,
        action: AuditAction,
        entity_id: uuid.UUID | None = None,
        changes: dict | None = None,
        actor: str = "système",
        reason: str | None = None,
        commit: bool = True,
    ) -> AuditLog:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            changes=changes or None,
            reason=reason,
        )
        db.add(entry)
        if commit:
            db.commit()
        return entry

    def list(
        self,
        db: Session,
        *,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> Sequence[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        return db.execute(stmt.limit(limit)).scalars().all()


audit_service = AuditService()
