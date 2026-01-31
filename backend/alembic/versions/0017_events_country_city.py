"""events: country, city for breakdown by location

Revision ID: 0017_events_country_city
Revises: 0016_task_scope_crs_snapshots
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0017_events_country_city"
down_revision = "0016_task_scope_crs_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("country", sa.String(length=80), nullable=True))
    op.add_column("events", sa.Column("city", sa.String(length=80), nullable=True))
    op.create_index(op.f("ix_events_country"), "events", ["country"], unique=False)
    op.create_index(op.f("ix_events_city"), "events", ["city"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_events_city"), table_name="events")
    op.drop_index(op.f("ix_events_country"), table_name="events")
    op.drop_column("events", "city")
    op.drop_column("events", "country")
