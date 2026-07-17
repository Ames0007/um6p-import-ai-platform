"""Agrégation des routes de l'API v1."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.admin.router import admin_router
from app.api.v1.endpoints import (
    authorizations,
    chat,
    documents,
    health,
    hs_codes,
    import_analysis,
    invoices,
    knowledge,
    products,
    purchase_history,
    suppliers,
    taxes,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(products.router)
api_router.include_router(hs_codes.router)
api_router.include_router(taxes.router)
api_router.include_router(authorizations.router)
api_router.include_router(suppliers.router)
api_router.include_router(purchase_history.router)
api_router.include_router(invoices.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge.router)
api_router.include_router(import_analysis.router)
api_router.include_router(admin_router)
