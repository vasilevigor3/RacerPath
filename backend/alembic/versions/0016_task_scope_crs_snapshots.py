"""task scope, period_key, achieved_by; CRS/Recommendation snapshots (inputs_hash, algo_version, computed_from)

Revision ID: 0016_task_scope_crs_snapshots
Revises: 0015_remove_coach_role
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0016_task_scope_crs_snapshots"
down_revision = "0015_remove_coach_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----- TaskDefinition -----
    op.add_column(
        "task_definitions",
        sa.Column("scope", sa.String(length=24), nullable=False, server_default="per_participation"),
    )
    op.add_column("task_definitions", sa.Column("cooldown_days", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("period", sa.String(length=16), nullable=True))
    op.add_column("task_definitions", sa.Column("window_size", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("window_unit", sa.String(length=20), nullable=True))

    # ----- TaskCompletion -----
    op.add_column("task_completions", sa.Column("period_key", sa.String(length=16), nullable=True))
    op.add_column(
        "task_completions",
        sa.Column("achieved_by", sa.JSON(), nullable=True),
    )

    # Partial unique indexes for task_completions (Postgres)
    # global: (driver_id, task_id) WHERE participation_id IS NULL AND period_key IS NULL
    op.create_index(
        "uq_task_completions_global",
        "task_completions",
        ["driver_id", "task_id"],
        unique=True,
        postgresql_where=sa.text("participation_id IS NULL AND period_key IS NULL"),
    )
    # per_participation: (driver_id, task_id, participation_id) WHERE participation_id IS NOT NULL
    op.create_index(
        "uq_task_completions_per_participation",
        "task_completions",
        ["driver_id", "task_id", "participation_id"],
        unique=True,
        postgresql_where=sa.text("participation_id IS NOT NULL"),
    )
    # periodic: (driver_id, task_id, period_key) WHERE period_key IS NOT NULL
    op.create_index(
        "uq_task_completions_periodic",
        "task_completions",
        ["driver_id", "task_id", "period_key"],
        unique=True,
        postgresql_where=sa.text("period_key IS NOT NULL"),
    )

    # ----- CRSHistory -----
    op.add_column(
        "crs_history",
        sa.Column("computed_from_participation_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "crs_history",
        sa.Column("inputs_hash", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "crs_history",
        sa.Column("algo_version", sa.String(length=32), nullable=False, server_default="crs_v1"),
    )
    op.create_foreign_key(
        "fk_crs_history_computed_from_participation",
        "crs_history",
        "participations",
        ["computed_from_participation_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ----- Recommendation -----
    op.add_column(
        "recommendations",
        sa.Column("inputs_hash", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "recommendations",
        sa.Column("algo_version", sa.String(length=32), nullable=False, server_default="rec_v1"),
    )
    op.add_column(
        "recommendations",
        sa.Column("computed_from_participation_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_recommendations_computed_from_participation",
        "recommendations",
        "participations",
        ["computed_from_participation_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_recommendations_computed_from_participation", "recommendations", type_="foreignkey"
    )
    op.drop_column("recommendations", "computed_from_participation_id")
    op.drop_column("recommendations", "algo_version")
    op.drop_column("recommendations", "inputs_hash")

    op.drop_constraint(
        "fk_crs_history_computed_from_participation", "crs_history", type_="foreignkey"
    )
    op.drop_column("crs_history", "algo_version")
    op.drop_column("crs_history", "inputs_hash")
    op.drop_column("crs_history", "computed_from_participation_id")

    op.drop_index("uq_task_completions_periodic", table_name="task_completions")
    op.drop_index("uq_task_completions_per_participation", table_name="task_completions")
    op.drop_index("uq_task_completions_global", table_name="task_completions")
    op.drop_column("task_completions", "achieved_by")
    op.drop_column("task_completions", "period_key")

    op.drop_column("task_definitions", "window_unit")
    op.drop_column("task_definitions", "window_size")
    op.drop_column("task_definitions", "period")
    op.drop_column("task_definitions", "cooldown_days")
    op.drop_column("task_definitions", "scope")
