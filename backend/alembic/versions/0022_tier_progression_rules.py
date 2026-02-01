"""tier_progression_rules: min_events and difficulty_threshold per tier

Revision ID: 0022_tier_progression_rules
Revises: 0021_event_session_type
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa

revision = "0022_tier_progression_rules"
down_revision = "0021_event_session_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tier_progression_rules",
        sa.Column("tier", sa.String(length=10), nullable=False),
        sa.Column("min_events", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("difficulty_threshold", sa.Float(), nullable=False, server_default="0.0"),
        sa.PrimaryKeyConstraint("tier"),
    )
    op.create_check_constraint(
        "ck_tier_progression_rules_tier",
        "tier_progression_rules",
        "tier IN ('E0', 'E1', 'E2', 'E3', 'E4', 'E5')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tier_progression_rules_tier", "tier_progression_rules", type_="check")
    op.drop_table("tier_progression_rules")
