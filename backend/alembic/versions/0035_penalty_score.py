"""Add score column to penalties (CRS uses sum of penalty scores)

Revision ID: 0035_penalty_score
Revises: 0034_penalties
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa

revision = "0035_penalty_score"
down_revision = "0034_penalties"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "penalties",
        sa.Column("score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("penalties", "score")
