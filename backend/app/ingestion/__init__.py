"""Moteur d'ingestion documentaire (Phase 2).

Pipeline : PDF/DOCX/XLSX/CSV → extraction texte → OCR si nécessaire →
détection sections/chapitres/codes SH/taxes/autorisations → découpage →
préparation des embeddings → stockage PostgreSQL + traçabilité.

⚠️ Ce moteur ne fait qu'EXTRAIRE et STRUCTURER le contenu des documents
officiels. Il n'invente aucune donnée. L'IA (phase suivante) devra répondre
exclusivement à partir de ce contenu.
"""
