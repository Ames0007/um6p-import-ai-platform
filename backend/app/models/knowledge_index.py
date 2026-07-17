"""Index de connaissance unifié — UNIQUE couche recherchable.

`knowledge_index` n'est PAS une base ni une source de vérité : c'est une
représentation de recherche optimisée, reconstruite automatiquement à partir
des tables relationnelles de PostgreSQL (qui restent autoritatives). Chaque
concept recherchable (code SH, document, chapitre, section, produit,
fournisseur, autorisation, taxe) devient UN enregistrement, avec un
`searchable_text` normalisé et une clé (`source_table` + `source_pk`)
permettant de recharger l'enregistrement complet depuis PostgreSQL.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDMixin

# Types de concepts supportés.
KI_HS_CODE = "HS_CODE"
KI_DOCUMENT = "DOCUMENT"
KI_CHAPTER = "CHAPTER"
KI_SECTION = "SECTION"
KI_PRODUCT = "PRODUCT"
KI_SUPPLIER = "SUPPLIER"
KI_AUTHORIZATION = "AUTHORIZATION"
KI_TAX = "TAX"


class KnowledgeIndex(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_index"

    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_title: Mapped[str | None] = mapped_column(Text, nullable=True)

    chapter: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    section: Mapped[str | None] = mapped_column(String(120), nullable=True)

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True, index=True
    )
    document_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    taxes: Mapped[str | None] = mapped_column(Text, nullable=True)
    authorizations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Champ de recherche normalisé (minuscule, sans accent, sans ponctuation,
    # singularisé) : titre + description + code + chapitre + section + document
    # + mots-clés + alias + noms chimiques/commerciaux/scientifiques.
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Rechargement de l'enregistrement complet depuis PostgreSQL (source de vérité).
    source_table: Mapped[str] = mapped_column(String(40), nullable=False)
    source_pk: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KnowledgeIndex {self.type} {self.reference}>"
