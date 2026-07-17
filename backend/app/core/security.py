"""Utilitaires de sécurité / JWT.

Architecture préparée pour un futur SSO : les jetons sont émis et vérifiés
ici, ce qui permettra de brancher un fournisseur d'identité (OIDC/SAML) sans
modifier le reste de l'application.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Émet un JWT signé pour `subject` (identifiant utilisateur)."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Décode et vérifie un JWT. Retourne le payload ou None si invalide."""
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        return None
