"""Allow multiple drivers per user; unique (user_id, primary_discipline) — one career per discipline.

Revision ID: 0036_drivers_unique_user_discipline
Revises: 0035_penalty_score
Create Date: 2026-01-30

"""
from alembic import op

revision = "0036_drivers_unique_user_discipline"
down_revision = "0035_penalty_score"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_drivers_user_id", "drivers", type_="unique")
    op.create_unique_constraint(
        "uq_drivers_user_id_primary_discipline",
        "drivers",
        ["user_id", "primary_discipline"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_drivers_user_id_primary_discipline", "drivers", type_="unique")
    op.create_unique_constraint("uq_drivers_user_id", "drivers", ["user_id"])
