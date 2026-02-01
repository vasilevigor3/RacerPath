"""events.finished_time_utc: nullable, set from external API or admin UI

Revision ID: 0020_event_finished_time_utc
Revises: 0019_event_special_event
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0020_event_finished_time_utc"
down_revision = "0019_event_special_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("finished_time_utc", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("events", "finished_time_utc")
