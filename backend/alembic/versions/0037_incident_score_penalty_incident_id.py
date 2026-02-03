"""Incident code/score (CRS v2); Penalty optional incident_id.

Revision ID: 0037_incident_score_penalty_incident_id
Revises: 0036_drivers_unique_user_discipline
Create Date: 2026-02-03

"""
from alembic import op
import sqlalchemy as sa

revision = "0037_incident_score_penalty_incident_id"
down_revision = "0036_drivers_unique_user_discipline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("code", sa.String(40), nullable=True))
    op.add_column(
        "incidents",
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "penalties",
        sa.Column("incident_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_penalties_incident_id_incidents",
        "penalties",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_penalties_incident_id_incidents", "penalties", type_="foreignkey")
    op.drop_column("penalties", "incident_id")
    op.drop_column("incidents", "score")
    op.drop_column("incidents", "code")
