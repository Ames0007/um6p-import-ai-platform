# Rapport de durcissement post-récupération

**Projet :** Assistant IA Import & Achats UM6P
**Date :** 2026-07-17
**Portée :** durcissement opérationnel uniquement — **aucune** modification de la
logique applicative, de l'IA, de la recherche, du pipeline d'ingestion, de
l'Index de connaissance, du comportement de l'API, des migrations ni des
**données** de la base récupérée.
**Objectif :** rendre l'environnement récupéré **permanent, reproductible et sûr**.

---

## 0. Contexte

La base PostgreSQL a été récupérée (voir le rapport de récupération). Le cluster
récupéré est désormais la **base officielle** :

| Élément | Valeur |
|---|---|
| Moteur | PostgreSQL 16 (binaires `pgserver`) |
| Hôte / port | `localhost:5432` (port fixe) |
| Base | `um6p_import` |
| Rôle | `postgres` (superuser, authentification `trust`) |
| PGDATA actif | `database/recovered_pgdata/` (copie de travail) |
| PGDATA original | `…\Temp\claude\pgdata_val` (figé, jamais démarré) |

**Seul problème restant avant ce durcissement :** le backend ne fonctionnait
qu'avec des variables d'environnement fournies *au lancement* (runtime). Rien
n'était persisté sur disque → un redémarrage sans ces variables retombait sur le
rôle `um6p` (inexistant dans le cluster récupéré) et échouait. Ce rapport corrige
ce point de manière permanente, **sans créer de nouveau rôle**.

---

## 1. Changements de configuration

Un fichier de configuration **local et persistant** a été créé pour le backend :
`backend/.env`. Il fige la connexion au cluster récupéré.

```dotenv
APP_ENV=development
LOG_LEVEL=INFO
LOG_FORMAT=json

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=um6p_import
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

USE_TASK_QUEUE=false

BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:3005

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-opus-4-8
```

**Pourquoi `backend/.env` et non le `.env` racine :**

- Le backend est lancé par `uvicorn app.main:app` avec **CWD = `backend/`**.
  `pydantic-settings` lit `env_file=".env"` **relativement au CWD** → il lit donc
  `backend/.env`. C'est le seul fichier qui pilote réellement la connexion locale.
- Le `.env` **racine** contient volontairement des valeurs **Docker**
  (`POSTGRES_HOST=postgres`). Il est utilisé par `docker compose` pour
  l'interpolation `${…}`. **Il n'a pas été modifié** pour ne pas perturber la
  stack Docker.
- **Aucun impact sur Docker :** `docker-compose.yml` injecte des variables
  d'environnement **réelles** (bloc `x-backend-env`). Dans `pydantic-settings`,
  les variables d'environnement réelles ont **priorité** sur le fichier `.env`.
  `backend/.env` est donc **ignoré / surchargé** à l'intérieur des conteneurs.

**Aucun code applicatif n'a été touché** — `backend/app/core/config.py` est
inchangé (les valeurs par défaut y demeurent ; seul le fichier `.env` fournit
désormais les valeurs effectives en local).

---

## 2. Fichiers modifiés

| Fichier | Nature | Action |
|---|---|---|
| `backend/.env` | **créé** | configuration DB locale persistante (non versionné) |
| `.gitignore` | **modifié** | ajout des règles de protection données/sauvegardes |
| `docs/POST_RECOVERY_HARDENING_REPORT.md` | **créé** | ce rapport |

**Non modifié (volontairement) :** `backend/app/**` (logique, IA, recherche,
ingestion, Index de connaissance, API), migrations Alembic, `.env` racine,
`docker-compose.yml`, extensions PostgreSQL, données du cluster récupéré.

> Note : les autres fichiers apparaissant comme « modifiés » dans `git status`
> (pages frontend, `pipeline.py`, `README.md`, compose, etc.) proviennent des
> sprints **antérieurs** (stabilisation, port 3005) et sont hors périmètre de ce
> durcissement.

---

## 3. Protection Git

Règles ajoutées à `.gitignore` (les règles existantes ont été **conservées**) :

```gitignore
# Cluster PostgreSQL récupéré + sauvegardes (ne JAMAIS versionner : données)
database/recovered_pgdata/
database/backups/*.sql
database/backups/*.dump
database/backups/*.tar
database/backups/*.backup
# Artefacts d'exécution PostgreSQL
postmaster.pid
postmaster.opts
*.wal
pg_wal/
recovery.log
```

**Vérification (`git check-ignore -v`) :**

| Chemin | Ignoré par |
|---|---|
| `database/recovered_pgdata/PG_VERSION` | `.gitignore:35` ✅ |
| `database/backups/…​.sql` | `.gitignore:36` ✅ |
| `database/backups/…​.dump` | `.gitignore:37` ✅ |
| `backend/.env` | `.gitignore:23` (`.env`) ✅ |

`git ls-files database/recovered_pgdata database/backups` → **vide** (aucun
fichier de données ou de sauvegarde n'a jamais été suivi).

`git status --short` ne fait apparaître **ni données PostgreSQL, ni
sauvegardes, ni `backend/.env`, ni artefacts d'exécution** — uniquement des
fichiers source/config (dont ce durcissement : `.gitignore`).

---

## 4. Persistance de la base de données

- **Cluster actif :** `database/recovered_pgdata/` — hors de `Temp`, dans le
  dépôt (mais **ignoré par Git**), démarré sur `127.0.0.1:5432` (pid 35540).
  **Non touché** par ce durcissement.
- **Original figé :** `…\Temp\claude\pgdata_val` — jamais démarré, conservé comme
  instantané de sécurité.
- **Sauvegardes logiques** dans `database/backups/` :

  | Fichier | Taille | Restauration |
  |---|---|---|
  | `um6p_import_20260717_155822.sql` | 4,65 Mo | `psql` |
  | `um6p_import_20260717_155822.dump` | 838 Ko | `pg_restore` |

- **Connexion persistée :** le backend lit maintenant `backend/.env` à chaque
  démarrage → plus aucune dépendance à des variables passées au lancement.

---

## 5. Résultats de vérification

Backend **redémarré à froid**, variables d'environnement `POSTGRES_*` /
`USE_TASK_QUEUE` **explicitement effacées** du shell avant lancement, afin de
prouver que `backend/.env` est bien la **seule** source de configuration.

**Démarrage :** `Application startup complete.` / `API prête.` — connexion à la
base réussie via le rôle `postgres` (aucune variable runtime), Index de
connaissance vérifié, rafraîchisseur démarré.

| Vérification | Endpoint / action | Résultat |
|---|---|---|
| Connexion base | (démarrage) | **OK** — connecté `postgres@localhost:5432/um6p_import` |
| Liveness | `GET /api/v1/live` | **200** `{"status":"alive"}` |
| Readiness | `GET /api/v1/ready` | **200** `ready` — database ok, knowledge_index ok (2693, `dirty=false`) |
| Recherche SH | `GET /api/v1/hs-codes/search?q=3104.20` | **200** → Chlorure de potassium (Chapitre 31) |
| Recherche SH | `GET /api/v1/hs-codes/search?q=urée` | **200** → 3102.10 Urée |
| Recherche connaissances | `GET /api/v1/knowledge/search?q=engrais` | **200** — `hits`/`total` renseignés |
| Endpoint IA | `POST /api/v1/chat/ask` | **200** — réponse ancrée, 3 sources (mode repli déterministe) |
| Endpoint import | `GET /api/v1/import-analysis` | **200** `[]` (joignable) |

**Services en cours d'exécution :**

| Service | Port | PID |
|---|---|---|
| PostgreSQL (cluster récupéré) | 5432 | 35540 |
| Backend FastAPI (via `backend/.env`) | 8000 | 33148 |
| Frontend Next.js | 3005 | 12912 |

**Conclusion :** tout fonctionne à partir de la **seule** configuration
persistante. Le redémarrage à froid est reproductible.

---

## 6. Risques opérationnels restants

1. **CWD de lancement obligatoire.** `backend/.env` n'est lu que si le backend
   est lancé depuis `backend/` (`uvicorn app.main:app`). Un lancement depuis la
   racine lirait le `.env` racine (valeurs Docker → échec en local). → Toujours
   démarrer depuis `backend/`.
2. **Cluster hors de Git / non sauvegardé automatiquement.**
   `database/recovered_pgdata/` est volontairement ignoré : il **n'est pas**
   sauvegardé par le dépôt. Seules les sauvegardes `pg_dump` du 2026-07-17 font
   foi hors du cluster. → Planifier des `pg_dump` réguliers.
3. **Absence de superviseur.** PostgreSQL et le backend sont des processus
   lancés manuellement : ils **ne redémarrent pas** automatiquement après un
   reboot de la machine. → Voir §7 (service/tâche planifiée).
4. **Authentification `trust` + secrets par défaut.** Le cluster utilise `trust`
   (aucun mot de passe) et `SECRET_KEY`/`POSTGRES_PASSWORD` restent des valeurs
   de développement. Acceptable en local, **inacceptable en production**.
5. **Original en zone volatile.** `…\Temp\claude\pgdata_val` peut être purgé par
   Windows. Il est désormais redondant (copie + 2 sauvegardes) mais ne doit plus
   servir de référence.
6. **Divergence Docker / local.** Deux chemins de configuration coexistent
   (Docker via `x-backend-env`, local via `backend/.env`). Documenté ici, mais à
   garder à l'esprit lors d'un futur passage à Docker (données dans le volume
   `pgdata`, non dans `recovered_pgdata`).

---

## 7. Améliorations futures recommandées

1. **Sauvegardes planifiées.** Tâche planifiée Windows quotidienne :
   `pg_dump -Fc um6p_import` → `database/backups/`, avec rotation (rétention 7/30 j).
2. **Démarrage supervisé.** Encapsuler PostgreSQL (`pg_ctl`) + backend + frontend
   dans un script de démarrage unique (ou des tâches planifiées « au démarrage »)
   pour survivre à un reboot, sans dépendre d'un lancement manuel.
3. **Consolider un chemin unique.** À terme, réunifier local et Docker : soit
   migrer les données récupérées dans le volume Docker `pgdata` et repasser à
   `docker compose up`, soit officialiser le cluster local — pour éviter deux
   sources de vérité.
4. **Durcir les secrets** avant toute exposition : `SECRET_KEY` fort,
   mot de passe PostgreSQL réel, `pg_hba.conf` en `scram-sha-256` plutôt que
   `trust`, CORS restreint. (Le backend en `APP_ENV=production` refuse déjà les
   valeurs par défaut.)
5. **Créer un rôle applicatif `um6p`** (hors périmètre ici, explicitement
   interdit) le jour où l'on voudra revenir aux valeurs par défaut du code sans
   `backend/.env`, avec privilèges limités (non-superuser).
6. **Sonde de sauvegarde.** Vérifier périodiquement l'intégrité des dumps
   (`pg_restore --list`) pour garantir qu'ils sont restaurables.

---

## Conclusion

L'environnement récupéré est désormais **permanent, reproductible et sûr** :

- la configuration de connexion est **persistée** (`backend/.env`), sans aucune
  variable runtime et **sans modification de code** ;
- Git ne suivra **jamais** les données du cluster, les sauvegardes ni les
  artefacts d'exécution ;
- le backend redémarre à froid et **tous les endpoints critiques** (live, ready,
  recherche SH, recherche connaissances, IA, import) répondent correctement
  contre la base récupérée ;
- les données du cluster récupéré n'ont **pas** été modifiées.

**La récupération est déclarée opérationnelle de façon permanente.**
