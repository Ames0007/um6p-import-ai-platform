# Conventions — Assistant IA Import & Achats UM6P

## Langue

- **Tout** est en français : libellés, boutons, messages d'erreur, réponses IA,
  commentaires métier, documentation.
- Les identifiants techniques (noms de variables, tables, colonnes) restent en
  anglais pour la cohérence du code ; les libellés utilisateur sont en français.

## Identité visuelle UM6P

| Rôle              | Couleur   | Hex       |
| ----------------- | --------- | --------- |
| Primaire (orange) | Orange    | `#D7492A` |
| Orange secondaire | Orange 2  | `#ED6E47` |
| Charbon (texte)   | Charcoal  | `#3B3B3C` |
| Fond              | Blanc     | `#FFFFFF` |

Règles :

- Fond **blanc** dominant, beaucoup d'espace, coins arrondis, typographie nette.
- L'**orange est réservé** aux boutons, états actifs, icônes et mises en avant.
  Ne jamais surcharger l'interface d'orange.
- Animations **subtiles** (Framer Motion), interface responsive et accessible.

Les couleurs sont centralisées :

- Frontend : variables CSS dans `frontend/src/app/globals.css` +
  `tailwind.config.ts`.
- Partagé : `shared/constants.ts` (`UM6P_COLORS`).

## Frontend

- Composants serveur par défaut ; `"use client"` uniquement si nécessaire.
- UI réutilisable dans `src/components/ui` (convention shadcn/ui).
- Fusion des classes via `cn()` (`src/lib/utils.ts`).
- Accès API centralisé dans `src/lib/api` ; état serveur via React Query.

## Backend

- **SQLAlchemy 2.0** (types `Mapped`) ; migrations via **Alembic**.
- Les routeurs ne contiennent pas de logique métier : ils délèguent aux
  **services** (`app/services`).
- Schémas Pydantic pour toutes les entrées/sorties.
- Aucune donnée réglementaire ne doit être codée en dur ni générée : elle
  provient des tables de référence.

## Git

- Branche principale : `main`.
- Commits clairs et atomiques, en français de préférence.
