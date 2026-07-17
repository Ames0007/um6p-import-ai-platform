"""Agrégation des routes de l'administration (préfixe /admin)."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.admin import audit, dashboard, details, importing, search
from app.api.v1.admin.crud_factory import build_crud_router
from app.api.v1.admin.resources import RESOURCES

admin_router = APIRouter(prefix="/admin")

# Fonctionnalités transverses
admin_router.include_router(dashboard.router)
admin_router.include_router(search.router)
admin_router.include_router(importing.router)
admin_router.include_router(audit.router)
admin_router.include_router(details.router)

# Ressources CRUD génériques
for _config in RESOURCES:
    admin_router.include_router(build_crud_router(_config))
