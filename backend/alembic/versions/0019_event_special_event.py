"""events.special_event: race_of_day, race_of_week, race_of_month, race_of_year

Revision ID: 0019_event_special_event
Revises: 0018_driver_tier
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0019_event_special_event"
down_revision = "0018_driver_tier"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("special_event", sa.String(length=20), nullable=True),
    )
    op.create_check_constraint(
        "ck_events_special_event",
        "events",
        "special_event IS NULL OR special_event IN ('race_of_day', 'race_of_week', 'race_of_month', 'race_of_year')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_events_special_event", "events", type_="check")
    op.drop_column("events", "special_event")
