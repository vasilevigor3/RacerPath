"""Add penalties table (time_penalty, drive_through, stop_and_go, dsq)

Revision ID: 0034_penalties
Revises: 0033_eval_failure
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0034_penalties"
down_revision = "0033_eval_failure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "penalties",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("participation_id", sa.String(36), sa.ForeignKey("participations.id"), nullable=False, index=True),
        sa.Column("penalty_type", sa.String(32), nullable=False),
        sa.Column("time_seconds", sa.Integer(), nullable=True),
        sa.Column("lap", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(240), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("penalties")
