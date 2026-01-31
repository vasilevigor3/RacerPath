"""add raw_events

Revision ID: 0002_raw_events
Revises: 0001_initial
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_raw_events"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("source_event_id", sa.String(length=80), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("normalized_event", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("event_id", sa.String(length=36), sa.ForeignKey("events.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("normalized_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("raw_events")