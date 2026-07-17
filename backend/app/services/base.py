"""Service générique de lecture (couche d'accès aux données).

Les services encapsulent l'accès à la base. Aucune règle métier « inventée »
n'est autorisée : les données proviennent exclusivement de PostgreSQL.
"""
from __future__ import annotations

import uuid
from typing import Generic, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base_class import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseService(Generic[ModelT]):
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    def get(self, db: Session, obj_id: uuid.UUID) -> ModelT | None:
        return db.get(self.model, obj_id)

    def list(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelT]:
        stmt = select(self.model).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()
