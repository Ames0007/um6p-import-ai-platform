# Journal des modifications

Toutes les évolutions notables de ce projet sont documentées dans ce fichier.

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le projet suit le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

### À venir
- Authentification SSO (Entra ID) — architecture JWT déjà en place.
- OCR réel (Tesseract / Azure / Google) — hooks présents, désactivés par défaut.
- Recherche sémantique par embeddings — hooks présents, désactivés par défaut.

## [1.0.0] — 2026-07-17

Première version publique — **release initiale**.

### Ajouté
- **Copilote IA** ancré exclusivement sur la base UM6P et les documents officiels
  (aucune génération de codes SH, taxes ou réglementations par le modèle).
- **Recherche** de produits et de **codes SH** (référentiel officiel), consultation
  des **taxes** et vérification des **autorisations**.
- **Bibliothèque documentaire** : import PDF/DOCX/XLSX/CSV/ZIP et pipeline
  d'ingestion asynchrone (extraction, détection SH/taxes, traçabilité page/chapitre).
- **Index de connaissance** : table matérialisée reconstruite hors du chemin des
  requêtes (au démarrage puis réconciliation périodique), recherche plein texte
  PostgreSQL (`to_tsvector`).
- **Moteur de conformité à l'import** : analyse de facture (OCR → rapprochement →
  conformité), rapport exportable (PDF/Excel/CSV).
- **Administration** complète (produits, codes SH, taxes, autorisations,
  fournisseurs, achats) + assistant d'import Excel/CSV + piste d'audit.
- **Frontend** Next.js 15 (App Router, TypeScript, TailwindCSS) sur le port 3005.
- **Backend** FastAPI + SQLAlchemy + Alembic, PostgreSQL 16 + pgvector.
- **Runtime Docker** : `docker compose up --build` (postgres → migrate → backend
  → worker → frontend), sondes de santé `/live` et `/ready`.
- **Documentation** : architecture, conventions, ingestion, copilote IA,
  conformité, runtime.

### Sécurité
- Aucun secret versionné : `.env` ignoré, `.env.example` fourni comme gabarit.
- Le backend en production refuse de démarrer avec un `SECRET_KEY` / mot de passe
  par défaut ou un CORS `*`.

[Non publié]: https://github.com/UM6P/um6p-import-ai-platform/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/UM6P/um6p-import-ai-platform/releases/tag/v1.0.0
