# Runtime & Exploitation — Assistant IA Import & Achats UM6P

Runtime officiel : **Docker**. Aucun script manuel, aucun port dynamique.

## Démarrer (développement)

```bash
git clone <repo> && cd assistant-ia-import-um6p
docker compose up --build
```

C'est la seule commande. Elle démarre, dans l'ordre garanti :

1. **postgres** (pgvector, port fixe `5432`) → attend `pg_isready`.
2. **redis** → attend `redis-cli ping`.
3. **migrate** (one-shot) → crée les extensions (`pgcrypto`, `vector`, `pg_trgm`)
   puis `alembic upgrade head`. **Le backend ne démarre jamais avant sa fin.**
4. **backend** (FastAPI, `--reload`) → `http://localhost:8000`
5. **worker** (RQ, ingestion documentaire)
6. **frontend** (Next.js dev) → `http://localhost:3005`

Fonctionne **sans `.env`** (valeurs de développement par défaut). Pour
personnaliser : `cp .env.example .env`.

## Démarrer (production)

```bash
cp .env.example .env      # renseignez SECRET_KEY, POSTGRES_PASSWORD, CORS…
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Différences : `APP_ENV=production` → **Gunicorn** (pas de `--reload`), **aucun
montage de code source** (l'image fait foi, jamais de code périmé), frontend
**construit** (`next build`/`next start`). Le backend **refuse de démarrer**
avec un `SECRET_KEY`/mot de passe par défaut ou un CORS `*`.

## Santé

| Sonde | URL | Rôle |
|---|---|---|
| Liveness | `GET /live` · `GET /api/v1/live` | le process répond (jamais de dépendance) |
| Readiness | `GET /ready` · `GET /readiness` · `GET /api/v1/ready` | Base + Index + Redis + Worker ; `503` si non prêt |
| Simple | `GET /api/v1/health` | compat rétro |

La sonde Docker du backend cible `/api/v1/live`.

## Migrations

Automatiques via le service `migrate`. Manuellement :

```bash
docker compose run --rm migrate
# ou dans un backend en cours d'exécution :
docker compose exec backend alembic upgrade head
```

## Index de connaissance

Les **recherches ne reconstruisent jamais** l'index (lecture seule). La
reconstruction a lieu hors du chemin des requêtes : au démarrage puis
périodiquement (`KI_REFRESH_INTERVAL_SECONDS`) lorsque les données source
changent (imports, taxes, autorisations — signalées par les déclencheurs SQL).

## Journalisation

Logs **JSON structurés** sur stdout (`LOG_FORMAT=text` pour un format lisible).

```bash
docker compose logs -f backend worker
```

## Commandes utiles

```bash
docker compose ps                      # état des services
docker compose down                    # arrêt (conserve les volumes)
docker compose down -v                 # arrêt + purge des données
docker compose up --build -d backend   # reconstruire un service
```
