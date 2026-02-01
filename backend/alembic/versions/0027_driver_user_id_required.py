"""Make driver.user_id NOT NULL (driver cannot exist without a user)

Revision ID: 0027_driver_user_id_req
Revises: 0026_backfill_part_class
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0027_driver_user_id_req"
down_revision = "0026_backfill_part_class"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Delete dependent records for orphan drivers (user_id IS NULL), then delete orphans
    op.execute(
        "DELETE FROM incidents WHERE participation_id IN "
        "(SELECT id FROM participations WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL))"
    )
    op.execute(
        "DELETE FROM task_completions WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL)"
    )
    op.execute(
        "DELETE FROM participations WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL)"
    )
    op.execute(
        "DELETE FROM crs_history WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL)"
    )
    op.execute(
        "DELETE FROM driver_licenses WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL)"
    )
    op.execute(
        "DELETE FROM anti_gaming_reports WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL)"
    )
    op.execute(
        "DELETE FROM real_world_readiness WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL)"
    )
    op.execute(
        "DELETE FROM recommendations WHERE driver_id IN (SELECT id FROM drivers WHERE user_id IS NULL)"
    )
    op.execute("DELETE FROM drivers WHERE user_id IS NULL")
    # Enforce NOT NULL
    op.alter_column(
        "drivers",
        "user_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "drivers",
        "user_id",
        existing_type=sa.String(length=36),
        nullable=True,
    )
