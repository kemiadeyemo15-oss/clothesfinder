"""init: pgvector extension + products table + ivfflat index

Revision ID: 0001_init
Revises:
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from app.config import get_settings

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

_DIM = get_settings().embedding_dim


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "products",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("retailer", sa.String, nullable=False, index=True),
        sa.Column("category", sa.String, server_default=""),
        sa.Column("colours", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("materials", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("silhouettes", sa.ARRAY(sa.String), server_default="{}"),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("currency", sa.String, server_default="GBP"),
        sa.Column("url", sa.String, server_default="unknown"),
        sa.Column("image", sa.String, server_default="unknown"),
        sa.Column("embedding", Vector(_DIM), nullable=False),
    )
    # Approximate-NN index for cosine. Tune `lists` to your catalogue size.
    op.execute(
        "CREATE INDEX products_embedding_idx ON products "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("products")
