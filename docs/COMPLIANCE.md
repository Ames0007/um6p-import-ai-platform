# Moteur d'intelligence de conformité à l'import (Phase 5)

Automatise l'analyse des factures fournisseurs **avant importation**. Le rapport
généré devient le document opérationnel des agents achats/import.

## Chaîne de traitement (`backend/app/compliance/`)

```
Facture (PDF / PDF scanné / Excel / Word / PNG / JPG / TIFF, multi-fichiers)
  ↓  ocr.py         OCR configurable (pdf_text | tesseract | azure | google)
  ↓  parser.py      fournisseur, n° facture, date, devise, incoterm, lignes produits
  ↓  matching.py    rapprochement : nom → référence → alias → marque → fabricant → sémantique
  ↓  enrichment.py  code SH, taxes, autorisations, historique, fournisseur, documents
  ↓  pricing.py     comparaison prix facturé ↔ historique (moyenne/min/max, variation %)
  ↓  rules.py       constats de conformité + niveau de risque (faible/moyen/élevé)
  ↓  report.py      rapport structuré (sections) + confiance
  ↓  exports.py     PDF (reportlab) · Excel · CSV
```

Traitement **en arrière-plan** (RQ ou thread), **progression** persistée par
ligne, **reprise** des analyses interrompues au démarrage. Conçu pour des
factures de **200+ lignes**.

## Règle de non-invention

Comme le copilote (Phase 4), le moteur n'invente **rien** : produits, codes SH,
taxes et autorisations proviennent exclusivement de la base UM6P et des
documents officiels. Un produit non trouvé devient un **candidat à valider** ;
en l'absence d'information vérifiée : « Aucune information vérifiée disponible. »

## Fournisseurs OCR (configurables)

`settings.OCR_PROVIDER` : `pdf_text` (texte natif, défaut), `tesseract` (local,
hook), `azure` (Document Intelligence, hook), `google` (Document AI, hook),
`noop`. Repli automatique sur Tesseract pour les images / PDF scannés.

## Entités

`import_analyses`, `import_analysis_items`, `ocr_results`, `product_candidates`,
`price_alerts`, `compliance_findings`, `analysis_reports`.

## Rapport — sections

Fournisseur · Synthèse facture · Produits détectés · Analyse de conformité ·
Taxes · Autorisations · Documents requis · Historique des achats · Comparaison
de prix · Avertissements · Recommandations · Sources · Confiance.

## API (`/api/v1/import-analysis`)

- `POST /upload` — une ou plusieurs factures → lance les analyses.
- `GET /` — analyses récentes / historique.
- `GET /{id}` — détail (lignes, constats, rapport).
- `GET /{id}/progress` — suivi temps réel.
- `POST /{id}/reanalyze` — relance complète.
- `GET /{id}/export?format=pdf|xlsx|csv` — export du rapport.

## Audit / observabilité

Document importé, sortie OCR (`ocr_results`), produits rapprochés + confiance,
rapport généré, temps d'exécution, appels IA — tout est persisté.

## Interface

Page **Analyse Importation** : dépôt multi-fichiers, analyses récentes avec
progression, tableau des résultats (ligne, produit, rapprochement, confiance,
code SH, droits, TVA, autorisations, documents, historique, statut), panneau de
détail par produit, graphiques de prix, exports.

> L'analyse de facture ne modifie pas l'OCR de la Phase 2 et s'intègre à
> l'interface existante sans la redessiner.
