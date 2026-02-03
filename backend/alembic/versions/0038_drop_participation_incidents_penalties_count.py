"""Drop participation incidents_count and penalties_count (derived from relations).

Revision ID: 0038_drop_part_counts
Revises: 0037_incident_score_penalty_incident_id
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0038_drop_part_counts"
down_revision = "0037_incident_score_penalty_incident_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("participations", "incidents_count")
    op.drop_column("participations", "penalties_count")


def downgrade() -> None:
    op.add_column(
        "participations",
        sa.Column("incidents_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "participations",
        sa.Column("penalties_count", sa.Integer(), nullable=False, server_default="0"),
    )
