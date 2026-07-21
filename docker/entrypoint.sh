#!/bin/sh
# Point d'entrée backend (Phase 6).
# - production : Gunicorn + workers Uvicorn (pas de --reload, pas de code périmé).
# - développement : Uvicorn --reload (rechargement à chaud du code monté).
# Les migrations sont gérées par le service `migrate` (le backend ne démarre
# jamais avant leur fin) ; RUN_MIGRATIONS=1 permet un filet de sécurité optionnel.
set -e

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "[entrypoint] python -m app.db.bootstrap && alembic upgrade head"
  python -m app.db.bootstrap
  alembic upgrade head
fi

# Port d'écoute : $PORT est injecté par les PaaS (Railway, etc.) ; 8000 sinon
# (Docker / compose / local). Le comportement historique est préservé.
PORT="${PORT:-8000}"

case "$APP_ENV" in
  production|prod)
    echo "[entrypoint] mode PRODUCTION : gunicorn (${WEB_CONCURRENCY:-2} workers) sur :${PORT}"
    exec gunicorn app.main:app \
      -k uvicorn.workers.UvicornWorker \
      -w "${WEB_CONCURRENCY:-2}" \
      -b "0.0.0.0:${PORT}" \
      --timeout "${WEB_TIMEOUT:-120}" \
      --graceful-timeout 30 \
      --access-logfile - \
      --error-logfile -
    ;;
  *)
    echo "[entrypoint] mode DÉVELOPPEMENT : uvicorn --reload sur :${PORT}"
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --reload
    ;;
esac
