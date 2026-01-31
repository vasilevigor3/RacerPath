"""user profiles

Revision ID: 0010_user_profiles
Revises: 0009_task_completion_v2
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0010_user_profiles"
down_revision = "0009_task_completion_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("primary_discipline", sa.String(length=20), nullable=True),
        sa.Column("sim_platforms", sa.JSON(), nullable=False),
        sa.Column("rig", sa.String(length=120), nullable=True),
        sa.Column("goals", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
