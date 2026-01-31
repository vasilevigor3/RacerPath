"""driver user link

Revision ID: 0008_driver_user_link
Revises: 0007_anti_gaming
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_driver_user_link"
down_revision = "0007_anti_gaming"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("drivers", sa.Column("user_id", sa.String(length=36), nullable=True))
    op.create_unique_constraint("uq_drivers_user_id", "drivers", ["user_id"])
    op.create_foreign_key(
        "fk_drivers_user_id_users",
        "drivers",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_drivers_user_id_users", "drivers", type_="foreignkey")
    op.drop_constraint("uq_drivers_user_id", "drivers", type_="unique")
    op.drop_column("drivers", "user_id")
