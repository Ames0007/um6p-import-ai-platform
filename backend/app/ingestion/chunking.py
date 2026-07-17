"""Découpage du texte d'une page en fragments recherchables."""
from __future__ import annotations

from app.core.config import settings
from app.ingestion.types import ChunkDraft


def chunk_page_text(
    text: str,
    *,
    page: int | None,
    chapter: str | None,
    section: str | None,
    start_index: int,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[ChunkDraft]:
    """Découpe le texte d'une page en fragments avec chevauchement.

    Le découpage respecte autant que possible les frontières de paragraphe,
    puis se rabat sur une découpe par taille avec chevauchement.
    """
    size = chunk_size or settings.CHUNK_SIZE
    over = overlap if overlap is not None else settings.CHUNK_OVERLAP
    cleaned = text.strip()
    if not cleaned:
        return []

    chunks: list[ChunkDraft] = []
    index = start_index
    cursor = 0
    length = len(cleaned)

    while cursor < length:
        end = min(cursor + size, length)
        # Tente de couper à une frontière naturelle (saut de ligne / point).
        if end < length:
            window = cleaned[cursor:end]
            boundary = max(window.rfind("\n"), window.rfind(". "))
            if boundary > size * 0.5:
                end = cursor + boundary + 1

        piece = cleaned[cursor:end].strip()
        if piece:
            chunks.append(
                ChunkDraft(
                    chunk_index=index,
                    text=piece,
                    page=page,
                    chapter=chapter,
                    section=section,
                )
            )
            index += 1

        if end >= length:
            break
        cursor = max(end - over, cursor + 1)

    return chunks
