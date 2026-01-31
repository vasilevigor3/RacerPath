"""real world mapping

Revision ID: 0006_real_world_mapping
Revises: 0005_auth_audit
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_real_world_mapping"
down_revision = "0005_auth_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "real_world_formats",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("min_crs", sa.Float(), nullable=False),
        sa.Column("required_license_code", sa.String(length=40), nullable=True),
        sa.Column("required_task_codes", sa.JSON(), nullable=False),
        sa.Column("required_event_tiers", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_real_world_formats_code"),
    )

    op.create_table(
        "real_world_readiness",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=36), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.String(length=300), nullable=False),
        sa.Column("formats", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("real_world_readiness")
    op.drop_table("real_world_formats")