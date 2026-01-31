"""remove coach role: set coach users to driver

Revision ID: 0015_remove_coach_role
Revises: 0014_unique_constraints
Create Date: 2026-01-30

"""
from alembic import op

revision = "0015_remove_coach_role"
down_revision = "0014_unique_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE users SET role = 'driver' WHERE role = 'coach'")


def downgrade() -> None:
    pass
