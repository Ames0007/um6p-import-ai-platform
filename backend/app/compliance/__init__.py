"""Moteur d'intelligence de conformité à l'import (Phase 5).

Automatise l'analyse des factures fournisseurs avant importation :
OCR → extraction → rapprochement produit → récupération (base UM6P + documents
officiels) → analyse de prix → conformité → rapport.

⚠️ Comme pour le copilote IA, rien n'est inventé : produits, codes SH, taxes et
autorisations proviennent exclusivement de la base et des documents officiels.
"""
