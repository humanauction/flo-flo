"""add: rag v1 headline embeddings

Revision ID: af06c5742fe2
Revises: 9f2b4a7d1c0e
Create Date: 2026-05-11 12:34:56.789012

"""

from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector
except Exception:
    raise RuntimeError("pgvector is required for this migration")

# revision identifiers, used by Alembic.
revision = "af06c5742fe2"
down_revision = "9f2b4a7d1c0e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql" and Vector is not None:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.add_column(
            "headlines",
            sa.Column("embedding", Vector(1536), nullable=True),
        )
        op.add_column(
            "headlines",
            sa.Column("embedding_model", sa.String(64), nullable=True),
        )
        op.add_column(
            "headlines",
            sa.Column(
                "embedded_at",
                sa.DateTime(timezone=True),
                nullable=True
            ),
        )
        # Optional index once rows are large enough; can be deferred
        op.create_index(
            "ix_headlines_embedding",
            "headlines",
            ["embedding"],
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("ix_headlines_embedding", table_name="headlines")
    op.drop_column("headlines", "embedded_at")
    op.drop_column("headlines", "embedding_model")
    op.drop_column("headlines", "embedding")
