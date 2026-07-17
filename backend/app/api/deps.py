"""Dépendances FastAPI communes (DB, sécurité).

L'authentification est facultative pour l'instant (architecture prête pour SSO).
`get_current_subject` décode le JWT s'il est présent mais n'impose pas encore
l'accès — le durcissement se fera lors de l'intégration SSO.
"""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db

__all__ = ["get_db", "get_current_subject"]

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_subject(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    """Retourne l'identifiant du sujet si un JWT valide est fourni, sinon None."""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    return payload.get("sub")
