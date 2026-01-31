"""anti gaming reports

Revision ID: 0007_anti_gaming
Revises: 0006_real_world_mapping
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_anti_gaming"
down_revision = "0006_real_world_mapping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anti_gaming_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=36), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("flags", sa.JSON(), nullable=False),
        sa.Column("multiplier", sa.Float(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("anti_gaming_reports")