# Plateforme de gestion des connaissances (Phase 3)

Base de connaissances **structurée** des achats & imports. C'est la **1ʳᵉ source**
que l'IA interrogera (avant les documents officiels de la Phase 2).

## Ordre d'interrogation prévu pour l'IA

1. **Base structurée** (ce module) — produits, alias, codes SH, taxes,
   autorisations, fournisseurs, historique des achats.
2. **Documents douaniers officiels** (Phase 2) — chunks tracés.
3. Seulement ensuite, Claude génère une explication (Phase 4, non implémentée).

## Sections d'administration (`/administration`)

Tableau de bord · Produits · Codes SH · Taxes · Autorisations · Fournisseurs ·
Historique des achats · Pays · Alias Produits · Import.

## Modèle de données (ajouts Phase 3)

- **product_aliases** — désignations alternatives d'un produit (améliore la
  recherche IA).
- **audit_logs** — piste d'audit : qui, quand, ancienne/nouvelle valeur, motif.
- **Produit** enrichi : référence, fabricant, marque, catégorie, mots-clés,
  pays d'origine, fournisseur privilégié, code SH, statut, notes.
- **Taxe** : droit d'importation, TVA, taxe parafiscale, taxes additionnelles,
  date d'effet (l'historique = plusieurs lignes).
- **Autorisation** : organisme, documents requis, référence légale, délai, commentaires.
- **Fournisseur** : site web, contact, délai d'appro.
- **Historique d'achat** : facture, incoterm, pays.

## API (`/api/v1/admin`)

- **CRUD générique** par ressource : liste paginée/filtrée/triée, création,
  création en masse (`/bulk`), lecture, mise à jour, suppression, export CSV.
- **Import** : `POST /import/preview` (aperçu + mapping proposé), `POST /import/commit`
  (upsert + rapport). Excel/CSV, résolution des clés naturelles (code SH, pays,
  fournisseur…), détection de doublons, mise à jour sans duplication.
- **Tableau de bord** : `GET /dashboard` (cartes + graphiques + activité récente).
- **Recherche globale** : `GET /search?q=` (produits, alias, codes SH,
  fournisseurs, achats, autorisations).
- **Audit** : `GET /audit`.
- **Détails enrichis** : `GET /products/{id}/detail`, `GET /hs-codes/{id}/detail`
  (avec taxes, autorisations, produits liés, citations documentaires).

Toute écriture est **journalisée** automatiquement (piste d'audit).

## Assistant d'import

1. Choix du type de données + dépôt du fichier (Excel/CSV).
2. Aperçu des lignes + **correspondance des colonnes** (proposée automatiquement).
3. Option « mettre à jour sans doublon ».
4. **Rapport** : créés / mis à jour / ignorés / erreurs par ligne.

## À noter

- Aucune donnée d'exemple n'est créée : le module est conçu pour **importer**
  vos jeux de données réels.
- Design UM6P conservé (fond blanc, orange pour les actions).
- Nouvelle migration à générer :
  `alembic revision --autogenerate -m "phase3 knowledge platform"` puis
  `alembic upgrade head`.
