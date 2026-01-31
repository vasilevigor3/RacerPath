"""drivers.tier E0-E5, default E0 for newcomers

Revision ID: 0018_driver_tier
Revises: 0017_events_country_city
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0018_driver_tier"
down_revision = "0017_events_country_city"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "drivers",
        sa.Column("tier", sa.String(length=10), nullable=False, server_default="E0"),
    )
    op.create_check_constraint(
        "ck_drivers_tier",
        "drivers",
        "tier IN ('E0', 'E1', 'E2', 'E3', 'E4', 'E5')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_drivers_tier", "drivers", type_="check")
    op.drop_column("drivers", "tier")
