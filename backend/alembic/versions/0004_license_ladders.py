"""license ladders

Revision ID: 0004_license_ladders
Revises: 0003_event_classification_inputs
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_license_ladders"
down_revision = "0003_event_classification_inputs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "license_levels",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("min_crs", sa.Float(), nullable=False),
        sa.Column("required_task_codes", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_license_levels_code"),
    )

    op.create_table(
        "driver_licenses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("level_code", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("driver_licenses")
    op.drop_table("license_levels")