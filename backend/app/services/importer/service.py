"""Assistant d'import : aperçu (mapping) puis validation (upsert + rapport)."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AuditAction
from app.services.audit_service import audit_service
from app.services.importer.parsing import read_tabular
from app.services.importer.specs import get_spec
from app.schemas.importer import (
    ImportCommitRequest,
    ImportPreviewResponse,
    ImportReport,
    ImportRowError,
)

SAMPLE_SIZE = 10


class ImportService:
    def _imports_dir(self) -> Path:
        path = Path(settings.DOCUMENTS_DIR).parent / "imports"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _resolve_token_path(self, token: str) -> Path:
        for candidate in self._imports_dir().glob(f"{token}__*"):
            return candidate
        raise FileNotFoundError("Fichier d'import expiré ou introuvable.")

    # -------- étape 1 : aperçu + proposition de mapping --------
    def preview(self, file: UploadFile, resource: str) -> ImportPreviewResponse:
        spec = get_spec(resource)
        token = uuid.uuid4().hex
        suffix = Path(file.filename or "import.csv").suffix.lower() or ".csv"
        stored = self._imports_dir() / f"{token}__{Path(file.filename or 'import').name}"
        with stored.open("wb") as buffer:
            buffer.write(file.file.read())

        columns, rows = read_tabular(stored)
        return ImportPreviewResponse(
            token=token,
            resource=resource,
            columns=columns,
            sample_rows=[
                {k: _stringify(v) for k, v in r.items()} for r in rows[:SAMPLE_SIZE]
            ],
            total_rows=len(rows),
            target_fields=spec.target_fields,
            suggested_mapping=spec.suggest_mapping(columns),
        )

    # -------- étape 2 : validation + upsert --------
    def commit(
        self, db: Session, req: ImportCommitRequest, *, actor: str = "système"
    ) -> ImportReport:
        spec = get_spec(req.resource)
        path = self._resolve_token_path(req.token)
        _columns, rows = read_tabular(path)

        created = updated = skipped = 0
        errors: list[ImportRowError] = []

        for index, raw in enumerate(rows):
            line = index + 2  # +1 en-tête, +1 base 1
            values = {
                target: raw.get(source)
                for source, target in req.mapping.items()
                if source in raw
            }
            outcome = None
            try:
                with db.begin_nested():
                    kwargs = spec.build(db, values)
                    existing = self._find_existing(db, spec, kwargs, req.dedup_field)
                    if existing is not None and not req.update_existing:
                        outcome = "skip"
                    elif existing is not None:
                        for key, value in kwargs.items():
                            setattr(existing, key, value)
                        db.flush()
                        outcome = "update"
                    else:
                        db.add(spec.model(**kwargs))
                        db.flush()
                        outcome = "create"
            except Exception as exc:  # ligne invalide → consignée, on continue
                errors.append(ImportRowError(row=line, message=str(exc)))
                continue

            if outcome == "create":
                created += 1
            elif outcome == "update":
                updated += 1
            elif outcome == "skip":
                skipped += 1

        db.commit()

        audit_service.log(
            db,
            entity_type=spec.resource,
            action=AuditAction.IMPORT,
            changes={
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "errors": len(errors),
            },
            actor=actor,
            reason=req.reason or "Import de données",
        )

        return ImportReport(
            resource=req.resource,
            total=len(rows),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )

    def _find_existing(self, db, spec, kwargs: dict, dedup_field: str | None):
        if spec.find_existing is not None:
            return spec.find_existing(db, kwargs)
        field = dedup_field or spec.dedup_field
        if field and kwargs.get(field) is not None:
            return db.execute(
                select(spec.model).where(getattr(spec.model, field) == kwargs[field])
            ).scalar_one_or_none()
        return None


def _stringify(value) -> str:
    if value is None:
        return ""
    return str(value)


import_service = ImportService()
