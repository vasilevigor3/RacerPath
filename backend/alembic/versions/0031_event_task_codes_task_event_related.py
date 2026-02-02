"""Add event task_codes and task_definitions event_related

Revision ID: 0031_task_codes_event_related
Revises: 0030_rig_options
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0031_task_codes_event_related"
down_revision = "0030_rig_options"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("task_codes", sa.JSON(), nullable=True),
    )
    op.add_column(
        "task_definitions",
        sa.Column("event_related", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("task_definitions", "event_related")
    op.drop_column("events", "task_codes")
