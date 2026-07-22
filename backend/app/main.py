"""Point d'entrée de l'application FastAPI."""
from __future__ import annotations

import logging
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.health import health as _health
from app.api.v1.endpoints.health import live as _live
from app.api.v1.endpoints.health import ready as _ready
from app.api.v1.endpoints.health import readiness as _readiness
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

# Journalisation structurée avant toute chose (Phase 8).
setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
log = logging.getLogger("app")

# Chemins ignorés par le journal des requêtes (sondes de santé bruyantes).
_QUIET_PATHS = {"/live", "/ready", "/readiness", "/api/v1/live", "/api/v1/ready",
                "/api/v1/readiness", "/api/v1/health"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("startup").info(
        "Démarrage de l'API.",
        extra={"extra_fields": {"env": settings.APP_ENV, "version": "1.0.0"}},
    )

    # 1) Garde-fous de configuration (Phase 9) — bloque la prod avec secrets par défaut.
    from app.core.runtime_checks import validate_runtime

    validate_runtime()

    # 2) Index de connaissance : reconstruction si « sale »/vide AVANT de servir
    #    (Phase 7 — jamais pendant une recherche).
    try:
        from app.services.knowledge_refresher import refresh_once, refresher

        refresh_once()
        refresher.start()
    except Exception:
        logging.getLogger("knowledge_index").warning(
            "Rafraîchissement initial de l'index impossible au démarrage.", exc_info=True
        )

    # 3) Reprise des ingestions/analyses interrompues (comportement existant).
    try:
        from app.db.session import SessionLocal
        from app.services.compliance_service import compliance_service
        from app.services.document_service import document_service

        db = SessionLocal()
        try:
            resumed = document_service.resume_interrupted(db)
            if resumed:
                logging.getLogger("ingestion").info(
                    "%s ingestion(s) interrompue(s) relancée(s).", resumed
                )
            resumed_analyses = compliance_service.resume_interrupted(db)
            if resumed_analyses:
                logging.getLogger("compliance").info(
                    "%s analyse(s) interrompue(s) relancée(s).", resumed_analyses
                )
        finally:
            db.close()
    except Exception:  # ne bloque jamais le démarrage de l'API
        logging.getLogger("ingestion").warning(
            "Reprise des ingestions impossible au démarrage.", exc_info=True
        )

    logging.getLogger("startup").info("API prête.")
    yield

    # Arrêt propre.
    try:
        from app.services.knowledge_refresher import refresher

        refresher.stop()
    except Exception:
        pass
    logging.getLogger("shutdown").info("Arrêt de l'API.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "API du copilote IA d'importation UM6P. "
        "La base de données est l'unique source de vérité."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Regex optionnel (ex. déploiements preview Vercel `https://.*\.vercel\.app`).
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Filet global : TOUTE exception non gérée est journalisée AVEC sa trace
    complète (type, message, fichier, ligne, pile), puis convertie en 500 JSON.

    La trace est émise à la fois via `exc_info` (rendu par le formateur) ET
    comme champ `traceback` en clair — garantissant qu'elle apparaît dans les
    logs quel que soit le formateur/handler (uvicorn, gunicorn, JSON, texte).
    """
    tb_frames = traceback.extract_tb(exc.__traceback__)
    last = tb_frames[-1] if tb_frames else None
    full_tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logging.getLogger("http").error(
        "Exception non gérée : %s: %s (%s:%s)",
        type(exc).__name__,
        exc,
        last.filename if last else "?",
        last.lineno if last else "?",
        exc_info=exc,
        extra={"extra_fields": {
            "method": request.method,
            "path": str(request.url.path),
            "exc_type": type(exc).__name__,
            "exc_message": str(exc),
            "exc_file": last.filename if last else None,
            "exc_line": last.lineno if last else None,
            "traceback": full_tb,
        }},
    )
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur."})


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Journal structuré par requête (hors sondes de santé).

    Les exceptions ne sont PAS journalisées ici : le gestionnaire global
    `unhandled_exception_handler` s'en charge (trace complète), on se contente
    de les laisser remonter.
    """
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    if request.url.path not in _QUIET_PATHS:
        logging.getLogger("http").info(
            "request",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": duration_ms,
            }},
        )
    return response


app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Alias racine des sondes (standards orchestrateur / PaaS Railway / Docker) — mêmes handlers.
app.add_api_route("/health", _health, tags=["Santé"])
app.add_api_route("/live", _live, tags=["Santé"])
app.add_api_route("/ready", _ready, tags=["Santé"])
app.add_api_route("/readiness", _readiness, tags=["Santé"])


@app.get("/", tags=["Racine"])
def root() -> dict[str, str]:
    return {
        "application": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }
