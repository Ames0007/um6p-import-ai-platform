# Contribuer au projet

Merci de votre intérêt pour **Assistant IA Import & Achats UM6P**.

> ℹ️ Ce logiciel est **propriété de l'UM6P** (voir [LICENSE](./LICENSE)). Les
> contributions sont réservées aux membres de l'équipe UM6P et aux
> collaborateurs explicitement autorisés. Toute contribution externe suppose un
> accord écrit préalable avec l'UM6P.

## Principes non négociables

1. **L'IA ne génère jamais** de codes SH, taxes, autorisations ou réglementations.
   PostgreSQL est **l'unique source de vérité** ; le modèle se limite à comprendre,
   interroger et expliquer. Toute PR qui contourne ce principe sera refusée.
2. **Langue** : interface et réponses en **français**.
3. **Identité UM6P** : fond blanc, orange réservé aux actions/états actifs.

## Mise en place

```bash
git clone <repo> && cd um6p-import-ai-platform
docker compose up --build          # stack complète (recommandé)
```

Détails d'exploitation locale (hors Docker) : voir [docs/RUNTIME.md](./docs/RUNTIME.md).

## Flux de travail Git

- Branche par fonctionnalité : `feat/…`, `fix/…`, `docs/…`, `chore/…`.
- Ne jamais committer directement sur `main`.
- Ouvrez une Pull Request décrivant le **quoi** et le **pourquoi**.

### Convention de commits

Format [Conventional Commits](https://www.conventionalcommits.org/fr/) :

```
type(portée): résumé à l'impératif

Corps optionnel expliquant le pourquoi.
```

Types : `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`.

## Qualité attendue avant une PR

| Couche | Commande | Attendu |
|---|---|---|
| Frontend | `npm run build` (dans `frontend/`) | build réussi, pas d'erreur de type |
| Frontend | `npm run lint` | aucune erreur ESLint |
| Backend | `alembic upgrade head` | migrations à jour |
| Backend | `pytest` (si applicable) | tests au vert |

- **Aucun secret** dans le code ni dans les commits (voir [SECURITY.md](./SECURITY.md)).
- Respecter la structure existante (`backend/`, `frontend/`, `database/`, `docs/`).
- Mettre à jour la documentation et le [CHANGELOG](./CHANGELOG.md) si nécessaire.

## Signalement de bogues

Ouvrez une *issue* décrivant : le comportement observé, le comportement attendu,
les étapes de reproduction et l'environnement. Pour une faille de sécurité,
**n'ouvrez pas d'issue publique** — suivez [SECURITY.md](./SECURITY.md).

## Code de conduite

Toute participation est régie par notre [Code de conduite](./CODE_OF_CONDUCT.md).
