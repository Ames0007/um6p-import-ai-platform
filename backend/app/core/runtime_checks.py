"""Validation de configuration au démarrage (Phase 9).

Interdit le démarrage en PRODUCTION avec des secrets par défaut ou une
configuration dangereuse. En développement, se contente d'émettre des
avertissements. Aucune logique métier ici — uniquement des garde-fous
d'exploitation.
"""
from __future__ import annotations

import logging

from app.core.config import settings

log = logging.getLogger("security")

# Valeurs par défaut connues considérées comme non sûres en production.
_DEFAULT_SECRET_KEYS = {"change-me-super-secret-key", "", "secret", "changeme"}
_DEFAULT_DB_PASSWORDS = {"postgres", "change-me-in-production", "", "password"}
_PLACEHOLDER_API_KEYS_PREFIX = "sk-ant-xxxx"


class ConfigurationError(RuntimeError):
    """Configuration invalide bloquant le démarrage en production."""


def validate_runtime(*, raise_on_error: bool = True) -> tuple[list[str], list[str]]:
    """Valide la configuration. Retourne (erreurs, avertissements).

    En production, lève `ConfigurationError` si des erreurs existent (sauf si
    `raise_on_error=False`, utilisé pour l'inspection).
    """
    errors: list[str] = []
    warnings: list[str] = []
    prod = settings.is_production

    # --- SECRET_KEY ---
    if settings.SECRET_KEY in _DEFAULT_SECRET_KEYS or len(settings.SECRET_KEY) < 32:
        msg = "SECRET_KEY est une valeur par défaut / trop courte (< 32 caractères)."
        (errors if prod else warnings).append(msg)

    # --- Mot de passe base de données ---
    if settings.POSTGRES_PASSWORD in _DEFAULT_DB_PASSWORDS:
        msg = "POSTGRES_PASSWORD utilise une valeur par défaut non sûre."
        (errors if prod else warnings).append(msg)

    # --- CORS ---
    if "*" in settings.cors_origins:
        msg = "BACKEND_CORS_ORIGINS contient '*' — incompatible avec les identifiants (credentials)."
        (errors if prod else warnings).append(msg)
    if not settings.cors_origins:
        warnings.append("BACKEND_CORS_ORIGINS est vide — le frontend sera bloqué par CORS.")

    # --- Clé API Claude (non bloquant : repli déterministe si absente) ---
    key = settings.ANTHROPIC_API_KEY.strip()
    if not key or key.startswith(_PLACEHOLDER_API_KEYS_PREFIX):
        warnings.append(
            "ANTHROPIC_API_KEY absente ou factice — l'assistant IA fonctionnera "
            "en mode repli déterministe (sans appel Claude)."
        )

    for w in warnings:
        log.warning("Configuration : %s", w)
    for e in errors:
        log.error("Configuration (bloquant en production) : %s", e)

    if prod and errors and raise_on_error:
        raise ConfigurationError(
            "Démarrage en production refusé — corrigez : " + " | ".join(errors)
        )

    return errors, warnings
