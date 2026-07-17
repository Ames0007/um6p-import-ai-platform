# Backend FastAPI — image unique (dev via --reload, prod via gunicorn).
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances système minimales (psycopg, build, healthcheck).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ ./
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

# Sonde conteneur = LIVENESS (le process répond). La readiness est vérifiée
# séparément par l'orchestrateur / le compose (dépendances DB, Redis, worker).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/live || exit 1

ENTRYPOINT ["/entrypoint.sh"]
