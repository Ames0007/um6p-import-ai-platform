"""unified knowledge index (single searchable layer)

Revision ID: 0003_knowledge_index
Revises: 0002_understanding
Create Date: 2026-07-11 10:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0003_knowledge_index'
down_revision: Union[str, None] = '0002_understanding'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables sources dont toute modification doit rendre l'index « sale »
# (rafraîchissement automatique après import de document / produit / taxe /
# autorisation, sans toucher à l'importateur).
_SOURCE_TABLES = [
    "hs_codes", "products", "product_aliases", "taxes", "authorizations",
    "documents", "hs_references", "suppliers",
]


def upgrade() -> None:
    op.create_table(
        "knowledge_index",
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("reference", sa.String(length=120), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("normalized_title", sa.Text(), nullable=True),
        sa.Column("chapter", sa.String(length=120), nullable=True),
        sa.Column("section", sa.String(length=120), nullable=True),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("document_title", sa.Text(), nullable=True),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("taxes", sa.Text(), nullable=True),
        sa.Column("authorizations", sa.Text(), nullable=True),
        sa.Column("searchable_text", sa.Text(), nullable=False),
        sa.Column("source_table", sa.String(length=40), nullable=False),
        sa.Column("source_pk", sa.String(length=64), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_index_type", "knowledge_index", ["type"])
    op.create_index("ix_knowledge_index_reference", "knowledge_index", ["reference"])
    op.create_index("ix_knowledge_index_chapter", "knowledge_index", ["chapter"])
    op.create_index("ix_knowledge_index_document_id", "knowledge_index", ["document_id"])
    op.create_index("ix_knowledge_index_source_pk", "knowledge_index", ["source_pk"])
    op.create_index("ix_ki_type_reference", "knowledge_index", ["type", "reference"])
    op.create_index("ix_ki_type_chapter", "knowledge_index", ["type", "chapter"])
    # Recherche plein-texte scalable (cœur PostgreSQL, sans extension) : GIN
    # sur un tsvector 'simple' du texte déjà normalisé côté application.
    op.execute(
        "CREATE INDEX ix_ki_search ON knowledge_index "
        "USING gin (to_tsvector('simple', searchable_text))"
    )

    # --- Rafraîchissement automatique : table d'état + fonction + déclencheurs ---
    op.create_table(
        "knowledge_index_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dirty", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_built_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("INSERT INTO knowledge_index_state (id, dirty) VALUES (1, true)")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION knowledge_index_mark_dirty() RETURNS trigger AS $$
        BEGIN
            UPDATE knowledge_index_state SET dirty = true WHERE id = 1;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for tbl in _SOURCE_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_ki_dirty_{tbl} "
            f"AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON {tbl} "
            f"FOR EACH STATEMENT EXECUTE FUNCTION knowledge_index_mark_dirty()"
        )


def downgrade() -> None:
    for tbl in _SOURCE_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_ki_dirty_{tbl} ON {tbl}")
    op.execute("DROP FUNCTION IF EXISTS knowledge_index_mark_dirty()")
    op.drop_table("knowledge_index_state")
    op.execute("DROP INDEX IF EXISTS ix_ki_search")
    op.drop_table("knowledge_index")
