# Architecture — Assistant IA Import & Achats UM6P

## Vue d'ensemble

Monorepo composé d'un frontend Next.js et d'une API FastAPI, adossés à
PostgreSQL (avec `pgvector`) et Redis. L'IA (Claude) n'est qu'une couche
d'interprétation : **la base de données est l'unique source de vérité**.

```
┌────────────┐        HTTP/JSON        ┌────────────┐        SQL        ┌──────────────┐
│  Frontend  │  ───────────────────▶   │   Backend  │  ─────────────▶   │  PostgreSQL  │
│ Next.js 15 │                         │  FastAPI   │                   │  + pgvector  │
└────────────┘   ◀───────────────────  └────────────┘   ◀────────────   └──────────────┘
                                              │  ▲
                                              ▼  │
                                        ┌────────────┐        ┌────────────┐
                                        │   Redis    │        │ Claude API │
                                        └────────────┘        └────────────┘
```

## Principe fondamental (garde-fou IA)

Le modèle de langage se limite à :

1. **comprendre** la question de l'utilisateur ;
2. **interroger** la base via les services applicatifs ;
3. **expliquer** le résultat en français.

Il ne doit **jamais** inventer de code SH, taxe, autorisation ni réglementation.
Toute réponse doit être traçable à des enregistrements de la base (voir le champ
`Message.sources`).

## Frontend (`frontend/`)

- **Next.js 15 (App Router)** + TypeScript.
- **TailwindCSS** + **shadcn/ui** pour l'UI ; thème UM6P via variables CSS.
- **Framer Motion** pour les animations subtiles, **Lucide** pour les icônes.
- **React Query** pour l'état serveur (hooks dans `src/hooks`).
- Organisation par fonctionnalité : `components/{layout,chat,upload,home}`,
  `config/`, `lib/api/`, `app/` (routes).

## Backend (`backend/`)

Architecture en couches :

- `app/api/` — routeurs FastAPI (transport HTTP uniquement).
- `app/services/` — accès aux données et logique applicative.
- `app/models/` — modèles SQLAlchemy 2.0.
- `app/schemas/` — schémas Pydantic (contrats d'API).
- `app/core/` — configuration, sécurité (JWT).
- `app/db/` — moteur, sessions, base déclarative, client Redis.
- `alembic/` — migrations de schéma.

## Base de données

Entités : `countries`, `hs_codes`, `taxes`, `authorizations`, `suppliers`,
`products`, `purchase_history`, `invoices`, `conversations`, `messages`.

- Clés primaires **UUID** (générées par `pgcrypto`).
- Horodatage automatique (`created_at`, `updated_at`).
- Colonnes `embedding` (`pgvector`) sur `hs_codes` et `products` pour la
  future recherche sémantique.

## Authentification

JWT (module `app/core/security.py`). L'accès n'est pas encore imposé ;
l'architecture est prête pour un branchement **SSO** (OIDC/SAML) ultérieur.

## Déploiement

`docker compose up --build` orchestre PostgreSQL, Redis, l'API et le frontend.
Voir [`../README.md`](../README.md).
