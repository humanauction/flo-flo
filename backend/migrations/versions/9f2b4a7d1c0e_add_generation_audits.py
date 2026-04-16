"""add generation audits

Revision ID: 9f2b4a7d1c0e
Revises: 18a6bfb4fa39
Create Date: 2026-04-15 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revisions: str = "9f2b4a7d1c0e"
down_revision: Union[str, None] = "18a6bfb4fa39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generation_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("provenance_schema_version", sa.Integer(), nullable=True),
        sa.Column("provenance_json", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),

            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index(
        op.f("ix_generation_audits_job_id"),
        "generation_audits",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_generation_audits_job_id"),
        table_name="generation_audits",
    )
    op.drop_table("generation_audits")
