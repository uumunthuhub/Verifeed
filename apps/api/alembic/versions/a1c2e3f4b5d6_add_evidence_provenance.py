"""add evidence source governance and article provenance

Revision ID: a1c2e3f4b5d6
Revises: 91d572397d9b
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a1c2e3f4b5d6"
down_revision: Union[str, Sequence[str], None] = "91d572397d9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("allowed_domains", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("sources", sa.Column("ingestion_method", sa.String(length=30), nullable=False, server_default="rss"))
    op.add_column("sources", sa.Column("refresh_minutes", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("sources", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("sources", sa.Column("last_ingested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sources", sa.Column("last_ingestion_error", sa.Text(), nullable=True))
    op.add_column("articles", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("articles", sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("articles", sa.Column("content_type", sa.String(length=100), nullable=True))
    op.create_index(op.f("ix_articles_content_hash"), "articles", ["content_hash"], unique=False)
    op.create_index(op.f("ix_articles_retrieved_at"), "articles", ["retrieved_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_articles_retrieved_at"), table_name="articles")
    op.drop_index(op.f("ix_articles_content_hash"), table_name="articles")
    op.drop_column("articles", "content_type")
    op.drop_column("articles", "retrieved_at")
    op.drop_column("articles", "content_hash")
    op.drop_column("sources", "last_ingestion_error")
    op.drop_column("sources", "last_ingested_at")
    op.drop_column("sources", "is_active")
    op.drop_column("sources", "refresh_minutes")
    op.drop_column("sources", "ingestion_method")
    op.drop_column("sources", "allowed_domains")
