"""Widen alembic_version.version_num to varchar(64) for long revision IDs

Revision ID: 0024_ver_num_64
Revises: 0023_tier_required_licenses
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa

revision = "0024_ver_num_64"
down_revision = "0023_tier_required_licenses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(32),
        type_=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(64),
        type_=sa.String(32),
        existing_nullable=False,
    )
