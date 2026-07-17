"""Énumérations métier partagées par les modèles."""
from __future__ import annotations

import enum


class AuthorizationStatus(str, enum.Enum):
    """Statut d'exigence d'autorisation pour une marchandise."""

    REQUISE = "requise"
    NON_REQUISE = "non_requise"
    CONDITIONNELLE = "conditionnelle"


class InvoiceStatus(str, enum.Enum):
    """Cycle de vie d'une facture importée."""

    RECUE = "recue"
    EN_TRAITEMENT = "en_traitement"
    ANALYSEE = "analysee"
    ERREUR = "erreur"


class MessageRole(str, enum.Enum):
    """Rôle d'un message dans une conversation."""

    USER = "user"
    ASSISTANT = "assistant"


# --- Ingestion documentaire (Phase 2) ---


class DocumentCategory(str, enum.Enum):
    """Catégories des documents officiels de la douane marocaine."""

    CODE_DES_DOUANES = "code_des_douanes"
    NOMENCLATURE = "nomenclature_douaniere"
    PRODUITS_CHIMIQUES = "produits_chimiques"
    ENGRAIS = "engrais"
    MACHINES = "machines_et_appareils"
    MATIERES_PLASTIQUES = "matieres_plastiques"
    PRODUITS_CONTROLES = "produits_controles"
    CIRCULAIRES = "circulaires"
    ANNEXES = "annexes_reglementaires"
    AUTRE = "autre"


class DocumentStatus(str, enum.Enum):
    """Cycle de vie d'un document dans le moteur d'ingestion."""

    EN_ATTENTE = "en_attente"        # importé, en file d'attente
    EN_TRAITEMENT = "en_traitement"  # pipeline en cours
    TERMINE = "termine"              # ingestion complète
    PARTIEL = "partiel"              # terminé avec des pages en erreur
    ERREUR = "erreur"                # échec global
    DOUBLON = "doublon"              # checksum déjà présent


class ImportStatus(str, enum.Enum):
    """Statut d'une exécution d'import (IMPORT_HISTORY)."""

    EN_COURS = "en_cours"
    REUSSI = "reussi"
    PARTIEL = "partiel"
    ECHOUE = "echoue"
    INTERROMPU = "interrompu"


# --- Plateforme de gestion des connaissances (Phase 3) ---


class ProductStatus(str, enum.Enum):
    """Statut d'un produit dans le référentiel."""

    ACTIF = "actif"
    INACTIF = "inactif"
    ARCHIVE = "archive"


class AuditAction(str, enum.Enum):
    """Type d'opération journalisée dans la piste d'audit."""

    CREATION = "creation"
    MODIFICATION = "modification"
    SUPPRESSION = "suppression"
    IMPORT = "import"


# --- Moteur de conformité à l'import (Phase 5) ---


class AnalysisStatus(str, enum.Enum):
    """Cycle de vie d'une analyse d'importation."""

    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    PARTIEL = "partiel"
    ERREUR = "erreur"


class RiskLevel(str, enum.Enum):
    """Niveau de risque de conformité."""

    FAIBLE = "faible"
    MOYEN = "moyen"
    ELEVE = "eleve"


class CandidateStatus(str, enum.Enum):
    """Statut d'un produit candidat (non trouvé en base)."""

    A_VALIDER = "a_valider"
    VALIDE = "valide"
    REJETE = "rejete"


class MatchMethod(str, enum.Enum):
    """Méthode ayant permis la correspondance produit."""

    NOM_EXACT = "nom_exact"
    REFERENCE = "reference_interne"
    ALIAS = "alias"
    MARQUE = "marque"
    FABRICANT = "fabricant"
    SEMANTIQUE = "semantique"
    AUCUNE = "aucune"


class FindingType(str, enum.Enum):
    """Type de constat de conformité."""

    CODE_SH_MANQUANT = "code_sh_manquant"
    AUTORISATION_MANQUANTE = "autorisation_manquante"
    PRODUIT_ABSENT = "produit_absent"
    FOURNISSEUR_ABSENT = "fournisseur_absent"
    PRODUIT_RESTREINT = "produit_restreint"
    DONNEES_INCOMPLETES = "donnees_incompletes"
    REGLEMENTATION_EXPIREE = "reglementation_expiree"
    ALERTE_PRIX = "alerte_prix"


class ItemStatus(str, enum.Enum):
    """Statut d'une ligne de facture analysée."""

    RAPPROCHE = "rapproche"           # produit trouvé
    A_VALIDER = "a_valider"           # candidat créé
    SANS_DONNEES = "sans_donnees"     # aucune info vérifiée
