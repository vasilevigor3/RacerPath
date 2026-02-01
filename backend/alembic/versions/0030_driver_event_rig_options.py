"""Add rig_options to drivers and events

Revision ID: 0030_rig_options
Revises: 0028_withdraw_count
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0030_rig_options"
down_revision = "0028_withdraw_count"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "drivers",
        sa.Column("rig_options", sa.JSON(), nullable=True),
    )
    op.add_column(
        "events",
        sa.Column("rig_options", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("events", "rig_options")
    op.drop_column("drivers", "rig_options")
