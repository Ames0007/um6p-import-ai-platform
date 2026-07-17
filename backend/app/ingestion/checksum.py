"""Calcul d'empreinte de fichier (détection doublons / versions)."""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_of_file(path: str | Path, *, chunk_size: int = 1 << 20) -> str:
    """Retourne l'empreinte SHA-256 hexadécimale d'un fichier."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while block := fh.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
