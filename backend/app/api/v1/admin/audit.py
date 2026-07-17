"""Endpoint de consultation de la piste d'audit."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.admin import AuditLogRead
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["Admin · Audit"])


@router.get("", response_model=list[AuditLogRead])
def list_audit(
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    entries = audit_service.list(
        db, entity_type=entity_type, entity_id=entity_id, limit=limit
    )
    return [AuditLogRead.model_validate(e) for e in entries]
