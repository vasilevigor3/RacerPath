"""events.session_type: race | training, default race

Revision ID: 0021_event_session_type
Revises: 0020_event_finished_time_utc
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0021_event_session_type"
down_revision = "0020_event_finished_time_utc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("session_type", sa.String(length=20), nullable=False, server_default="race"),
    )
    op.create_check_constraint(
        "ck_events_session_type",
        "events",
        "session_type IN ('race', 'training')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_events_session_type", "events", type_="check")
    op.drop_column("events", "session_type")
