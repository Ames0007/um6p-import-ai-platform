"""query understanding transparency columns

Revision ID: 0002_understanding
Revises: 0001_initial
Create Date: 2026-07-10 22:30:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002_understanding'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ai_request_logs',
        sa.Column('understanding', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'ai_request_logs',
        sa.Column('retriever_query', sa.Text(), nullable=True),
    )
    op.add_column(
        'ai_request_logs',
        sa.Column('executed_sql', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('ai_request_logs', 'executed_sql')
    op.drop_column('ai_request_logs', 'retriever_query')
    op.drop_column('ai_request_logs', 'understanding')
