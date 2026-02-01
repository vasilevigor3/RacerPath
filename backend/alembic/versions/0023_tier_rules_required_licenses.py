"""tier_progression_rules.required_license_codes: list of license codes for next tier

Revision ID: 0023_tier_required_licenses
Revises: 0022_tier_progression_rules
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa

revision = "0023_tier_required_licenses"
down_revision = "0022_tier_progression_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tier_progression_rules",
        sa.Column("required_license_codes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )


def downgrade() -> None:
    op.drop_column("tier_progression_rules", "required_license_codes")
