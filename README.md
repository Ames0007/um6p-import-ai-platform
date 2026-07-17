<div align="center">

# Assistant IA Import & Achats UM6P

**Copilote IA spécialisé dans l'importation au Maroc**, destiné au Département
des Achats, de la Supply Chain et de l'Import de l'Université Mohammed VI
Polytechnique (UM6P).

`um6p-import-ai-platform`

</div>

> ⚠️ L'IA ne **génère jamais** de codes SH, taxes, autorisations ou
> réglementations. La base de données PostgreSQL est **l'unique source de
> vérité**. Le modèle de langage se limite à comprendre la question, interroger
> la base et expliquer le résultat.

---

## Sommaire

- [Aperçu](#aperçu)
- [Architecture](#architecture)
- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Captures d'écran](#captures-décran)
- [Installation](#installation)
- [Développement](#développement)
- [Variables d'environnement](#variables-denvironnement)
- [Mise en place de la base de données](#mise-en-place-de-la-base-de-données)
- [Architecture IA](#architecture-ia)
- [Index de connaissance](#index-de-connaissance)
- [Flux d'analyse d'import](#flux-danalyse-dimport)
- [Feuille de route](#feuille-de-route)
- [Documentation](#documentation)
- [Licence](#licence)

---

## Aperçu

L'Assistant IA Import & Achats UM6P aide les équipes achats à déterminer, de
manière **fiable et traçable**, les informations douanières d'un produit importé
au Maroc : code SH (nomenclature harmonisée), taxes applicables, autorisations
requises et conformité d'une facture avant importation.

La philosophie du produit est **anti-hallucination** : toute donnée
réglementaire provient de PostgreSQL et de documents officiels ingérés ; l'IA
n'ajoute jamais d'information inventée et cite systématiquement ses sources
(document / chapitre / page).

## Architecture

```
┌────────────┐      HTTP/JSON      ┌────────────┐     SQL      ┌──────────────┐
│  Frontend  │  ───────────────▶   │  Backend   │  ─────────▶  │ PostgreSQL   │
│ Next.js 15 │  ◀───────────────   │  FastAPI   │  ◀─────────  │ + pgvector   │
│  (:3005)   │                     │  (:8000)   │              │  (:5432)     │
└────────────┘                     └─────┬──────┘              └──────────────┘
                                         │
                        ┌────────────────┼─────────────────┐
                        ▼                ▼                 ▼
                   ┌─────────┐     ┌───────────┐     ┌────────────┐
                   │  Redis  │     │  Worker   │     │  Claude    │
                   │ (files) │     │ ingestion │     │  API (IA)  │
                   └─────────┘     └───────────┘     └────────────┘
```

- **Frontend** — Next.js 15 (App Router), rendu et appels à l'API v1.
- **Backend** — FastAPI : recherche, IA, ingestion, conformité, administration.
- **PostgreSQL + pgvector** — source de vérité (codes SH, taxes, documents,
  index de connaissance, historique IA).
- **Redis + Worker** — file d'attente d'ingestion documentaire (asynchrone).
- **Claude API** — compréhension / explication uniquement (repli déterministe
  si aucune clé n'est fournie).

Détail : [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

## Fonctionnalités

- 💬 **Chat IA** ancré sur la base UM6P + documents officiels (citations tracées).
- 🏷️ **Recherche de code SH** (référentiel officiel) et 🔍 **recherche de produit**.
- 💰 Consultation des **taxes** · ✅ Vérification des **autorisations**.
- 📎 **Analyse de facture** avant import (OCR → rapprochement → conformité).
- 📚 **Bibliothèque documentaire** (import PDF/DOCX/XLSX/CSV/ZIP, ingestion asynchrone).
- 🗂️ **Administration** complète + assistant d'import Excel/CSV + piste d'audit.
- 📊 **Historique** des achats et tableau de bord.

## Technologies

| Couche | Technologies |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui, Framer Motion, Lucide, React Query |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Base de données | PostgreSQL 16 + pgvector |
| Cache / files | Redis, RQ (worker) |
| IA | Claude API (repli déterministe sans clé) |
| Auth | JWT (architecture prête pour un futur SSO) |
| Déploiement | Docker / Docker Compose |

## Captures d'écran

> 📷 **À venir.** Les captures d'écran seront déposées dans
> [`docs/screenshots/`](./docs/screenshots/) avant la publication publique.
> Écrans prévus : accueil / recherche, copilote IA, bibliothèque documentaire,
> analyse de conformité d'une facture.

## Installation

**Prérequis** : [Docker](https://docs.docker.com/get-docker/) et Docker Compose.

Runtime officiel : **Docker**. Une seule commande (fonctionne sans `.env`) :

```bash
git clone <repo> && cd um6p-import-ai-platform
docker compose up --build
```

- Frontend : http://localhost:3005
- API : http://localhost:8000 — Docs : http://localhost:8000/docs
- Santé : `GET /live` (liveness), `GET /ready` (readiness)

Démarrage ordonné et garanti : **postgres → migrate** (extensions + `alembic
upgrade head`) **→ backend + worker + frontend**. Le backend ne démarre jamais
avant la fin des migrations. Port PostgreSQL fixe (5432), aucun port dynamique.

## Développement

Exploitation locale (hors Docker) — voir [`docs/RUNTIME.md`](./docs/RUNTIME.md)
pour le détail. En résumé :

```bash
# Backend (depuis backend/)
cd backend
python -m venv .venv && .venv/Scripts/activate     # Windows
pip install -r requirements.txt
cp ../.env.example .env        # puis ajuster (voir ci-dessous)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (depuis frontend/)
cd frontend
npm install
npm run dev                    # http://localhost:3005
npm run build                  # build de production (validation)
```

> Le backend lit `backend/.env` (relatif au CWD de lancement). Ce fichier
> n'est **jamais** versionné.

## Variables d'environnement

Copiez [`.env.example`](./.env.example) et renseignez les valeurs. Principales
variables :

| Variable | Défaut (dev) | Rôle |
|---|---|---|
| `APP_ENV` | `development` | `development` (uvicorn) / `production` (gunicorn) |
| `POSTGRES_HOST` | `postgres` (Docker) / `localhost` (local) | Hôte PostgreSQL |
| `POSTGRES_PORT` | `5432` | Port PostgreSQL (fixe) |
| `POSTGRES_DB` | `um6p_import` | Base de données |
| `POSTGRES_USER` | `um6p` | Rôle applicatif |
| `POSTGRES_PASSWORD` | *(placeholder)* | Mot de passe — **à changer en prod** |
| `USE_TASK_QUEUE` | `true` (Docker) / `false` (local) | File RQ vs thread d'arrière-plan |
| `REDIS_URL` | `redis://redis:6379/0` | Redis (file d'ingestion) |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000,http://localhost:3005` | Origines CORS |
| `SECRET_KEY` | *(placeholder)* | Clé JWT — **≥ 32 caractères en prod** |
| `ANTHROPIC_API_KEY` | *(vide)* | Clé Claude — vide = repli déterministe |
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | Modèle Claude |
| `KI_REFRESH_INTERVAL_SECONDS` | `20` | Réconciliation de l'Index de connaissance |
| `OCR_ENABLED` / `OCR_PROVIDER` | `false` / `pdf_text` | OCR (hooks) |
| `EMBEDDINGS_ENABLED` | `false` | Recherche sémantique (hook) |

> 🔒 **Aucun secret ne doit être versionné.** `.env` et `backend/.env` sont
> ignorés par Git ; seul `.env.example` (placeholders) est publié.

## Mise en place de la base de données

- **Moteur** : PostgreSQL 16 + extension `pgvector`.
- **Extensions & schéma** : le service `migrate` exécute
  `database/init/01_extensions.sql` puis `alembic upgrade head` (voir
  [`backend/alembic/`](./backend/alembic/)).
- **Docker** : la base est initialisée automatiquement (volume `pgdata`).
- **Local** : pointez `POSTGRES_*` vers votre instance puis appliquez les
  migrations :

  ```bash
  cd backend && alembic upgrade head
  ```

- **Sauvegardes** : déposez les dumps `pg_dump` dans `database/backups/`
  (contenu ignoré par Git ; le dossier est conservé via `.gitkeep`).

## Architecture IA

Pipeline strictement ancré (jamais de réponse inventée) :

```
Question → Intention → Récupération PostgreSQL → Documents officiels
         → Construction du contexte → Claude (compréhension/explication)
         → Réponse + citations tracées + niveau de confiance
```

- Si `ANTHROPIC_API_KEY` est absente, le pipeline bascule en **mode repli
  déterministe** : réponses structurées à partir des seules données de la base,
  sans appel externe.
- Mémoire conversationnelle (questions de suivi), réponses en streaming (SSE),
  journalisation complète des requêtes IA.

Détail : [`docs/AI_COPILOT.md`](./docs/AI_COPILOT.md).

## Index de connaissance

- Table **matérialisée** (`knowledge_index`) construite **hors du chemin des
  requêtes** : les recherches ne reconstruisent jamais l'index (lecture seule).
- Reconstruction au **démarrage**, puis **réconciliation périodique**
  (`KI_REFRESH_INTERVAL_SECONDS`) lorsque les données source changent (imports,
  taxes, autorisations — signalés par des déclencheurs SQL).
- Recherche **plein texte** PostgreSQL (`to_tsvector`), avec traçabilité
  document / chapitre / page.

## Flux d'analyse d'import

```
Upload facture → OCR (pdf_text par défaut) → Extraction lignes
   → Rapprochement produit / code SH / taxes / autorisations
   → Comparaison de prix (seuil d'alerte) → Constats de risque
   → Rapport de conformité exportable (PDF / Excel / CSV)
```

Traitement en arrière-plan (worker), architecture OCR enfichable (pdf_text,
Tesseract, Azure, Google). Détail : [`docs/COMPLIANCE.md`](./docs/COMPLIANCE.md).

## Feuille de route

- [ ] **SSO Entra ID** (l'architecture JWT est déjà en place).
- [ ] **OCR réel** en production (Tesseract / Azure / Google) — hooks présents.
- [ ] **Recherche sémantique** par embeddings — hooks présents.
- [ ] Enrichissement des référentiels (produits, fournisseurs, autorisations).
- [ ] Tableaux de bord analytiques avancés.

## Documentation

| Document | Contenu |
|---|---|
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Architecture détaillée |
| [docs/CONVENTIONS.md](./docs/CONVENTIONS.md) | Conventions de code |
| [docs/RUNTIME.md](./docs/RUNTIME.md) | Exploitation, santé, migrations, logs |
| [docs/INGESTION.md](./docs/INGESTION.md) | Moteur d'ingestion documentaire |
| [docs/AI_COPILOT.md](./docs/AI_COPILOT.md) | Copilote IA |
| [docs/COMPLIANCE.md](./docs/COMPLIANCE.md) | Moteur de conformité à l'import |
| [docs/ADMINISTRATION.md](./docs/ADMINISTRATION.md) | Administration |
| [CHANGELOG.md](./CHANGELOG.md) · [CONTRIBUTING.md](./CONTRIBUTING.md) · [SECURITY.md](./SECURITY.md) | Processus projet |

## Licence

**Propriétaire — Tous droits réservés.**
© 2026 Université Mohammed VI Polytechnique (UM6P). Voir [LICENSE](./LICENSE).
