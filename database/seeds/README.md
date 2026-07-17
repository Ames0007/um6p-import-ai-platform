# Données de départ (seeds)

Ce dossier contiendra les jeux de données de référence **officiels** :

- Codes SH (Système Harmonisé)
- Taux de droits de douane et de TVA
- Autorisations et ministères émetteurs
- Pays

> ⚠️ Ces données constituent la **source de vérité**. Elles doivent provenir de
> sources officielles (Douane marocaine / ADII, textes réglementaires) et ne
> jamais être générées par l'IA.

Le chargement se fera via `backend/scripts/seed.py` (à implémenter dans une
version ultérieure), qui lira des fichiers CSV/JSON versionnés ici.
