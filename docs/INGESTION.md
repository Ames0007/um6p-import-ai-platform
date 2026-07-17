# Moteur d'ingestion documentaire (Phase 2)

Transforme les documents officiels de la douane marocaine en une base de
connaissances interrogeable. **C'est l'unique source de vérité de l'IA** : rien
n'est inventé, tout est extrait puis tracé jusqu'à sa page d'origine.

## Pipeline

```
Fichier (PDF/DOCX/XLSX/CSV/ZIP)
   ↓  extraction de texte (pypdf / python-docx / openpyxl / csv)
   ↓  détection des pages scannées  →  OCR (hook, si activé)
   ↓  détection structure : chapitre / section
   ↓  détection des codes SH  →  table HS_REFERENCES (traçable)
   ↓  détection des tables de taxes / autorisations (comptage + repérage)
   ↓  découpage en chunks (avec chevauchement)
   ↓  préparation des embeddings (hook, si activé)
   ↓  stockage PostgreSQL : TEXT_CHUNKS + HS_REFERENCES + IMPORT_HISTORY
```

Code : [`backend/app/ingestion/`](../backend/app/ingestion) — orchestrateur
`pipeline.py`, extracteurs, `detectors/`, `ocr/`, `embeddings/`, `chunking.py`.

## Tables

| Table                 | Rôle                                                        |
| --------------------- | ----------------------------------------------------------- |
| `documents`           | Métadonnées + statut + checksum + pages                     |
| `text_chunks`         | Fragments recherchables + `embedding` (pgvector)            |
| `hs_references`       | Codes SH détectés, localisés (page/chapitre/section)        |
| `document_references` | Citations reliant un produit à un passage précis            |
| `import_history`      | Exécutions : temps, statut, erreurs, progression, stats     |

## Exécution asynchrone

- `USE_TASK_QUEUE=true` → file d'attente **RQ** traitée par le service `worker`
  (durable, adapté aux documents > 1000 pages).
- Sinon → **thread d'arrière-plan** (pratique en développement local).
- **Reprise** : au démarrage de l'API, les documents restés `en_traitement`
  sont relancés ; le pipeline reprend à `processed_pages` (idempotent).
- **Dédoublonnage** : empreinte SHA-256 ; un contenu identique est refusé
  (409) sauf `allow_duplicate=true`.

## OCR & embeddings (hooks)

Désactivés par défaut, branchés via des interfaces :

- OCR : `app/ingestion/ocr/` — `NoOpOcrProvider` (défaut) ou
  `TesseractOcrProvider` (`OCR_ENABLED=true` + `pytesseract`/`pdf2image` +
  binaires `tesseract-ocr`/`poppler`). Les pages scannées sont toujours
  signalées, même sans OCR.
- Embeddings : `app/ingestion/embeddings/` — `NoOpEmbeddingProvider` (défaut).
  Sans embeddings, la recherche se rabat sur le plein texte.

## Recherche

`GET /api/v1/knowledge/search?q=centrifuge` renvoie les passages pertinents
avec leur traçabilité :

```
Source : Code des Douanes 2022 — Chapitre 84 — Page 154
```

Sémantique (cosinus pgvector) si les embeddings sont présents, sinon repli
textuel insensible à la casse.

## Gestion des erreurs

Détectées et consignées dans `import_history.errors` : PDF corrompu, page
illisible, page scannée sans OCR, échec OCR, format non pris en charge,
doublon. Un document terminé avec erreurs passe au statut `partiel`.
