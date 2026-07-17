"""Fabrique de routes CRUD génériques pour l'administration.

Chaque ressource obtient : liste paginée/filtrée/triée, création, création en
masse, lecture, mise à jour, suppression et export CSV — le tout audité.
"""
from __future__ import annotations

import csv
import io
import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_subject, get_db
from app.api.v1.admin.resources import ALLOWED_FILTERS, ResourceConfig
from app.schemas.pagination import Page


def _actor(subject: str | None) -> str:
    return subject or "système"


def _validate(schema, payload: dict, *, partial: bool = False):
    try:
        if partial:
            return schema.model_validate(payload)
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return "; ".join(str(v) for v in value) if isinstance(value, list) else str(value)
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def build_crud_router(config: ResourceConfig) -> APIRouter:
    router = APIRouter(prefix=f"/{config.name}", tags=[config.tag])
    crud = config.crud
    read_schema = config.read_schema

    def _read(obj) -> Any:
        return read_schema.model_validate(obj)

    @router.get("")
    def list_items(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        size: int = Query(25, ge=1, le=200),
        sort: str | None = None,
        order: str = Query("desc", pattern="^(asc|desc)$"),
        q: str | None = None,
        status: str | None = None,
        category: str | None = None,
        hs_code_id: uuid.UUID | None = None,
        country_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        country_of_origin_id: uuid.UUID | None = None,
        preferred_supplier_id: uuid.UUID | None = None,
    ):
        local = locals()
        filters = {f: local.get(f) for f in ALLOWED_FILTERS if local.get(f) is not None}
        items, total = crud.list(
            db, page=page, size=size, sort=sort, order=order, q=q, filters=filters
        )
        return Page.build([_read(i) for i in items], total, page, size)

    @router.post("", status_code=201)
    def create_item(
        payload: dict = Body(...),
        reason: str | None = None,
        db: Session = Depends(get_db),
        subject: str | None = Depends(get_current_subject),
    ):
        data = _validate(config.create_schema, payload)
        obj = crud.create(db, data.model_dump(), actor=_actor(subject), reason=reason)
        return _read(obj)

    @router.post("/bulk", status_code=201)
    def bulk_create(
        payload: list[dict] = Body(...),
        reason: str | None = None,
        db: Session = Depends(get_db),
        subject: str | None = Depends(get_current_subject),
    ):
        created = 0
        errors: list[dict] = []
        for index, row in enumerate(payload):
            try:
                data = config.create_schema.model_validate(row)
                crud.create(db, data.model_dump(), actor=_actor(subject), reason=reason)
                created += 1
            except (ValidationError, Exception) as exc:  # ligne fautive isolée
                errors.append({"row": index, "error": str(exc)})
        return {"created": created, "errors": errors}

    @router.get("/export")
    def export_csv(
        db: Session = Depends(get_db),
        q: str | None = None,
    ):
        items, _ = crud.list(db, page=1, size=100000, q=q)
        fields = list(read_schema.model_fields.keys())
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(fields)
        for item in items:
            dumped = _read(item).model_dump()
            writer.writerow([_stringify(dumped.get(f)) for f in fields])
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={config.name}.csv"
            },
        )

    @router.get("/{item_id}")
    def get_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
        obj = crud.get(db, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Élément introuvable.")
        return _read(obj)

    @router.patch("/{item_id}")
    def update_item(
        item_id: uuid.UUID,
        payload: dict = Body(...),
        reason: str | None = None,
        db: Session = Depends(get_db),
        subject: str | None = Depends(get_current_subject),
    ):
        obj = crud.get(db, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Élément introuvable.")
        data = _validate(config.update_schema, payload, partial=True)
        updated = crud.update(
            db, obj, data.model_dump(exclude_unset=True),
            actor=_actor(subject), reason=reason,
        )
        return _read(updated)

    @router.delete("/{item_id}", status_code=204)
    def delete_item(
        item_id: uuid.UUID,
        reason: str | None = None,
        db: Session = Depends(get_db),
        subject: str | None = Depends(get_current_subject),
    ):
        obj = crud.get(db, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Élément introuvable.")
        crud.delete(db, obj, actor=_actor(subject), reason=reason)

    return router
